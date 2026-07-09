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

