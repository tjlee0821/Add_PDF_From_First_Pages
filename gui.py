import os
import shutil
import tempfile
from datetime import datetime
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinterdnd2 import DND_FILES

from pdf_utils import prepend_pdfs, cleanup_old_backups, image_to_pdf_page
from image_utils import files_to_pdf_list, cleanup_temp_files, is_image_file


ALLOWED_EXTS = (
    ".pdf",
    ".jpg", ".jpeg",
    ".png",
    ".bmp",
    ".tif", ".tiff",
    ".webp",
)


def is_pdf_file(path):
    return path.lower().endswith(".pdf")


def is_allowed_file(path):
    return path.lower().endswith(ALLOWED_EXTS)


def image_to_base_pdf(image_path):
    base_dir = os.path.dirname(image_path)
    base_stem = os.path.splitext(os.path.basename(image_path))[0]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_pdf = os.path.join(base_dir, f"{base_stem}_base_{timestamp}.pdf")

    image_to_pdf_page(image_path, output_pdf)

    return output_pdf


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 앞에 붙이기")
        self.root.geometry("420x420")
        self.root.resizable(False, False)

        self.base_pdf = None

        self.label = tk.Label(
            root,
            text=(
                "PDF 또는 이미지를 드래그하세요\n\n"
                "첫 번째 파일 = 기준 파일\n"
                "그 이후 파일 = 기준 파일 앞에 추가\n\n"
                "※ 이미지도 자동으로 PDF 변환됩니다"
            ),
            font=("Arial", 14),
            justify="center"
        )
        self.label.pack(expand=True, fill="both", padx=20, pady=20)

        self.status = tk.Label(
            root,
            text="기준 파일: 없음",
            font=("Arial", 11),
            fg="gray"
        )
        self.status.pack(pady=15)

        root.drop_target_register(DND_FILES)
        root.dnd_bind("<<Drop>>", self.on_drop)

    def on_drop(self, event):
        files = list(self.root.tk.splitlist(event.data))

        if not files:
            return

        temp_files = []

        try:
            if not self.base_pdf:
                first_file = files[0]

                if not is_allowed_file(first_file):
                    messagebox.showwarning(
                        "경고",
                        "첫 번째 기준 파일은 PDF 또는 이미지여야 합니다."
                    )
                    return

                if is_pdf_file(first_file):
                    self.base_pdf = first_file

                elif is_image_file(first_file):
                    self.base_pdf = image_to_base_pdf(first_file)
                    messagebox.showinfo(
                        "기준 파일 변환 완료",
                        f"이미지를 기준 PDF로 변환했습니다.\n\n{os.path.basename(self.base_pdf)}"
                    )

                else:
                    messagebox.showwarning(
                        "경고",
                        "지원하지 않는 파일 형식입니다."
                    )
                    return

                cleanup_old_backups(self.base_pdf)

                self.status.config(
                    text=f"기준 파일: {os.path.basename(self.base_pdf)}"
                )

                remaining_files = files[1:]

                if not remaining_files:
                    return

                pdfs, temp_files = files_to_pdf_list(remaining_files)

            else:
                pdfs, temp_files = files_to_pdf_list(files)

            if not pdfs:
                messagebox.showwarning(
                    "경고",
                    "PDF 또는 이미지 파일만 드롭하세요."
                )
                return

            prepend_pdfs(self.base_pdf, pdfs)

            messagebox.showinfo(
                "완료",
                f"{len(pdfs)}개 파일을 기준 PDF 앞에 추가 완료"
            )

        except Exception as e:
            messagebox.showerror("오류", str(e))

        finally:
            cleanup_temp_files(temp_files)
