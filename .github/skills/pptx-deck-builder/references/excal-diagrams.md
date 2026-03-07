# excal CLI — Diagram Reference

## Commands

### excal inspect <file|->
Inspect scene structure: element counts, bounds, metadata.
```bash
excal inspect diagram.excalidraw
```

### excal validate <file|->
Validate scene: frame refs, bound text, arrow bindings, assets.
```bash
excal validate diagram.excalidraw
excal validate diagram.excalidraw --check-assets
```

### excal render <file|->
Render to SVG, PNG, or PDF. PNG/PDF require Playwright.
```bash
excal render diagram.excalidraw --outDir ./out --png --scale 2 --no-background
excal render diagram.excalidraw --outDir ./out --svg
excal render diagram.excalidraw --outDir ./out --png --dark-mode
excal render diagram.excalidraw --outDir ./out --png --frame "Frame Name"
```

Flags:
- `--outDir <dir>` — Output directory (default: .)
- `--svg` — Export SVG (default format)
- `--png` — Export PNG (requires Playwright)
- `--pdf` — Export PDF (requires Playwright)
- `--dark-mode` — Dark theme
- `--no-background` — Transparent background
- `--scale <n>` — Scale factor for PNG (default: 2)
- `--padding <n>` — Padding in pixels (default: 20)
- `--frame <id|name>` — Export specific frame only
- `--element <id>` — Export specific element only
- `--dry-run` — Validate pipeline without writing

### excal guide
Output CLI guide as Markdown.

### excal skill
Return Excalidraw domain knowledge.

---

## Excalidraw scene format

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "manual",
  "elements": [ ... ],
  "appState": { "viewBackgroundColor": "#ffffff" },
  "files": {}
}
```

## Element types

| Type | Description |
|---|---|
| rectangle | Box shape |
| diamond | Diamond/rhombus |
| ellipse | Circle/ellipse |
| arrow | Arrow connector |
| line | Line/polyline |
| text | Text label |
| image | Embedded image |
| frame | Grouping frame |

## Key element properties

Every element has: `id`, `type`, `x`, `y`, `width`, `height`, `isDeleted`,
`opacity`, `groupIds`, `frameId`, `angle`, `seed`.

Shape-specific:
- `strokeColor` — Border color (hex)
- `backgroundColor` — Fill color (hex)
- `fillStyle` — "solid", "hachure", "cross-hatch"
- `strokeWidth` — Border width (1-4 typical)
- `roundness` — `{ "type": 3 }` for rounded corners
- `boundElements` — Array of `{ id, type }` for bound text/arrows

Text-specific:
- `text` — The text content (use \n for line breaks)
- `fontSize` — Font size in px
- `fontFamily` — 1 (hand-drawn), 2 (normal), 3 (monospace)
- `textAlign` — "left", "center", "right"
- `verticalAlign` — "top", "middle", "bottom"
- `containerId` — ID of container shape (for bound text)

Arrow-specific:
- `points` — Array of [x, y] relative to element position
- `startBinding` — `{ elementId, focus, gap }`
- `endBinding` — `{ elementId, focus, gap }`

## Bound text pattern

Text bound to a container:
1. Container has `boundElements: [{ id: "text-id", type: "text" }]`
2. Text has `containerId: "container-id"`
3. Text position is relative but overridden by container

## Styling for professional presentations

When creating diagrams for slide decks, use `fontFamily: 1` (the hand-drawn
Excalidraw style) for a distinctive, approachable look. This gives diagrams
a clean whiteboard aesthetic that contrasts well with formal slide typography.

Use the template's theme colors for visual consistency. Extract colors from
`pptx theme show`:

```bash
pptx theme show --manifest ./corp-template --format json
```

Use the theme's accent colors for fills and strokes. Common pattern:
- Primary elements: accent1 (e.g., `#003778`)
- Secondary elements: accent2 (e.g., `#4673C3`)
- Tertiary/subtle: accent3 (e.g., `#87AAE1`)
- Contrast/alternative: accent5/accent6 for a different hue
- Success/positive: `#087f5b` (green)
- Labels/muted: `#868e96` (gray)

### Aspect ratio matching

**This is critical.** Before designing a diagram, check the target
placeholder's EMU dimensions and calculate its aspect ratio:

```
aspect = width_emu / height_emu
```

Design the diagram's bounding box to match. For a 1.2:1 placeholder, aim for
~540x450 px. For a 2:1 placeholder, aim for ~600x300 px.

Vertical/stacked layouts (top-to-bottom flow) work well for nearly-square
placeholders. Horizontal layouts work for wide placeholders.

---

## Error codes

| Code | Exit | Description |
|---|---|---|
| ERR_VALIDATION_INVALID_JSON | 10 | Input is not valid JSON |
| ERR_VALIDATION_INVALID_SCENE | 10 | Scene structure validation failed |
| ERR_RENDER_BROWSER_UNAVAILABLE | 20 | Playwright not installed |
| ERR_RENDER_EXPORT_FAILED | 20 | Export failed in browser |
| ERR_IO_READ_FAILED | 50 | Failed to read input |
| ERR_IO_WRITE_FAILED | 50 | Failed to write output |

---

## Concurrency

Reads (inspect, validate) and renders are all safe to run concurrently.
Each render launches its own browser instance.
