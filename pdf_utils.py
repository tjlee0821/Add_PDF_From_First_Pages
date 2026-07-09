import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
DEFAULT_PAGE_WIDTH = 612.0
DEFAULT_MARGIN = 36.0


def _pdf_page_widths(pdf_path):
    reader = PdfReader(pdf_path)
    widths = []

    for page in reader.pages:
        width = float(page.mediabox.width)
        if width > 0:
            widths.append(width)

    return widths


def _target_page_width(base_pdf, insert_files):
    widths = []

    for path in [base_pdf, *insert_files]:
        if os.path.splitext(path)[1].lower() != ".pdf":
            continue
        if not os.path.exists(path):
            continue
        widths.extend(_pdf_page_widths(path))

    if not widths:
        return DEFAULT_PAGE_WIDTH

    rounded_widths = [round(width, 2) for width in widths]

    if len(rounded_widths) == 1 and rounded_widths[0] > DEFAULT_PAGE_WIDTH * 1.5:
        return DEFAULT_PAGE_WIDTH

    counts = Counter(rounded_widths)
    max_count = max(counts.values())
    candidates = [width for width, count in counts.items() if count == max_count]

    if len(candidates) == 1:
        return candidates[0]

    median_width = sorted(rounded_widths)[(len(rounded_widths) - 1) // 2]
    return min(candidates, key=lambda width: (abs(width - median_width), width))


def image_to_pdf_page(image_path, output_path, target_width=DEFAULT_PAGE_WIDTH, margin=DEFAULT_MARGIN):
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    img_width, img_height = image.size
    if img_width <= 0 or img_height <= 0:
        image.close()
        raise ValueError(f"Invalid image dimensions: {image_path}")

    draw_width = max(float(target_width) - (margin * 2), 1.0)
    draw_height = draw_width * (img_height / img_width)
    page_height = draw_height + (margin * 2)

    c = canvas.Canvas(output_path, pagesize=(float(target_width), page_height))
    c.drawImage(
        ImageReader(image),
        margin,
        margin,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    c.save()
    image.close()


def image_to_temp_pdf(image_path, temp_dir, target_width=DEFAULT_PAGE_WIDTH):
    temp_pdf = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
        dir=temp_dir
    )
    temp_pdf.close()

    image_to_pdf_page(image_path, temp_pdf.name, target_width=target_width)

    return temp_pdf.name


def _scale_page_to_width(page, target_width):
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    if width <= 0 or height <= 0:
        return

    target_height = height * (float(target_width) / width)
    page.scale_to(float(target_width), target_height)


def _append_pdf_with_normalized_width(writer, pdf_path, target_width):
    start_index = len(writer.pages)
    writer.append(pdf_path, import_outline=True)

    for page in writer.pages[start_index:]:
        _scale_page_to_width(page, target_width)


def cleanup_old_backups(base_pdf, days=90):
    base_dir = os.path.dirname(base_pdf)
    base_stem = os.path.splitext(os.path.basename(base_pdf))[0]
    tmp_dir = os.path.join(base_dir, "tmp")

    os.makedirs(tmp_dir, exist_ok=True)

    cutoff = datetime.now() - timedelta(days=days)

    for name in os.listdir(tmp_dir):
        if not name.startswith(f"{base_stem}_backup_"):
            continue
        if not name.lower().endswith(".pdf"):
            continue

        path = os.path.join(tmp_dir, name)
        modified_time = datetime.fromtimestamp(os.path.getmtime(path))

        if modified_time < cutoff:
            os.remove(path)


def make_backup(base_pdf):
    base_dir = os.path.dirname(base_pdf)
    base_stem = os.path.splitext(os.path.basename(base_pdf))[0]
    tmp_dir = os.path.join(base_dir, "tmp")

    os.makedirs(tmp_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{base_stem}_backup_{timestamp}.pdf"
    backup_path = os.path.join(tmp_dir, backup_name)

    shutil.copy2(base_pdf, backup_path)
    return backup_path


def normalize_to_pdf(file_path, temp_dir, target_width=DEFAULT_PAGE_WIDTH):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return file_path, False

    if ext in IMAGE_EXTS:
        converted_pdf = image_to_temp_pdf(file_path, temp_dir, target_width)
        return converted_pdf, True

    raise ValueError(f"Unsupported file type: {file_path}")


def prepend_pdfs(base_pdf, insert_files):
    temp_converted_files = []
    temp_path = None
    writer = None

    try:
        if not os.path.exists(base_pdf):
            raise FileNotFoundError(f"Base PDF not found: {base_pdf}")

        base_dir = os.path.dirname(base_pdf)

        cleanup_old_backups(base_pdf)
        backup_path = make_backup(base_pdf)
        target_width = _target_page_width(base_pdf, insert_files)

        writer = PdfWriter()

        for file_path in insert_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Insert file not found: {file_path}")

            pdf_path, is_temp = normalize_to_pdf(file_path, base_dir, target_width)

            if is_temp:
                temp_converted_files.append(pdf_path)

            _append_pdf_with_normalized_width(writer, pdf_path, target_width)

        _append_pdf_with_normalized_width(writer, base_pdf, target_width)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=base_dir) as tmp:
            temp_path = tmp.name

        with open(temp_path, "wb") as f:
            writer.write(f)

        writer.close()
        writer = None

        os.replace(temp_path, base_pdf)

        return backup_path

    except Exception as e:
        log_path = os.path.join(
            os.path.dirname(base_pdf) if base_pdf else os.getcwd(),
            "prepend_pdf_error.log"
        )

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(str(e))

        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

        raise

    finally:
        if writer:
            try:
                writer.close()
            except Exception:
                pass

        for temp_file in temp_converted_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
