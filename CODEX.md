# Codex Notes

Follow `AGENTS.md` and `PROJECT_RULES.md`.

For this repository:

- Prefer small patches over broad rewrites.
- Use existing module boundaries.
- Do not alter OCR outputs.
- Do not change transaction amounts in Stage 2.
- Preserve legacy CSV exports exactly.
- Keep the blank original `target_name` position after `replaced_name`.

If Stage 2 files are absent, stop and report that the production implementation is not available in this checkout.

