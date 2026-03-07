# pptx CLI — Full Reference

## Commands

### pptx guide
Show machine-readable CLI guide with all commands, schemas, error codes.
```bash
pptx guide --format json
```

### pptx init <template> --out <dir>
Initialize a manifest package from a .pptx template. Extracts layouts, assets,
theme, and creates manifest.yaml.
```bash
pptx init Template.pptx --out ./corp-template --dry-run
pptx init Template.pptx --out ./corp-template --format json
```

Creates:
- `manifest.yaml` — The contract (layouts, placeholders, rules)
- `manifest.schema.json` — JSON Schema for the manifest format
- `annotations.yaml` — Editable metadata and overrides
- `assets/source-template.pptx` — Copy of original template
- `assets/images/` — Extracted images (logos, patterns, backgrounds)
- `assets/theme/` — Extracted theme XML
- `reports/init-report.json` — Initialization diagnostics
- `fingerprints/parts.json` — SHA-256 hashes for change detection

### pptx doctor --manifest <dir>
Check manifest compatibility. Run after init to verify readiness.
```bash
pptx doctor --manifest ./corp-template --format json
```

### pptx layouts list --manifest <dir>
List all available layouts with id, name, placeholder count.
```bash
pptx layouts list --manifest ./corp-template --format json
```

### pptx layouts show <layout-id> --manifest <dir>
Show a single layout contract with full detail.
```bash
pptx layouts show title-only --manifest ./corp-template --format json
```

### pptx placeholders list <layout-id> --manifest <dir>
List all placeholders for a layout with full contracts.
```bash
pptx placeholders list 1-title-and-content --manifest ./corp-template --format json
```

Key fields per placeholder:
- `logical_name` — Key to use in specs (title, subtitle, content_1, picture, source)
- `source_name` — Original name from template
- `placeholder_idx` — Internal index
- `placeholder_type` — title, body, object, or picture
- `supported_content_types` — Array of: text, markdown-text, image, table, chart
- `required` — Boolean
- `overflow_policy` — fit, warn, or truncate
- `text_defaults` — Object with suggested_font_size_pt, max_lines, alignment
- `left_emu`, `top_emu`, `width_emu`, `height_emu` — Position/size in EMUs

### pptx theme show --manifest <dir>
Show theme metadata: colors, fonts, effects.
```bash
pptx theme show --manifest ./corp-template --format json
```

### pptx assets list --manifest <dir>
List extracted assets with kind, path, SHA-256 hash, size.
```bash
pptx assets list --manifest ./corp-template --format json
```

### pptx slide create
Create a single-slide deck from a layout.
```bash
pptx slide create --manifest ./corp-template --layout title-only \
  --set title=Hello --set "subtitle=World" --out slide.pptx --format json
```

The `--set` flag supports:
- `key=value` — Plain text
- `key=@file.png` — Image file (detected by extension)
- `key=@file.json` — Structured content (JSON/YAML)
- `key=@file.md` — Markdown text
- `key=@file.txt` — Plain text from file

### pptx deck build
Build a full deck from a YAML or JSON spec.
```bash
pptx deck build --manifest ./corp-template --spec deck.yaml --out deck.pptx --format json
pptx deck build --manifest ./corp-template --spec deck.yaml --out deck.pptx --dry-run
```

### pptx validate
Validate a generated deck against the manifest contract.
```bash
pptx validate --manifest ./corp-template --deck deck.pptx --format json
pptx validate --manifest ./corp-template --deck deck.pptx --strict --format json
```

Checks: approved layouts, required placeholders filled, content types match,
protected elements intact, fingerprints valid.

### pptx manifest diff <left> <right>
Compare two manifest packages for additive vs breaking changes.
```bash
pptx manifest diff ./corp-template-v1 ./corp-template-v2 --format json
```

### pptx manifest schema
Emit the JSON schema for manifest.yaml.
```bash
pptx manifest schema --format json
```

### pptx wrapper generate
Generate a thin template-specific wrapper CLI scaffold.
```bash
pptx wrapper generate --manifest ./corp-template --out ./wrappers/acme --dry-run
```

---

## Deck spec format

```yaml
manifest: ./corp-template        # Path to manifest package
metadata:
  title: "Deck Title"            # Sets core_properties.title
  author: "Author Name"          # Sets core_properties.author

slides:
  - layout: layout-id            # Required: layout ID from manifest
    content:                      # Object mapping logical_name → value
      title: "Plain text value"
      subtitle: "Another text value"
      content_1: |
        Multi-line text
        with bullet points
        - Like this
      source: "Source: attribution"

  # Image content (structured object)
  - layout: picture-layout-id
    content:
      title: "Slide with image"
      picture:
        kind: image
        path: path/to/image.png

  # Table content
  - layout: some-layout
    content:
      title: "Slide with table"
      content_1:
        kind: table
        columns: ["Name", "Value", "Change"]
        rows:
          - ["Alpha", "42", "+12%"]
          - ["Beta", "38", "-3%"]

  # Chart content
  - layout: some-layout
    content:
      title: "Slide with chart"
      content_1:
        kind: chart
        chart_type: column_clustered
        categories: ["Q1", "Q2", "Q3", "Q4"]
        series:
          - name: "Revenue"
            values: [100, 120, 115, 140]
          - name: "Cost"
            values: [80, 85, 90, 95]
```

Supported chart_type values (python-pptx XL_CHART_TYPE):
column_clustered, bar_clustered, line, pie, area, scatter, etc.

---

## JSON envelope

Every command returns:
```json
{
  "schema_version": "1.0",
  "request_id": "req_...",
  "ok": true,
  "command": "deck.build",
  "result": { ... },
  "warnings": [],
  "errors": [],
  "metrics": { "duration_ms": 42 }
}
```

On failure, `ok: false` and `errors` contains objects with `code`, `message`,
`retryable`, and `suggested_action`.

---

## Error codes

| Code | Exit | Retryable | Description |
|---|---|---|---|
| ERR_VALIDATION_LAYOUT_UNKNOWN | 10 | No | Layout ID not in manifest |
| ERR_VALIDATION_PLACEHOLDER_UNKNOWN | 10 | No | Placeholder key not in layout |
| ERR_VALIDATION_PLACEHOLDER_REQUIRED | 10 | No | Required placeholder not filled |
| ERR_VALIDATION_CONTENT_TYPE | 10 | No | Content type not supported |
| ERR_IO_NOT_FOUND | 50 | No | File not found |
| ERR_CONFLICT_OUTPUT_EXISTS | 40 | No | Output path conflict |
| ERR_INTERNAL_PLACEHOLDER_MISSING | 90 | No | Placeholder not on generated slide |

---

## Concurrency rules

- Read commands (guide, layouts, placeholders, theme, assets, doctor) can run
  in parallel.
- Mutating commands (init, slide create, deck build) writing the same output
  must run sequentially.
- Validate should run after build completes on the same file.

---

## EMU reference

EMU = English Metric Unit. 1 inch = 914400 EMU. 1 cm = 360000 EMU.

Standard widescreen slide: 12192000 x 6858000 EMU (13.33" x 7.5").
