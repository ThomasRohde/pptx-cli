---
name: pptx-deck-builder
description: >
  Build enterprise PowerPoint decks using the `pptx` and `excal` CLI tools.
  Use this skill whenever the user wants to create a PowerPoint presentation,
  generate slides from a template, build a deck with diagrams, or produce
  consulting-style slide content. Also triggers for requests involving
  .pptx files, slide decks, presentation generation, Excalidraw diagrams
  for slides, or McKinsey/consulting-style deliverables. If the user mentions
  "pptx", "excal", "slides", "deck", "presentation", or "PowerPoint" in the
  context of creating output, use this skill.
---

# pptx + excal Deck Builder

Build template-bound, validated PowerPoint decks with professional diagrams.
This skill combines two CLI tools (`pptx` for slide generation, `excal` for
diagrams) with consulting-grade presentation principles.

## When to read the reference files

- **`references/pptx-workflow.md`** — Read when you need the full `pptx` CLI
  command reference, manifest structure, placeholder details, deck spec format,
  error codes, or image-handling workarounds.
- **`references/excal-diagrams.md`** — Read when you need to create Excalidraw
  diagrams, render them to PNG, or understand the scene JSON format.
- **`references/mckinsey-style.md`** — Read when the user asks for
  consulting-style, executive, strategy, or McKinsey-style presentations. Also
  read when you need guidance on action titles, storyline structure, slide
  archetypes, or the Pyramid Principle.

---

## Core workflow

Every deck project follows this sequence. Do not skip steps.

### Step 0 — Think before building

Before touching any tool, resolve the presentation's purpose:

1. What decision or outcome is this deck driving?
2. What is the single governing thought or recommendation?
3. What are the 3-5 supporting arguments?
4. What evidence proves each argument?

If the user's request is vague, ask clarifying questions. A deck without a
clear purpose becomes a collection of slides instead of an argument.

For consulting-style decks, write a **ghost deck** first — a title-only
outline where each slide title states the takeaway (not the topic). The titles
alone should tell a coherent story. See `references/mckinsey-style.md`.

### Step 1 — Initialize the manifest (one-time setup)

Check if a manifest package already exists. If not, initialize from the
template:

```bash
pptx init Template.pptx --out ./corp-template --format json
```

Then run the doctor to verify compatibility:

```bash
pptx doctor --manifest ./corp-template --format json
```

**Important:** After init, picture-type placeholders are missing `image` in
their `supported_content_types`. Fix this before using images — see the
image handling section below.

### Step 2 — Discover layouts and placeholders

List available layouts, then inspect placeholders for the ones you plan to use:

```bash
pptx layouts list --manifest ./corp-template --format json
pptx placeholders list <layout-id> --manifest ./corp-template --format json
```

Read-only commands can run in parallel for speed. Key information per
placeholder:

- `logical_name` — The key to use in your spec (e.g., `title`, `content_1`)
- `placeholder_type` — `title`, `body`, `object`, or `picture`
- `supported_content_types` — What it accepts (`text`, `markdown-text`,
  `image`, `table`, `chart`)
- `required` — Whether it must be filled
- `text_defaults` — Suggested font size, max lines

Also inspect theme colors and assets if you need to match the visual identity:

```bash
pptx theme show --manifest ./corp-template --format json
pptx assets list --manifest ./corp-template --format json
```

### Step 3 — Create diagrams with excal (if needed)

When the deck needs diagrams, flowcharts, or visual explanations, create them
as Excalidraw scenes and render to PNG.

**Critical: match the placeholder aspect ratio.** Before designing a diagram,
check the target placeholder's dimensions in EMUs (from the placeholders
command). Calculate the aspect ratio and design the diagram to match.

For a picture placeholder that is 6642100 x 5514313 EMU (~1.2:1), design a
diagram roughly 540px wide x 450px tall. A mismatch causes cropping or
letterboxing.

```bash
# Create the .excalidraw file, then:
excal validate diagrams/my-diagram.excalidraw
excal render diagrams/my-diagram.excalidraw --outDir ./out/diagrams --png --scale 4 --no-background
```

Use `--no-background` for transparent backgrounds that blend with slide
backgrounds. Use `--scale 4` for crisp output — scale 2 looks blurry on
large slide placeholders because the pixel density is too low for the
physical size. Scale 4 ensures diagrams stay sharp even on high-DPI
displays and when projected.

**Match the template's visual identity.** Diagrams should feel like they belong
on the slide, not like foreign objects pasted in. Two things matter most:

1. **Use `fontFamily: 1`** (Excalidraw's hand-drawn style) for diagram text.
   This gives a clean whiteboard aesthetic that contrasts well with formal slide
   typography and looks intentional rather than mismatched.

2. **Pull colors from the template theme.** Run `pptx theme show --manifest
   ./corp-template --format json` and use the accent colors for fills and
   strokes. Common mapping:
   - Primary elements → accent1 (e.g., `#003778`)
   - Secondary elements → accent2 (e.g., `#4673C3`)
   - Tertiary/subtle → accent3 (e.g., `#87AAE1`)
   - Success/positive → `#087f5b` (green)
   - Labels/muted → `#868e96` (gray)

   Avoid arbitrary colors — diagrams that use theme colors integrate seamlessly
   with the slide's color palette.

See `references/excal-diagrams.md` for the full Excalidraw scene format and
element types.

### Step 4 — Write the deck spec

Create a YAML file mapping layouts to content:

```yaml
manifest: ./corp-template
metadata:
  title: "Presentation Title"
  author: "Author Name"
slides:
  - layout: layout-id
    content:
      title: "Action title stating the takeaway"
      subtitle: "Optional context"
      content_1: |
        - Bullet point one
        - Bullet point two
      source: "Source: Data attribution"

  - layout: picture-layout-id
    content:
      title: "Slide title"
      picture:
        kind: image
        path: out/diagrams/my-diagram.png
      content_1: |
        Supporting text alongside the image
```

**Content value formats:**
- Plain string → treated as `text`
- Multi-line YAML block scalar → treated as `text` with line breaks
- `{ kind: "image", path: "path/to/file.png" }` → image insertion
- `{ kind: "table", columns: [...], rows: [[...], ...] }` → table
- `{ kind: "chart", chart_type: "column_clustered", categories: [...], series: [{name: "...", values: [...]}] }` → chart

### Step 5 — Build and validate

```bash
pptx deck build --manifest ./corp-template --spec deck.yaml --out ./out/deck.pptx --format json
pptx validate --manifest ./corp-template --deck ./out/deck.pptx --strict --format json
```

Always validate with `--strict`. Fix any issues and rebuild. If the output
file is locked (open in PowerPoint), write to a new filename.

Use `--dry-run` on build to preview without writing files.

---

## Image handling — known issues and fixes

### Picture placeholders need `image` added to supported_content_types

After `pptx init`, picture-type placeholders only list `["text",
"markdown-text"]`. You must edit `manifest.yaml` to add `- image`:

```yaml
# Find all placeholder_type: picture entries and add image:
    placeholder_type: picture
    guidance_lines: []
    supported_content_types:
    - text
    - markdown-text
    - image          # ← add this line
```

Use a replace-all to fix every occurrence at once.

### Image scaling — fit vs crop

The default `insert_picture` behavior crops to fill, which clips content when
aspect ratios differ. The composition code should be patched to scale images to
fit within placeholder bounds instead. The fix in
`pptx_cli/core/composition.py` replaces the image insertion block:

```python
# After insert_picture, reset crops and scale to fit:
ph_left, ph_top = shape.left, shape.top
ph_width, ph_height = shape.width, shape.height
pic = shape.insert_picture(str(image_path))
pic.crop_left = pic.crop_right = pic.crop_top = pic.crop_bottom = 0
img = pic.image
img_w, img_h = img.size
img_aspect = img_w / img_h
ph_aspect = ph_width / ph_height
if img_aspect > ph_aspect:
    new_width = ph_width
    new_height = int(ph_width / img_aspect)
else:
    new_height = ph_height
    new_width = int(ph_height * img_aspect)
pic.left = ph_left + (ph_width - new_width) // 2
pic.top = ph_top + (ph_height - new_height) // 2
pic.width = new_width
pic.height = new_height
```

Check whether this patch is already applied before applying it. Read the
`_apply_content_value` function in `composition.py` — if it only has
`shape.insert_picture(str(image_path))` with no scaling logic, the patch
is needed.

---

## Slide writing principles

These apply to every deck, not just consulting-style ones.

### Action titles, not topic labels

Every slide title should state the takeaway — what the audience should
conclude — not just name the topic.

- Bad: "Market Overview"
- Good: "Nordic retail margins will remain under pressure through 2027"

### One slide, one message

If a slide has two insights, split it into two slides. The body must prove
the headline.

### Source attribution

Data-driven slides need source lines. Use the `source` placeholder when
available.

### Storyline coherence

A reader should be able to read only the slide titles, in order, and
understand the full argument.

For full consulting-style guidance including the Pyramid Principle, MECE
structuring, ghost decks, slide archetypes, and executive summary
construction, read `references/mckinsey-style.md`.

---

## Layout selection guide

Match content to the right layout:

| Content type | Suggested layout patterns |
|---|---|
| Opening / title | front-page layouts (with pattern or picture) |
| Agenda / TOC | agenda layouts (use plain text items without numbered prefixes — the layout often auto-numbers) |
| Section divider | breaker layouts |
| Single topic with bullets | title-and-content |
| Side-by-side comparison | two-contents |
| Topic with description header | title-description-and-content |
| Image with explanation | picture-right-text-and-box (or similar) |
| Minimal / custom | title-only or blank-with-logo |
| Closing | end-slide layouts |

When a template has numbered variants (e.g., `1-title-and-content`,
`2-title-description-and-content`), inspect the placeholders of each to
understand the differences. Numbered variants often differ in placeholder
arrangement, background color, or description fields.

---

## Quick reference — common commands

```bash
# One-time setup
pptx init Template.pptx --out ./manifest-dir --format json
pptx doctor --manifest ./manifest-dir --format json

# Inspection (safe to parallelize)
pptx layouts list --manifest ./manifest-dir --format json
pptx placeholders list <layout-id> --manifest ./manifest-dir --format json
pptx theme show --manifest ./manifest-dir --format json
pptx assets list --manifest ./manifest-dir --format json

# Single slide (quick test)
pptx slide create --manifest ./manifest-dir --layout <id> --set title="Hello" --out slide.pptx

# Full deck
pptx deck build --manifest ./manifest-dir --spec deck.yaml --out deck.pptx --format json
pptx validate --manifest ./manifest-dir --deck deck.pptx --strict --format json

# Diagrams
excal validate diagram.excalidraw
excal render diagram.excalidraw --outDir ./out --png --scale 4 --no-background

# Template versioning
pptx manifest diff ./v1-manifest ./v2-manifest --format json
```

---

## Error handling

All `pptx` commands return JSON envelopes with `ok`, `errors`, and exit codes:

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 10 | Validation error (bad layout, missing placeholder, wrong content type) |
| 20 | Policy error |
| 40 | Conflict (output file exists / locked) |
| 50 | I/O error (file not found) |
| 90 | Internal error |

If output file is locked (exit code 40 or PermissionError), write to a
different filename — do not retry.

All `excal` errors also return JSON envelopes. Key codes: exit 10 for
invalid scene JSON, exit 20 for render failures, exit 50 for I/O errors.
