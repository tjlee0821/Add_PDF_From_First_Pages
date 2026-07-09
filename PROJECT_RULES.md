# Project Rules

Production stability and backward compatibility are the primary constraints.

## Boundaries

- Work only inside this repository.
- Do not traverse parent directories for implementation work.
- Do not edit sibling repositories.
- Do not modify `scan_prepare` or production data directories.
- Do not regenerate OCR outputs unless explicitly instructed.

## Stage Rules

- Stage 1 validates existing OCR transaction CSVs.
- Stage 1 must use `combined_{month}_1030_Source.csv` as the primary transaction source.
- Stage 1 compares statement debit amount against the CSV debit sum.
- Stage 2 performs vendor matching only.
- Stage 2 must never change transaction amounts.
- Stage 3 produces only QuickBooks Ready CSV and Unmatched CSV.

## Compatibility Rules

- Preserve filenames, CLI behavior, logs, done markers, and output formats.
- Preserve legacy unclassified output.
- Preserve legacy CSV column order.
- Internally `target_name` has been replaced by `replaced_name`.
- Exported CSVs must keep the original `target_name` column position as a blank column.
- `payment_split` must not occupy the original `target_name` position.

Required legacy export layout around the renamed field:

```text
description
replaced_name

debit
credit
```

The blank line represents the original legacy `target_name` column position.

