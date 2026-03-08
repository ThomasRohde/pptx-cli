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
# Generic (template-free) schema
# ---------------------------------------------------------------------------

_GENERIC_SCHEMA = """\
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
</slide-schema>

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
</content-rules>

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
</style-guide>
"""


# ---------------------------------------------------------------------------
# Template-enriched schema
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


def _build_template_section(manifest: ManifestDocument) -> str:
    """Return the template-specific portion of the reference doc."""
    layouts_ref: dict[str, Any] = {}
    examples: list[dict[str, Any]] = []

    for layout in manifest.layouts:
        layouts_ref[layout.id] = _layout_section(layout)
        examples.append(_example_slide(layout))

    doc: dict[str, Any] = {
        "template": manifest.template.name,
        "layouts": layouts_ref,
        "example_slides": examples,
    }
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_schema_document(template_dir: Path | None = None) -> str:
    """Return the full reference document as a string."""
    parts = [_GENERIC_SCHEMA]
    if template_dir is not None:
        manifest = load_effective_manifest(template_dir)
        parts.append("\n# ── Template-specific layouts ──────────────────────────────────\n")
        parts.append(_build_template_section(manifest))
    return "\n".join(parts)
