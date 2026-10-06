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

## Stitch Images mode

Select **Stitch Images** in the Mode dropdown, then drop a batch of image files
together in the desired order. Choose a PNG destination in the save dialog.
Each drop creates one image; files are not accumulated across separate drops or
sorted by filename. Switching back to **Add to existing PDF** restores the
selected base PDF. PDF mode remains the default and keeps its existing workflow.

Runtime path: `App.on_drop` → `App.stitch_dropped_images` →
`image_stitcher.stitch_images`. This path uses Pillow pixel operations only,
rejects PDFs, and does not create, read, merge, or render any PDF.

`image_processing.normalize_image_orientation` is shared by stitching and both
existing PDF image converters: apply `ImageOps.exif_transpose` first, then
optionally rotate landscape images 90° counterclockwise. Determine the widest
image after orientation and resize narrower images proportionally with Lanczos
resampling. Heights are rounded to the nearest pixel (minimum one pixel). Paste
vertically with no gap, preserving transparency in an RGBA PNG.

Before pixel decoding or final-canvas allocation, header/EXIF metadata determines
output dimensions. A conservative estimate includes the RGBA canvas, one input's
decoding/orientation buffers, conversion/resizing buffers, and encoder slack.
Requests above 512 MiB estimated working memory or Pillow's normal pixel safety
threshold are rejected with a message; inputs are never silently downscaled to
fit. Pillow's decompression safeguards remain enabled. This is a fixed safety
budget, not a guarantee of available system memory; allocation failures also
produce a clear error.

JPEG, PNG, BMP, TIFF, and WEBP inputs are supported. Only the first frame of
multi-frame/animated inputs is used. This version supports vertical stitching and
PNG output only. Processing is synchronous, so large accepted batches can briefly
occupy the GUI. Source paths (including aliases) cannot be output destinations.
Saving uses a temporary PNG beside the destination followed by atomic replacement;
the temporary file is removed on failure and an existing output stays intact.
