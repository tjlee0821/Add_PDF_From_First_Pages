# Architecture

## Intended Production Architecture

This project is the QuickBooks import preparation layer that runs after OCR.

### Stage 1

Stage 1 validates existing OCR output. It locates `combined_{month}_1030_Source.csv`, reads the statement summary debit amount, sums debit transactions in the CSV, and accepts the CSV only when those totals match.

If totals differ, Stage 1 runs validation and recovery logic. The final validated transaction total must equal the statement summary amount.

### Stage 2

Stage 2 performs vendor matching. It fills QuickBooks vendor or customer names and does not change amounts.

The production Stage 2 flow is:

```text
Upload
Clone 30 -> 40
Step40
Step40-A
Clone 40 -> 50
Step50
Export
```

Expected Stage 2 modules:

- `stage_2_host.py`
- `stage_2_loader.py`
- `stage_2_clone.py`
- `stage_2_step40.py`
- `stage_2_step40a.py`
- `stage_2_step50.py`
- `stage_2_validator.py`
- `stage_2_export.py`
- `stage_2_writer.py`

### Stage 3

Stage 3 produces:

- QuickBooks Ready CSV
- Unmatched CSV

No other Stage 3 outputs should be added unless explicitly requested.

## Current Repository Contents

This checkout currently contains a PDF prepend utility with a Tkinter drag-and-drop interface. The code is organized as:

- `main.py`: starts the TkinterDnD application.
- `gui.py`: owns the drag-and-drop UI and user workflow.
- `pdf_utils.py`: prepends PDFs or converted image PDFs and creates backups.
- `image_utils.py`: converts supported image files into temporary PDFs.

The expected Stage 2 modules are absent in this checkout.

