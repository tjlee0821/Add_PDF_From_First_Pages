import os
import tempfile
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


def is_image_file(file_path: str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_IMAGE_EXTENSIONS


def image_to_pdf(
    image_path: str,
    page_size=letter,
    margin: float = 36,
) -> str:
    """
    이미지 파일을 Letter portrait PDF 한 장으로 변환합니다.

    규칙:
    - landscape 이미지는 왼쪽으로 90도 회전
    - portrait 기준 페이지에 삽입
    - 이미지가 페이지보다 크면 비율 유지해서 축소
    - 가운데 정렬
    - 결과는 임시 PDF 경로로 반환
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    if not is_image_file(image_path):
        raise ValueError(f"지원하지 않는 이미지 형식입니다: {image_path}")

    page_width, page_height = page_size

    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    img_width, img_height = image.size

    # landscape 이미지면 왼쪽으로 90도 회전
    if img_width > img_height:
        image = image.rotate(90, expand=True)
        img_width, img_height = image.size

    max_width = page_width - (margin * 2)
    max_height = page_height - (margin * 2)

    scale = min(max_width / img_width, max_height / img_height, 1)

    draw_width = img_width * scale
    draw_height = img_height * scale

    x = (page_width - draw_width) / 2
    y = (page_height - draw_height) / 2

    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_img_path = temp_img.name
    temp_img.close()

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf_path = temp_pdf.name
    temp_pdf.close()

    try:
        image.save(temp_img_path, "JPEG", quality=95)

        c = canvas.Canvas(temp_pdf_path, pagesize=page_size)
        c.drawImage(
            temp_img_path,
            x,
            y,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )
        c.save()

        return temp_pdf_path

    finally:
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)


def files_to_pdf_list(file_paths):
    """
    PDF + 이미지가 섞여 들어왔을 때,
    PDF는 그대로 두고 이미지는 임시 PDF로 변환해서 리스트로 반환합니다.

    반환:
    - pdf_paths: 실제 삽입/합치기에 사용할 PDF 경로 리스트
    - temp_files: 나중에 삭제해야 할 임시 PDF 리스트
    """

    pdf_paths = []
    temp_files = []

    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()

        if ext == ".pdf":
            pdf_paths.append(path)

        elif is_image_file(path):
            temp_pdf = image_to_pdf(path)
            pdf_paths.append(temp_pdf)
            temp_files.append(temp_pdf)

    return pdf_paths, temp_files


def cleanup_temp_files(temp_files):
    for path in temp_files:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass