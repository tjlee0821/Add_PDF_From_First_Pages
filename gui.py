import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from pdf_utils import prepend_pdfs


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 앞에 붙이기")
        self.root.geometry("400x400")

        self.base_pdf = None

        self.label = tk.Label(
            root,
            text="기준 PDF 선택 후\nPDF 드래그하세요",
            font=("Arial", 14),
            justify="center"
        )
        self.label.pack(expand=True)

        btn = tk.Button(root, text="기준 PDF 선택", command=self.select_base)
        btn.pack()

        self.status = tk.Label(root, text="없음", fg="gray")
        self.status.pack()

        root.drop_target_register(DND_FILES)
        root.dnd_bind("<<Drop>>", self.on_drop)

    def select_base(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            self.base_pdf = path
            self.status.config(text=os.path.basename(path))

    def on_drop(self, event):
        if not self.base_pdf:
            messagebox.showwarning("경고", "기준 PDF 먼저 선택")
            return

        files = self.root.tk.splitlist(event.data)
        pdfs = [f for f in files if f.endswith(".pdf")]

        if not pdfs:
            return

        prepend_pdfs(self.base_pdf, pdfs)
        messagebox.showinfo("완료", "앞에 추가 완료")