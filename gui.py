import os
import shutil
import tempfile
from datetime import datetime
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from tkinterdnd2 import DND_FILES

from pdf_utils import prepend_pdfs, cleanup_old_backups, image_to_pdf_page
from image_utils import files_to_pdf_list, cleanup_temp_files, is_image_file
from image_stitcher import stitch_images


PDF_MODE = "Add to existing PDF"
STITCH_MODE = "Stitch Images"


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


def image_to_base_pdf(image_path, rotate_landscape=False):
    base_dir = os.path.dirname(image_path)
    base_stem = os.path.splitext(os.path.basename(image_path))[0]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_pdf = os.path.join(base_dir, f"{base_stem}_base_{timestamp}.pdf")

    image_to_pdf_page(image_path, output_pdf, rotate_landscape=rotate_landscape)

    return output_pdf


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 앞에 붙이기")
        self.root.geometry("420x420")
        self.root.resizable(False, False)

        self.base_pdf = None

        self.mode = tk.StringVar(master=root, value=PDF_MODE)
        mode_controls = tk.Frame(root)
        mode_controls.pack(pady=5)
        tk.Label(mode_controls, text="Mode:").pack(side="left", padx=5)
        tk.OptionMenu(mode_controls, self.mode, PDF_MODE, STITCH_MODE,
                      command=self.update_mode).pack(side="left")

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

        self.rotate_landscape = tk.BooleanVar(master=root, value=False)
        self.rotate_checkbox = tk.Checkbutton(
            root,
            text="Rotate landscape images 90°",
            variable=self.rotate_landscape,
        )
        self.rotate_checkbox.pack(pady=5)

        self.status = tk.Label(
            root,
            text="기준 파일: 없음",
            font=("Arial", 11),
            fg="gray"
        )
        self.status.pack(pady=15)

        root.drop_target_register(DND_FILES)
        root.dnd_bind("<<Drop>>", self.on_drop)

    def update_mode(self, _selection=None):
        if self.mode.get() == STITCH_MODE:
            self.label.config(text=(
                "Stitch Images\n\nDrop images together in stitch order.\n"
                "Images are joined from top to bottom.\n\n"
                "Save as one PNG image. PDFs are not accepted."
            ))
            self.status.config(text="Output: one PNG image")
        else:
            self.label.config(text=(
                "PDF 또는 이미지를 드래그하세요\n\n"
                "첫 번째 파일 = 기준 파일\n"
                "그 이후 파일 = 기준 파일 앞에 추가\n\n"
                "※ 이미지도 자동으로 PDF 변환됩니다"
            ))
            name = os.path.basename(self.base_pdf) if self.base_pdf else "없음"
            self.status.config(text=f"기준 파일: {name}")

    def stitch_dropped_images(self, files, rotate_landscape):
        if any(is_pdf_file(path) for path in files):
            messagebox.showwarning("Stitch Images", "PDF inputs are not accepted. Drop image files only.")
            return
        if any(not is_image_file(path) for path in files):
            messagebox.showwarning("Stitch Images", "Drop supported image files only (JPEG, PNG, BMP, TIFF, WEBP).")
            return
        output = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save stitched image",
            initialdir=os.path.dirname(os.path.abspath(files[0])),
            initialfile=f"stitched_{datetime.now():%Y%m%d_%H%M%S}.png",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
        )
        if not output:
            return
        stitch_images(files, output, rotate_landscape=rotate_landscape)
        self.status.config(text=f"PNG: {os.path.basename(output)}")
        messagebox.showinfo("Stitch Images", f"Saved {len(files)} images as one PNG:\n{output}")

    def on_drop(self, event):
        files = list(self.root.tk.splitlist(event.data))

        if not files:
            return

        rotate_landscape = self.rotate_landscape.get()
        temp_files = []

        try:
            if self.mode.get() == STITCH_MODE:
                self.stitch_dropped_images(files, rotate_landscape)
                return

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
                    self.base_pdf = image_to_base_pdf(first_file, rotate_landscape=rotate_landscape)
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

                pdfs, temp_files = files_to_pdf_list(remaining_files, rotate_landscape=rotate_landscape)

            else:
                pdfs, temp_files = files_to_pdf_list(files, rotate_landscape=rotate_landscape)

            if not pdfs:
                messagebox.showwarning(
                    "경고",
                    "PDF 또는 이미지 파일만 드롭하세요."
                )
                return

            prepend_pdfs(self.base_pdf, pdfs, rotate_landscape=rotate_landscape)

            messagebox.showinfo(
                "완료",
                f"{len(pdfs)}개 파일을 기준 PDF 앞에 추가 완료"
            )

        except Exception as e:
            messagebox.showerror("오류", str(e))

        finally:
            cleanup_temp_files(temp_files)
