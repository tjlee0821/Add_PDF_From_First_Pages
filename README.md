# QuickBooks Import Preparation Layer

This repository is intended to host the post-OCR QuickBooks import preparation layer.

The production workflow starts after OCR has already completed:

1. Stage 1 validates OCR transaction CSVs against statement summary totals.
2. Stage 2 matches transaction names to QuickBooks reference data.
3. Stage 3 exports QuickBooks-ready CSVs and unmatched CSVs.

OCR output is the source of truth. This project must not regenerate OCR outputs unless explicitly instructed.

## Current Checkout Note

This checkout currently contains the older `Add_PDF_From_First_Pages` PDF utility files:

- `main.py`
- `gui.py`
- `pdf_utils.py`
- `image_utils.py`

The Stage 2 production modules named in the project brief are not present in this checkout:

- `stage_2_host.py`
- `stage_2_loader.py`
- `stage_2_clone.py`
- `stage_2_step40.py`
- `stage_2_step40a.py`
- `stage_2_step50.py`
- `stage_2_validator.py`
- `stage_2_export.py`
- `stage_2_writer.py`

Do not implement a replacement Stage 2 from scratch in this repository without first restoring or providing the existing production Stage 2 files.

## PDF utility image orientation

The main window includes **Rotate landscape images 90°**, unchecked by default.
Each drop reads the current setting. Images always receive EXIF orientation
normalization first; enabling the option then rotates landscape images 90 degrees
counterclockwise. Portrait and square images retain their normalized orientation.
The option does not affect PDF inputs or the existing page-width normalization.

The GUI converts base images through `image_to_base_pdf` →
`pdf_utils.image_to_pdf_page`. Inserted images use `image_utils.files_to_pdf_list`
→ `image_utils.image_to_pdf` before `pdf_utils.prepend_pdfs` merges the PDFs.
Both converters accept `rotate_landscape=False`. Direct image inputs to
`prepend_pdfs` also pass the option through `normalize_to_pdf` →
`image_to_temp_pdf` → `image_to_pdf_page`.

Run the focused regression suite with:

```sh
python3 -m unittest discover -s tests -v
```
