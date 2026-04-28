import os
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinterdnd2 import DND_FILES

from pdf_utils import prepend_pdfs, cleanup_old_backups
from image_utils import files_to_pdf_list, cleanup_temp_files, is_image_file


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 앞에 붙이기")
        self.root.geometry("420x420")
        self.root.resizable(False, False)

        self.base_pdf = None

        self.label = tk.Label(
            root,
            text="PDF 또는 이미지를 드래그하세요\n\n첫 번째 PDF = 기준 PDF\n그 이후 파일 = 기준 PDF 앞에 추가",
            font=("Arial", 14),
            justify="center"
        )
        self.label.pack(expand=True, fill="both", padx=20, pady=20)

        self.status = tk.Label(
            root,
            text="기준 PDF: 없음",
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

        # 기준 PDF가 아직 없으면 첫 번째 파일은 반드시 PDF여야 함
        if not self.base_pdf:
            first_file = files[0]

            if not first_file.lower().endswith(".pdf"):
                messagebox.showwarning("경고", "첫 번째 기준 파일은 PDF여야 합니다.")
                return

            self.base_pdf = first_file
            cleanup_old_backups(self.base_pdf)

            self.status.config(
                text=f"기준 PDF: {os.path.basename(self.base_pdf)}"
            )

            remaining_files = files[1:]

            if not remaining_files:
                return

            pdfs, temp_files = files_to_pdf_list(remaining_files)

        else:
            pdfs, temp_files = files_to_pdf_list(files)

        if not pdfs:
            messagebox.showwarning("경고", "PDF 또는 이미지 파일만 드롭하세요.")
            return

        try:
            prepend_pdfs(self.base_pdf, pdfs)
            messagebox.showinfo("완료", f"{len(pdfs)}개 파일 앞에 추가 완료")

        except Exception as e:
            messagebox.showerror("오류", str(e))

        finally:
            cleanup_temp_files(temp_files)