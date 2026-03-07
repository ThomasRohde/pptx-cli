---
applyTo: "src/pptx_cli/**/*.py"
---

# Backend instructions

- Keep command handlers thin and move reusable logic into `core/` or `models/`
- Preserve deterministic machine-readable output
- Do not introduce a Python package named `pptx`
- Prefer explicit types and small, composable functions
- When a command mutates outputs, maintain dry-run compatibility and safe file-write semantics
- Do not silently change stable error codes or exit-code categories
