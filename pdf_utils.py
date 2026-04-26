import os
import shutil
import tempfile
from pypdf import PdfWriter


def prepend_pdfs(base_pdf, insert_pdfs):
    base_dir = os.path.dirname(base_pdf)
    base_name = os.path.basename(base_pdf)

    backup_path = os.path.join(base_dir, f"backup_{base_name}")
    shutil.copy2(base_pdf, backup_path)

    writer = PdfWriter()

    # 새 PDF 먼저
    for pdf in insert_pdfs:
        writer.append(pdf, import_outline=True)

    # 기존 PDF
    writer.append(base_pdf, import_outline=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        temp_path = tmp.name

    with open(temp_path, "wb") as f:
        writer.write(f)

    os.replace(temp_path, base_pdf)

    return backup_path