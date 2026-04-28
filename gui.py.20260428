import os
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinterdnd2 import DND_FILES

from pdf_utils import prepend_pdfs


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 앞에 붙이기")
        self.root.geometry("420x420")
        self.root.resizable(False, False)

        self.base_pdf = None

        self.label = tk.Label(
            root,
            text="PDF를 드래그하세요\n\n첫 번째 PDF = 기준 PDF\n그 이후 PDF = 기준 PDF 앞에 추가",
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
        files = self.root.tk.splitlist(event.data)
        pdfs = [f for f in files if f.lower().endswith(".pdf")]

        if not pdfs:
            messagebox.showwarning("경고", "PDF만 드롭하세요")
            return

        if not self.base_pdf:
            self.base_pdf = pdfs[0]
            self.status.config(text=f"기준 PDF: {os.path.basename(self.base_pdf)}")

            if len(pdfs) > 1:
                prepend_pdfs(self.base_pdf, pdfs[1:])
                messagebox.showinfo("완료", "앞에 추가 완료")

            return

        prepend_pdfs(self.base_pdf, pdfs)
        messagebox.showinfo("완료", f"{len(pdfs)}개 추가 완료")