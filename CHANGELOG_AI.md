# AI Changelog

## 2026-07-09

- Added required project documentation files.
- Documented the intended post-OCR QuickBooks import preparation architecture.
- Documented Stage 2 backward compatibility requirements, including the blank legacy `target_name` column position after `replaced_name`.
- Recorded that the current checkout contains the older PDF prepend utility and does not include the expected Stage 2 modules.
- Fixed PDF output page-width inconsistency by replacing blind PIL PDF image saves with explicit ReportLab page boxes and normalizing appended PDF pages to a common width.
