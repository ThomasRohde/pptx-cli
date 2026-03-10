"""Build a human-readable YAML reference for deck specs.

Designed to be pasted into LLM prompts so the model knows how to
author valid ``pptx deck build`` input.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from pptx_cli.core.manifest_store import load_effective_manifest
from pptx_cli.models.manifest import LayoutContract, ManifestDocument

# ---------------------------------------------------------------------------
# Clipboard helper
# ---------------------------------------------------------------------------


def copy_to_clipboard(text: str) -> bool:
    """Copy *text* to the system clipboard.  Returns True on success."""
    if sys.platform == "win32":
        cmd = ["clip"]
    elif sys.platform == "darwin":
        cmd = ["pbcopy"]
    else:
        cmd = ["xclip", "-selection", "clipboard"]
    try:
        subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            check=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return False
    return True


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_OUTPUT_FORMAT = """\
<output-format>
IMPORTANT: Your output MUST be a YAML deck spec, not a binary .pptx file.
Do NOT attempt to generate PowerPoint XML, base64 data, or any format
other than the YAML shown below.  The `pptx deck build` CLI tool handles
all PowerPoint rendering — you only provide the YAML.

Preferred: offer the YAML as a downloadable file (e.g. a download link or
file attachment named "deck.yaml") so the user can save it directly.
Fallback: emit a single ```yaml code block the user can copy-paste into
a .yaml file and then run `pptx deck build -f deck.yaml`.
</output-format>"""

_STYLE_GUIDE = """\
<style-guide>
Follow these principles to produce decision-grade slides.

Structure
- Lead with the answer.  Do not build up to the conclusion.
- Pyramid Principle: governing thought -> supporting arguments -> evidence.
- Arguments must be MECE (mutually exclusive, collectively exhaustive).
- One slide = one message.  Two insights -> two slides.

Titles
- Use action titles, not topic labels.  The title states the takeaway.
  Bad:  "Market overview"
  Good: "Nordic retail banking margins will remain under pressure through 2027"
- Title storyline reads on its own - skim only titles and understand the
  full argument.
- Formulas:
    Insight:        "[What happened] because [driver]"
    Comparison:     "[A] outperforms [B] on [criterion]"
    Implication:    "[Fact] puts [objective] at risk"
    Recommendation: "[Org] should [action] to achieve [outcome]"

Executive summary slide
- Situation: what context everyone agrees on.
- Complication: what changed or created urgency.
- Answer: the recommended response.
- Support: 2-3 reasons the answer is correct.

Deck sequence (typical)
1. Title page
2. Executive summary (situation -> complication -> resolution)
3. Context / problem framing (only enough to orient)
4. Analysis body (current state -> root causes -> options -> recommendation)
5. Recommendation (explicit, decision-ready)
6. Implementation / roadmap
7. Risks and mitigations
8. Appendix (source data, benchmarks, methodology)

Body content
- Every claim backed by evidence.  The body proves the headline.
- Quantify.  Replace vague adjectives with measured claims.
- Keep text tight: verbs, short bullets, no filler.
- Move backup detail to appendix - main story stays focused.
</style-guide>"""

_GENERIC_SLIDE_SCHEMA = """\
<slide-schema>
Use this schema to draft presentation content.  Layout assignment and
template binding happen later, so focus on the slides themselves.

metadata:
  title: "<deck title>"
  author: "<author name>"

slides:
  - title: "Slide heading"
    body: |
      - Bullet one
      - Bullet two
    notes: |
      Talk track for this slide.

  - title: "Data slide"
    body: |
      Key observations from the quarter.
    table:
      kind: table
      columns: [Col A, Col B]
      rows:
        - [val1, val2]
        - [val3, val4]
    notes: Additional context.

  - title: "Trend slide"
    body: |
      Revenue grew 50% year-over-year.
    chart:
      kind: chart
      chart_type: column_clustered
      categories: [Q1, Q2, Q3]
      series:
        - name: Revenue
          values: [12, 15, 18]

  - title: "Visual slide"
    image:
      kind: image
      path: path/to/image.png
      image_fit: fit
</slide-schema>"""

_GENERIC_CONTENT_RULES = """\
<content-rules>
- Each slide MUST have a "title".
- Use "body" for the main text area.  Markdown is auto-detected
  (headings, bullets, **bold**, *italic*).
- Use "table", "chart", or "image" keys for structured content.
  chart_type accepts: column_clustered, bar_clustered, line, pie.
  image_fit accepts: "fit" (default) or "cover".
- "notes" is optional speaker-notes text (markdown ok).
- Do NOT include a "layout" key - layout is assigned later when
  binding to a corporate template.
</content-rules>"""

_TEMPLATE_CONTENT_RULES = """\
<content-rules>
- Each slide MUST have a "layout" key matching one of the layout IDs
  listed in the <layouts> section.
- Each slide MUST have a "content" dict that maps placeholder names
  (from the layout's placeholders) to values.
- Content type dispatch:
  - Plain text or markdown: provide a string value directly.
    Markdown is auto-detected (headings, bullets, **bold**, *italic*).
  - Image: { kind: image, path: path/to/image.png, image_fit: fit }
    image_fit accepts: "fit" (default) or "cover".
  - Table: { kind: table, columns: [...], rows: [[...], ...] }
  - Chart: { kind: chart, chart_type: column_clustered, categories: [...],
    series: [{ name: ..., values: [...] }] }
    chart_type accepts: column_clustered, bar_clustered, line, pie.
- Respect "required" and "max_lines" guidance from the layout definitions.
- "notes" is optional speaker-notes text (markdown ok) at the slide level.
</content-rules>"""

# Recompose generic schema from shared pieces
_GENERIC_SCHEMA = (
    _OUTPUT_FORMAT
    + "\n\n"
    + _GENERIC_SLIDE_SCHEMA
    + "\n\n"
    + _GENERIC_CONTENT_RULES
    + "\n\n"
    + _STYLE_GUIDE
    + "\n"
)


# ---------------------------------------------------------------------------
# Template-enriched schema helpers
# ---------------------------------------------------------------------------


def _placeholder_summary(ph: Any) -> dict[str, Any]:
    """Compact summary of a placeholder contract."""
    entry: dict[str, Any] = {
        "types": ph.supported_content_types,
    }
    if ph.required:
        entry["required"] = True
    if ph.guidance_text:
        entry["guidance"] = ph.guidance_text
    cap = ph.estimated_text_capacity
    if cap is not None:
        entry["max_lines"] = cap.max_lines
    return entry


def _layout_section(layout: LayoutContract) -> dict[str, Any]:
    """Build a dict describing one layout for the reference doc."""
    section: dict[str, Any] = {}
    if layout.description:
        section["description"] = layout.description
    if layout.aliases:
        section["aliases"] = layout.aliases
    placeholders: dict[str, Any] = {}
    for ph in layout.placeholders:
        placeholders[ph.logical_name] = _placeholder_summary(ph)
    section["placeholders"] = placeholders
    return section


def _example_slide(layout: LayoutContract) -> dict[str, Any]:
    """Generate an example slide entry using real placeholder names."""
    content: dict[str, str] = {}
    for ph in layout.placeholders:
        if "image" in ph.supported_content_types and "text" not in ph.supported_content_types:
            content[ph.logical_name] = "{ kind: image, path: path/to/image.png }"
        else:
            content[ph.logical_name] = f"<{ph.logical_name} text>"
    slide: dict[str, Any] = {"layout": layout.id, "content": content}
    return slide


def _build_layouts_section(manifest: ManifestDocument) -> str:
    """Return the <layouts> XML section with all layout definitions."""
    layouts_ref: dict[str, Any] = {}
    for layout in manifest.layouts:
        layouts_ref[layout.id] = _layout_section(layout)
    layouts_yaml = yaml.safe_dump(layouts_ref, sort_keys=False, allow_unicode=True, width=120)
    return f"<layouts>\n{layouts_yaml}</layouts>"


def _build_deck_schema_section(manifest: ManifestDocument) -> str:
    """Return the <deck-schema> XML section with DeckSpec example."""
    examples: list[dict[str, Any]] = []
    # Use up to 4 representative layouts for examples
    for layout in manifest.layouts[:4]:
        examples.append(_example_slide(layout))

    example_spec: dict[str, Any] = {
        "metadata": {
            "title": "<deck title>",
            "author": "<author name>",
        },
        "slides": examples,
    }
    example_yaml = yaml.safe_dump(example_spec, sort_keys=False, allow_unicode=True, width=120)

    prose = (
        f"Use this schema to draft presentation content for the "
        f'"{manifest.template.name}" template.\n'
        f"Each slide must reference a layout from the <layouts> section and "
        f"provide content for its placeholders.\n\n"
    )
    return f"<deck-schema>\n{prose}{example_yaml}</deck-schema>"


def _build_template_schema(manifest: ManifestDocument) -> str:
    """Compose the unified template-bound schema document."""
    parts = [
        _OUTPUT_FORMAT,
        "",
        _build_deck_schema_section(manifest),
        "",
        _build_layouts_section(manifest),
        "",
        _TEMPLATE_CONTENT_RULES,
        "",
        _STYLE_GUIDE,
    ]
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_schema_document(template_dir: Path | None = None) -> str:
    """Return the full reference document as a string."""
    if template_dir is not None:
        manifest = load_effective_manifest(template_dir)
        return _build_template_schema(manifest)
    return _GENERIC_SCHEMA
