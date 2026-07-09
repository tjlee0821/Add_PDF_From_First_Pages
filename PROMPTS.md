# Prompts

Use these project instructions when asking an AI agent to work on this repository.

```text
This repository is a post-OCR QuickBooks import preparation layer.
OCR is complete before this project starts.
Do not regenerate OCR output unless explicitly instructed.
Do not modify production input data.
Preserve backward compatibility with the legacy system.
Make the smallest safe change possible.
Before changing code, understand the implementation, explain the root cause, explain the proposed solution, implement, and verify.
```

For Stage 2 work:

```text
Do not redesign Stage 2.
Preserve the Upload -> Clone 30 to 40 -> Step40 -> Step40-A -> Clone 40 to 50 -> Step50 -> Export flow.
Stage 2 may fill QuickBooks vendor/customer names.
Stage 2 must never change transaction amounts.
Exports must preserve legacy column order.
The original target_name column position must remain blank after replaced_name.
```

