import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pypdf import PdfWriter


def cleanup_old_backups(base_pdf, days=90):
    base_dir = os.path.dirname(base_pdf)
    base_stem = os.path.splitext(os.path.basename(base_pdf))[0]
    tmp_dir = os.path.join(base_dir, "tmp")

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

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

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{base_stem}_backup_{timestamp}.pdf"
    backup_path = os.path.join(tmp_dir, backup_name)

    shutil.copy2(base_pdf, backup_path)
    return backup_path


def prepend_pdfs(base_pdf, insert_pdfs):
    cleanup_old_backups(base_pdf)
    backup_path = make_backup(base_pdf)

    writer = PdfWriter()

    for pdf in insert_pdfs:
        writer.append(pdf, import_outline=True)

    writer.append(base_pdf, import_outline=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        temp_path = tmp.name

    with open(temp_path, "wb") as f:
        writer.write(f)

    os.replace(temp_path, base_pdf)

    return backup_path