# pptx

[![PyPI version](https://img.shields.io/badge/pypi-v1.1.0-blue.svg)](https://pypi.org/project/pptx-cli/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Template-bound PowerPoint generation for enterprise decks.

`pptx` turns a real `.pptx` template into a machine-readable manifest, then generates slides and decks **inside the original corporate design contract** instead of trying to approximate it from prompts.

If your organization cares about slide masters, locked branding, placeholder rules, layout fidelity, and CI validation, this is the tool.

The package is published to PyPI as [`pptx-cli`](https://pypi.org/project/pptx-cli/) and installs the `pptx` command.

## Why `pptx` exists

Most AI slide generators fail where enterprise users care most:

- layouts drift from the official template
- placeholders get used inconsistently
- static branding moves or disappears
- theme styling gets recreated approximately instead of preserved exactly
- decks look plausible but are structurally wrong

`pptx` takes a different approach:

1. **Initialize from a real template**
2. **Extract a manifest of layouts, placeholders, assets, and rules**
3. **Generate only within those approved boundaries**
4. **Validate output before it reaches humans, CI, or customers**

The result is a CLI that behaves more like a compiler toolchain than a drawing tool.

## Features

- Initialize a manifest package from a real enterprise `.pptx`
- Inspect layouts, placeholders, themes, assets, and compatibility warnings
- Build slides from approved layouts only
- Build full decks from JSON/YAML specs
- Preserve template-bound masters, themes, geometry, and protected elements
- Validate generated decks against manifest rules and template fingerprints
- Diff template versions to detect breaking changes
- Generate template-specific wrapper CLIs
- Expose an agent-first machine contract with:
  - stable JSON response envelopes
  - structured error codes
  - documented exit codes
  - a built-in `guide` command
  - `--dry-run` support for mutating commands

## Installation

### With `uv` (recommended)

```bash
uv tool install pptx-cli
```

### From the repository

```bash
uv tool install git+https://github.com/ThomasRohde/pptx-cli.git
```

### From PyPI with pip

```bash
pip install pptx-cli
```

### Verify installation

```bash
pptx --version
pptx guide --format json
```

## Quick start

The repository includes a real sample template at `Template.pptx`. The examples below use that file and the layout IDs currently extracted from it.

Initialize a template package from an existing PowerPoint file:

```bash
pptx init ./Template.pptx --out ./corp-template
```

Inspect the extracted layouts:

```bash
pptx layouts list --manifest ./corp-template
pptx layouts show title-only --manifest ./corp-template
pptx placeholders list 1-title-and-content --manifest ./corp-template
```

Create a single slide:

```bash
pptx slide create \
  --manifest ./corp-template \
  --layout title-only \
  --set title="Enterprise AI Operating Model" \
  --set subtitle="March 2026" \
  --out ./out/operating-model-slide.pptx
```

Build a full deck from a spec:

```bash
pptx deck build \
  --manifest ./corp-template \
  --spec ./deck.yaml \
  --out ./out/operating-model.pptx
```

Validate the result:

```bash
pptx validate \
  --manifest ./corp-template \
  --deck ./out/operating-model.pptx \
  --strict
```

Preview the write before touching the filesystem:

```bash
pptx deck build \
  --manifest ./corp-template \
  --spec ./deck.yaml \
  --out ./out/operating-model.pptx \
  --dry-run
```

Replace an existing output file explicitly:

```bash
pptx deck build \
  --manifest ./corp-template \
  --spec ./deck.yaml \
  --out ./out/operating-model.pptx \
  --overwrite
```

## Example deck spec

```yaml
manifest: ./corp-template
metadata:
  title: Enterprise AI Operating Model
  author: Thomas Rohde
  template_version: 1.2.0
slides:
  - layout: title-only
    content:
      title: Enterprise AI Operating Model
      subtitle: March 2026
  - layout: 1-breaker-with-pattern
    content:
      title: Why this change
      subtitle: Preserve, don’t imitate
  - layout: 1-title-and-content
    content:
      title: Core idea
      content_1: |
        Preserve the template.
        Generate inside its rules.
      subtitle: Layouts and placeholders become machine-readable contracts.
```

## Core commands

```text
pptx guide
pptx init
pptx doctor
pptx layouts list
pptx layouts show
pptx placeholders list
pptx theme show
pptx assets list
pptx slide create
pptx deck build
pptx validate
pptx manifest diff
pptx manifest schema
pptx completions generate
pptx wrapper generate
```

## Manifest package layout

A template initialization produces a package like this:

```text
corp-template/
  manifest.yaml
  manifest.schema.json
  annotations.yaml
  assets/
    images/
    media/
    embedded/
  previews/
    layouts/
  fingerprints/
    parts.json
  reports/
    init-report.json
```

### Key files

- `manifest.yaml` — extracted source-of-truth contract
- `manifest.schema.json` — schema for validation and tooling
- `annotations.yaml` — human-authored semantic annotations and placeholder overrides layered over extracted facts
- `reports/init-report.json` — warnings, unsupported features, and compatibility findings
- `fingerprints/parts.json` — structural fingerprints used for validation and diffing

## Supported v1 content types

`pptx` supports these placeholder content types in v1:

- text
- image
- table
- chart
- markdown-text

## Structured content objects

`pptx slide create --set picture=@diagram.png` automatically normalizes the file into an
image payload. In deck specs, use the equivalent structured object explicitly:

```yaml
slides:
  - layout: 3-front-page-title-and-picture
    content:
      title: Workflow
      picture:
        kind: image
        path: out/diagrams/workflow.png
        image_fit: fit
```

`image_fit` defaults to `fit`, which preserves the whole image inside the placeholder.
Use `cover` to opt back into crop-to-fill behavior.

Tables and charts use the same `kind` pattern:

```yaml
slides:
  - layout: 1-title-and-content
    content:
      title: Status by workstream
      content_1:
        kind: table
        columns: [Workstream, Status]
        rows:
          - [Platform, Active]
          - [Sales, Planned]
  - layout: 1-title-and-content
    content:
      title: Quarterly trend
      content_1:
        kind: chart
        chart_type: column_clustered
        categories: [Q1, Q2, Q3]
        series:
          - name: Revenue
            values: [12, 15, 18]
```

### Fidelity model

Guaranteed in scope:

- slide size and orientation
- master/layout relationships
- approved placeholder geometry
- protected static elements
- preserved theme references where supported
- deterministic content mapping into approved placeholders

Best-effort in v1:

- advanced chart workbook behavior
- highly custom chart or table styling internals
- content-sensitive text reflow edge cases
- animations and transitions

## Agent-first CLI contract

`pptx` is designed to be scriptable by both humans and coding agents.

### Structured response envelope

In machine-readable mode, commands return a single JSON envelope on stdout:

```json
{
  "schema_version": "1.0",
  "request_id": "req_20260307_120000_abcd",
  "ok": true,
  "command": "layouts.list",
  "result": {},
  "warnings": [],
  "errors": [],
  "metrics": {
    "duration_ms": 42
  }
}
```

### Output rules

- stdout is reserved for structured machine output
- stderr is used for progress and diagnostics
- `LLM=true` enables minimal non-decorative output behavior
- `--dry-run` previews mutating commands without writing files

### Discoverability

Use `guide` to retrieve the CLI contract in one call:

```bash
pptx guide --format json
```

That output includes:

- commands and subcommands
- input/output schema references
- examples
- error-code taxonomy
- exit-code mapping
- identifier conventions

## Exit codes

`pptx` uses stable exit-code categories for automation:

| Exit code | Meaning |
|---|---|
| `0` | Success |
| `10` | Validation or schema error |
| `20` | Permission or policy failure |
| `40` | Conflict or stale-state failure |
| `50` | I/O or package read/write failure |
| `90` | Internal error |

## Safety model

Mutating commands support preview-first workflows and safe writes:

- `--dry-run` for non-destructive previews
- structured change summaries for write operations
- explicit override flags for dangerous operations
- temporary-file staging and atomic replacement where possible

Because PowerPoint files are ZIP-based packages wearing office clothes, half the job is content generation and the other half is not breaking them.

## Wrapper CLIs

You can generate a template-specific wrapper CLI for teams that want a narrower interface:

```bash
pptx wrapper generate \
  --manifest ./corp-template \
  --out ./wrappers/acme-pptx
```

In v1, wrapper generation emits a thin Python package scaffold that delegates to the shared `pptx` engine.

## Validation and governance

`pptx validate` checks both structure and fidelity constraints, including:

- master/layout usage
- placeholder mapping correctness
- required placeholder presence
- schema compliance of deck specs
- missing assets or broken relationships
- fingerprint mismatches for protected components
- geometry drift for locked objects and placeholders

This makes `pptx` suitable for:

- local authoring workflows
- CI pipelines
- agent-driven deck generation
- enterprise template governance

## Versioning and diffing

When templates change, `pptx` can compare manifest packages:

```bash
pptx manifest diff ./corp-template-v1 ./corp-template-v2
```

Diffs highlight:

- added or removed layouts
- placeholder contract changes
- alias changes
- geometry changes
- theme/font changes
- asset changes
- additive vs. breaking changes

## Platform support

- Windows
- macOS
- Linux

Microsoft PowerPoint is **not required** to run the CLI.

## Use cases

- enterprise strategy decks
- consulting deliverables
- board and steering-committee presentations
- corporate communications templates
- internal automation pipelines generating `.pptx` output from structured data
- AI-assisted deck generation with strict branding control

## Development

### Sample template for local testing

The repository root includes `Template.pptx`, which is currently used for:

- CLI integration tests
- README quick-start examples
- local manual smoke tests while the fixture catalog grows

If additional sanitized templates are introduced later, they should live under `tests/fixtures/templates/` with a short note describing their scenario coverage.

Clone the repository and sync the development environment:

```bash
git clone https://github.com/ThomasRohde/pptx-cli.git
cd pptx-cli
uv sync --group dev
```

Run the test suite:

```bash
uv run pytest
```

Run linting and type checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

## Versioning

The project uses semantic versioning with a **single source of truth** in `src/pptx_cli/__init__.py`.

Use the helper script to bump versions safely:

```bash
uv run python scripts/bump_version.py patch
uv run python scripts/bump_version.py minor
uv run python scripts/bump_version.py major
```

This commits the version change, creates an annotated `v*` tag, and pushes — which triggers the publish workflow automatically. Use `--no-push` to tag locally without pushing.

This updates the package version used for builds and PyPI publishing without needing to edit multiple files manually.

## Documentation

- `PRD.md` — product definition and scope
- `CLI-MANIFEST.md` — agent-first CLI design principles adopted by this project
- `SCAFFOLD.md` — project scaffolding instructions

## Roadmap highlights

- richer preview generation
- deeper table/chart plugins
- broader enterprise policy packs
- multi-template registries
- post-v1 MCP integration

## Contributing

Contributions are welcome.

Please open an issue or discussion for:

- new placeholder/content type support
- template edge cases
- manifest schema changes
- CLI contract changes
- validation or fidelity bugs

For larger changes, include:

- the motivating template behavior
- expected vs. actual output
- sample manifest or sanitized `.pptx` structure where possible

## License

MIT
