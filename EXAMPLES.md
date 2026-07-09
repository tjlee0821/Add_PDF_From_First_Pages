# Examples

## Intended Input Structure

Input comes from a separate production repository and must not be modified by this project.

```text
scan_prepare/
    Company/
        Statements/
            AMEX_81005/
                1/
                2/
                3/
```

Each monthly folder already contains OCR outputs.

```text
2/
    2_DEBITs/
        combined_2_1030_Source.csv
    summary/
    glmocr/
```

## Stage 1 Example

For month `2`, Stage 1 locates:

```text
combined_2_1030_Source.csv
```

It compares:

```text
Statement New Charges amount == Sum of debit transactions from CSV
```

If equal, the CSV is accepted. If different, validation or recovery logic runs.

## Stage 2 Export Layout Example

The legacy export layout must preserve a blank column where `target_name` used to be:

```text
description,replaced_name,,debit,credit
```

`payment_split` must not be written into that blank column.

