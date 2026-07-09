import os
import shutil
import tempfile
from datetime import datetime, timedelta
from PIL import Image
from pypdf import PdfWriter


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def image_to_temp_pdf(image_path, temp_dir):
    img = Image.open(image_path)

    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    # A4 size at 300 DPI
    page_w, page_h = 2550, 3300

    img.thumbnail((page_w, page_h), Image.LANCZOS)

    page = Image.new("RGB", (page_w, page_h), "white")

    x = (page_w - img.width) // 2
    y = (page_h - img.height) // 2
    page.paste(img, (x, y))

    temp_pdf = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
        dir=temp_dir
    )
    temp_pdf.close()

    page.save(temp_pdf.name, "PDF", resolution=300.0)

    img.close()
    page.close()

    return temp_pdf.name


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


def normalize_to_pdf(file_path, temp_dir):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return file_path, False

    if ext in IMAGE_EXTS:
        converted_pdf = image_to_temp_pdf(file_path, temp_dir)
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

        writer = PdfWriter()

        for file_path in insert_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Insert file not found: {file_path}")

            pdf_path, is_temp = normalize_to_pdf(file_path, base_dir)

            if is_temp:
                temp_converted_files.append(pdf_path)

            writer.append(pdf_path, import_outline=True)

        writer.append(base_pdf, import_outline=True)

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