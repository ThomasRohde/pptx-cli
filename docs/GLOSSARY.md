# Glossary

- **Agent-first CLI:** A CLI designed to expose stable machine-readable behavior for coding agents and automation.
- **Annotations file:** The `annotations.yaml` layer used for semantic or operator-authored notes without mutating extracted manifest facts.
- **Compatibility report:** Initialization output describing unsupported or risky template constructs.
- **Deck spec:** Structured JSON/YAML describing an ordered set of slides to build from approved layouts.
- **Fidelity contract:** The explicit statement of what is guaranteed versus best-effort in generated output.
- **Manifest package:** The directory emitted by `pptx init` containing manifest, schema, annotations, reports, assets, and fingerprints.
- **Placeholder contract:** The definition of a placeholder's name, type, geometry, rules, and supported content mapping.
- **Protected static element:** A template-owned element that should remain unchanged unless explicitly permitted.
- **Response envelope:** The stable JSON shape returned by commands in machine-readable mode.
- **Wrapper CLI:** A thin template-specific CLI generated from a manifest package and delegated to the shared engine.
