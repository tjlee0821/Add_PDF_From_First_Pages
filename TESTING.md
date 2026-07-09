# Testing

## Current Checkout

For the current PDF utility files, use Python syntax checks as a baseline:

```powershell
python -m py_compile main.py gui.py pdf_utils.py image_utils.py
```

Manual smoke test:

1. Run `python main.py`.
2. Drop a base PDF or image.
3. Drop one or more PDFs or images to prepend.
4. Confirm the base PDF is updated.
5. Confirm a backup PDF is written under the base file's `tmp` directory.

## Intended QuickBooks Pipeline

Stage 1 tests should verify:

- `combined_{month}_1030_Source.csv` is located without OCR regeneration.
- Statement debit amount is parsed from summary output.
- CSV debit sum matches the statement debit amount.
- Mismatches fail or enter recovery logic.

Stage 2 tests should verify:

- Transaction amounts never change.
- Vendor/customer names are filled as expected.
- Legacy unclassified output remains present.
- Legacy CSV column order is preserved.
- The original `target_name` column position remains blank in exports.
- `payment_split` does not occupy the original `target_name` position.

Stage 3 tests should verify:

- Only QuickBooks Ready CSV and Unmatched CSV are produced.
- Output values remain compatible with QuickBooks import expectations.

