# Architecture

## Chosen stack and rationale

### Confirmed

- **Language:** Python 3.12+
- **Package/dependency manager:** uv
- **CLI framework:** Typer
- **Modeling/schema:** Pydantic v2
- **XML/package handling:** `lxml`, `zipfile`
- **Presentation operations:** `python-pptx` selectively
- **Validation:** `jsonschema`
- **Terminal UX:** `rich`
- **Testing:** `pytest`
- **Linting/formatting:** Ruff
- **Type checking:** Pyright

### Rationale

The PRD explicitly recommends Python and a hybrid PowerPoint-processing approach. Python is a good fit for:

- CLI ergonomics
- XML/package manipulation
- YAML/JSON/schema workflows
- automation in enterprise and agent-driven environments

`uv` is the preferred package and environment manager because it provides one fast, reproducible workflow for local development, CI, and future publishing.

### Important packaging note

The public executable is `pptx`, but the Python package is scaffolded as `pptx_cli`.

This is intentional.

`python-pptx` already uses the import namespace `pptx`, so reusing that module name here would create a collision.

The intended distribution package name is `pptx-cli` on PyPI.

## Major components

### 1. CLI contract layer

Responsibilities:

- top-level command registration
- response envelope generation
- error-code and exit-code mapping
- `guide` command generation
- output-mode handling for JSON, human help, and `LLM=true`

### 2. Manifest compiler layer

Responsibilities:

- inspect Open Packaging Convention parts
- normalize extracted data into stable internal models
- emit `manifest.yaml`, `manifest.schema.json`, `annotations.yaml`, and compatibility reports

### 3. Composition engine

Responsibilities:

- clone approved layout structures
- map content into approved placeholders
- preserve masters, themes, and protected elements
- write valid `.pptx` outputs using safe file-write semantics

### 4. Validation engine

Responsibilities:

- validate manifest and deck specs
- validate generated outputs against the manifest and fingerprints
- emit machine-readable diagnostics

### 5. Wrapper generator

Responsibilities:

- emit thin Python package scaffolds for template-specific CLIs
- keep generated wrappers delegating to the shared engine

## Boundaries and responsibilities

- `src/pptx_cli/cli.py` owns command composition and top-level routing
- `src/pptx_cli/models/` owns typed models such as the response envelope and guide schema
- `src/pptx_cli/core/` owns reusable runtime behavior, configuration, and output helpers
- `src/pptx_cli/commands/` owns individual command implementations and thin orchestration logic

## Key data flows

### Template initialization

1. User runs `pptx init <template>.pptx --out <manifest-dir>`
2. CLI contract layer parses input and emits request metadata
3. Package analysis opens the `.pptx` as a zip package
4. Extracted structures are normalized into typed models
5. Manifest package files are written atomically
6. Response envelope returns a summary and warnings

### Deck build

1. User provides a manifest and deck spec
2. Spec is schema-validated
3. Layout references and placeholder mappings are resolved
4. Composition engine clones allowed structures and fills placeholders
5. Result is written as `.pptx`
6. Optional validation runs before success is returned

### Validation

1. User provides generated deck + manifest
2. Validation engine checks structure, assets, geometry, and fingerprints
3. CLI emits a structured pass/fail envelope and diagnostics

## External dependencies

### Confirmed runtime dependencies

- `typer`
- `pydantic`
- `lxml`
- `python-pptx`
- `PyYAML`
- `jsonschema`
- `rich`

### Provisional dependencies

- `orjson`
  - TODO: Confirm whether faster JSON serialization is worth the extra dependency.
  - Why it matters: The guide/response envelope path could benefit from predictable fast serialization.
  - How to fill this in: Benchmark standard `json` versus `orjson` after the envelope contract is implemented.

## Architectural constraints

- Public CLI name must remain `pptx`
- Python import package must avoid `pptx` namespace collision
- PyPI distribution name should remain `pptx-cli` unless an explicit migration plan is documented
- Package version should have one source of truth and support easy semantic-version bumps
- stdout must remain parseable in machine-readable mode
- write operations must support `--dry-run`
- manifest facts and human annotations must remain layered, not conflated

## Quality attributes

- determinism
- fidelity
- transparency
- portability
- safe mutation
- agent-readability
- extensibility

## Trade-offs

- Hybrid XML + high-level library manipulation is more complex than using a single slide-generation library, but materially safer for fidelity
- Agent-first CLI contract adds some upfront structure, but reduces orchestration fragility and future breaking changes
- Separate `annotations.yaml` adds one more file, but protects extracted facts from human drift

## Known unknowns

- TODO: Decide the first concrete manifest schema versioning and migration policy
  - Why it matters: Agents and wrappers need compatibility guarantees.
  - How to fill this in: Define semantic versioning rules for envelope schema, guide schema, and manifest schema.
  - Example: "Manifest schema major bumps for breaking field changes; additive fields are minor".

- TODO: Decide how much preview metadata should be coupled to future rendering backends
  - Why it matters: Overcommitting now may complicate preview implementation later.
  - How to fill this in: Implement a single canonical path field first and defer renderer-specific metadata until preview generation exists.
