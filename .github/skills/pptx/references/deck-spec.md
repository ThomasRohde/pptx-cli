# Deck Spec Format

The deck spec is a YAML or JSON file that describes a full presentation. It is the input to `pptx deck build`.

## Schema

```yaml
# Required
slides:
  - layout: <layout-id>        # Must match an ID from `pptx layouts list`
    content:                    # Optional — keys must match placeholder logical_names
      <placeholder-key>: <value>

# Optional
manifest: <path>                # Path to manifest package (can also be passed via --manifest flag)
metadata:                       # Presentation-level metadata
  title: <string>
  author: <string>
  template_version: <string>
  # Additional arbitrary key-value pairs are allowed
```

## Slide content values

Content values depend on the placeholder's `supported_content_types` (discoverable via `pptx placeholders list <layout-id>`).

### Text content

Plain strings or multi-line YAML strings:

```yaml
- layout: 1-title-and-content
  content:
    title: My Title
    content_1: |
      Bullet point one.
      Bullet point two.
      Bullet point three.
    subtitle: Supporting context here.
```

### Image content

Reference an image file path:

```yaml
- layout: picture-layout
  content:
    picture: ./images/diagram.png
```

### Table content

Structured table data:

```yaml
- layout: table-layout
  content:
    table:
      headers: [Name, Role, Status]
      rows:
        - [Alice, Engineer, Active]
        - [Bob, Designer, Active]
```

### Chart content

Structured chart data:

```yaml
- layout: chart-layout
  content:
    chart:
      type: bar
      categories: [Q1, Q2, Q3, Q4]
      series:
        - name: Revenue
          values: [100, 150, 130, 170]
```

## Full example

```yaml
manifest: ./.pptx
metadata:
  title: Quarterly Business Review
  author: Jane Smith
  template_version: 1.0.0
slides:
  - layout: title-only
    content:
      title: Q1 2026 Business Review
      subtitle: Prepared by Jane Smith

  - layout: 1-breaker-with-pattern
    content:
      title: Financial Overview

  - layout: 1-title-and-content
    content:
      title: Revenue Summary
      content_1: |
        Total revenue: $4.2M (up 12% YoY).
        New customer acquisition: 47 accounts.
        Renewal rate: 94%.
      subtitle: All figures as of March 31, 2026.

  - layout: 1-title-and-content
    content:
      title: Key Initiatives
      content_1: |
        Platform migration: 80% complete.
        New product launch: on track for Q2.
        Hiring: 12 of 15 positions filled.

  - layout: 1-breaker-with-pattern
    content:
      title: Next Steps

  - layout: 1-title-and-content
    content:
      title: Action Items
      content_1: |
        Complete platform migration by April 30.
        Finalize Q2 product launch plan.
        Fill remaining 3 open positions.
      subtitle: Review again at May steering committee.
```

## Discovering valid layout IDs and placeholder keys

Before writing a spec, always discover what's available:

```bash
# Get all layout IDs
pptx layouts list --manifest ./.pptx --format json

# Get placeholder keys for a specific layout
pptx placeholders list <layout-id> --manifest ./.pptx --format json
```

The `placeholders list` output includes:
- `logical_name` — the key to use in your spec's `content` block
- `placeholder_type` — what kind of placeholder it is (TITLE, SUBTITLE, BODY, etc.)
- `supported_content_types` — what content formats are accepted
- `required` — whether this placeholder must be filled
- `guidance_text` — hint text from the template about intended use

## Building from the spec

```bash
# Preview first
pptx deck build --manifest ./.pptx --spec deck.yaml --out ./out/deck.pptx --dry-run

# Build
pptx deck build --manifest ./.pptx --spec deck.yaml --out ./out/deck.pptx

# Validate
pptx validate --manifest ./.pptx --deck ./out/deck.pptx --strict --format json
```
