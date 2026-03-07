---
name: pptx
description: >
  How to use the `pptx` CLI to create PowerPoint presentations from enterprise templates.
  Use this skill whenever the user wants to create, build, or generate PowerPoint slides or decks,
  work with .pptx templates, inspect slide layouts or placeholders, validate presentations,
  or anything related to PowerPoint generation from the command line. Also trigger when the user
  mentions deck specs, slide layouts, manifest packages, or template-bound presentation workflows.
  Even if the user just says "make me a presentation" or "create some slides", this skill applies.
---

# pptx — Template-Bound PowerPoint Generation

`pptx` is a CLI that turns a real `.pptx` template into a machine-readable manifest, then generates slides and decks **inside the original corporate design contract**. It preserves masters, themes, locked branding, and placeholder rules — instead of approximating them.

## Quick orientation

The workflow has three phases:

1. **Setup** — install the CLI and initialize a manifest from a template
2. **Discover** — explore layouts, placeholders, and theme to understand what's available
3. **Build** — create slides or full decks from structured specs, then validate

## Phase 1: Setup

### Install

```bash
uv tool install pptx-cli
# or: pip install pptx-cli
```

Verify with `pptx --version`.

### Initialize a manifest

The manifest package lives at `.pptx/` in the project root. Always check for an existing one first:

```bash
ls .pptx/manifest.yaml 2>/dev/null
```

If no manifest exists, you need a `.pptx` template file from the user. **Ask the user** to provide one — do not assume a template exists. Then initialize:

```bash
pptx init <template.pptx> --out ./.pptx
```

This extracts layouts, placeholders, assets, themes, and rules into a structured manifest package.

### Bootstrap command: `pptx guide`

Run this once to get the full CLI contract — all commands, schemas, error codes, and examples:

```bash
pptx guide --format json
```

This is your single source of truth for the CLI's capabilities. Cache the result mentally and refer to it throughout the session.

## Phase 2: Discover

Before building anything, understand what the template offers. These are all read-only commands and can run in parallel:

```bash
# List all available layouts
pptx layouts list --manifest ./.pptx --format json

# Show details for a specific layout
pptx layouts show <layout-id> --manifest ./.pptx --format json

# List placeholders for a layout (tells you what content keys are available)
pptx placeholders list <layout-id> --manifest ./.pptx --format json

# Show theme metadata
pptx theme show --manifest ./.pptx --format json

# List extracted assets
pptx assets list --manifest ./.pptx --format json

# Check for compatibility warnings
pptx doctor --manifest ./.pptx --format json
```

**Layout IDs** are slugified names derived from the template (e.g., `title-only`, `1-title-and-content`, `1-breaker-with-pattern`). Use `layouts list` to discover the exact IDs.

**Placeholder keys** are logical names like `title`, `subtitle`, `content_1`, `picture`. Use `placeholders list <layout-id>` to discover the exact keys and their supported content types for each layout.

## Phase 3: Build

### Single slide

```bash
pptx slide create \
  --manifest ./.pptx \
  --layout <layout-id> \
  --set title="Your Title" \
  --set subtitle="Your Subtitle" \
  --out ./out/slide.pptx
```

### Full deck from a spec

Create a YAML or JSON spec file, then build. See `references/deck-spec.md` for the full spec format.

```yaml
# deck.yaml
manifest: ./.pptx
metadata:
  title: My Presentation
  author: Author Name
slides:
  - layout: title-only
    content:
      title: Welcome
      subtitle: March 2026
  - layout: 1-title-and-content
    content:
      title: Key Points
      content_1: |
        First point.
        Second point.
        Third point.
```

```bash
pptx deck build \
  --manifest ./.pptx \
  --spec deck.yaml \
  --out ./out/deck.pptx
```

### Preview before writing

Always use `--dry-run` first on mutating commands to preview what will happen without writing files:

```bash
pptx deck build --manifest ./.pptx --spec deck.yaml --out ./out/deck.pptx --dry-run
```

### Validate the output

After generating a deck, validate it against the manifest:

```bash
pptx validate --manifest ./.pptx --deck ./out/deck.pptx --strict --format json
```

## Supported content types

- `text` — plain text
- `image` — image file reference
- `table` — structured table data
- `chart` — chart data
- `markdown-to-text` — markdown converted to formatted text

## Error handling

All commands return a structured JSON envelope with `ok`, `errors`, and `warnings` fields. Key exit codes:

| Exit | Meaning |
|------|---------|
| 0 | Success |
| 10 | Validation error (bad input, unknown layout/placeholder) |
| 20 | Policy error |
| 40 | Conflict (output file exists) |
| 50 | I/O error |
| 90 | Internal error |

Check `ok` first, then branch on `errors[0].code` if it's `false`.

## Typical workflow for building a presentation

1. Check for `.pptx/manifest.yaml` — if missing, ask user for a template and run `pptx init`
2. Run `pptx layouts list` to see available layouts
3. For each layout you plan to use, run `pptx placeholders list <layout-id>` to discover content keys
4. Draft a `deck.yaml` spec using only discovered layout IDs and placeholder keys
5. Preview with `pptx deck build ... --dry-run`
6. Build with `pptx deck build ... --out ./out/deck.pptx`
7. Validate with `pptx validate ...`

## Key rules

- **Only use layout IDs that appear in `layouts list`** — unknown layouts cause validation errors
- **Only use placeholder keys that appear in `placeholders list`** — unknown keys are silently ignored or cause errors
- **Always use `--manifest ./.pptx`** to point to the manifest package
- **Use `--dry-run` before writing** to catch issues early
- **Use `--format json`** on read commands to get structured output you can parse

For detailed deck spec format and advanced options, read `references/deck-spec.md`.
