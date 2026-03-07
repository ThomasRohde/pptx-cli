from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE

from pptx_cli.core.io import load_json_or_yaml
from pptx_cli.core.manifest_store import template_copy_path
from pptx_cli.models.manifest import DeckSpec, LayoutContract, ManifestDocument, SlideSpec


class CompositionError(ValueError):
    code: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def resolve_layout(manifest: ManifestDocument, layout_id: str) -> LayoutContract:
    for layout in manifest.layouts:
        if layout.id == layout_id or layout.name == layout_id or layout_id in layout.aliases:
            return layout
    raise CompositionError("ERR_VALIDATION_LAYOUT_UNKNOWN", f"Unknown layout: {layout_id}")


def parse_set_arguments(items: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise CompositionError("ERR_VALIDATION_SET_FORMAT", f"Invalid --set entry: {item}")
        key, raw_value = item.split("=", 1)
        parsed[key] = _load_inline_or_file_value(raw_value)
    return parsed


def _load_inline_or_file_value(raw_value: str) -> Any:
    if raw_value.startswith("@"):
        path = Path(raw_value[1:])
        if not path.exists():
            raise CompositionError("ERR_IO_NOT_FOUND", f"Referenced content file not found: {path}")
        if path.suffix.lower() in {".json", ".yaml", ".yml"}:
            return load_json_or_yaml(path)
        if path.suffix.lower() in {".md", ".txt"}:
            kind = "markdown-text" if path.suffix.lower() == ".md" else "text"
            return {
                "kind": kind,
                "value": path.read_text(encoding="utf-8"),
            }
        return {"kind": "image", "path": str(path)}

    if raw_value.startswith("{") or raw_value.startswith("["):
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value
    return raw_value


def create_single_slide_spec(layout: str, content: dict[str, Any]) -> DeckSpec:
    return DeckSpec(slides=[SlideSpec(layout=layout, content=content)])


def build_presentation(manifest_dir: Path, manifest: ManifestDocument, spec: DeckSpec) -> Any:
    template_path = manifest_dir / manifest.template.stored_template_path
    if not template_path.exists():
        template_path = template_copy_path(manifest_dir)
    prs = Presentation(str(template_path))
    _remove_all_slides(prs)

    for slide_spec in spec.slides:
        layout_contract = resolve_layout(manifest, slide_spec.layout)
        slide_layout = prs.slide_layouts[layout_contract.source_layout_index]
        slide = prs.slides.add_slide(slide_layout)
        _populate_slide(slide, layout_contract, slide_spec.content)

    _apply_deck_metadata(prs, spec.metadata)
    return prs


def save_presentation(prs: Any, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=output_path.suffix,
        dir=output_path.parent,
    ) as handle:
        temp_path = Path(handle.name)
    try:
        prs.save(str(temp_path))
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _remove_all_slides(prs: Any) -> None:
    slide_id_list = list(prs.slides._sldIdLst)
    for slide_id in slide_id_list:
        relationship_id = slide_id.rId
        prs.part.drop_rel(relationship_id)
        prs.slides._sldIdLst.remove(slide_id)


def _apply_deck_metadata(prs: Any, metadata: dict[str, Any]) -> None:
    core_properties = prs.core_properties
    title = metadata.get("title")
    author = metadata.get("author")
    if isinstance(title, str):
        core_properties.title = title
    if isinstance(author, str):
        core_properties.author = author


def _populate_slide(slide: Any, layout: LayoutContract, content: dict[str, Any]) -> None:
    expected = {placeholder.logical_name: placeholder for placeholder in layout.placeholders}
    unknown_keys = sorted(set(content) - set(expected))
    if unknown_keys:
        raise CompositionError(
            "ERR_VALIDATION_PLACEHOLDER_UNKNOWN",
            f"Unknown placeholders for layout {layout.id}: {', '.join(unknown_keys)}",
        )

    missing_required = [
        name
        for name, placeholder in expected.items()
        if placeholder.required and name not in content
    ]
    if missing_required:
        raise CompositionError(
            "ERR_VALIDATION_PLACEHOLDER_REQUIRED",
            f"Missing required placeholders for layout {layout.id}: {', '.join(missing_required)}",
        )

    for key, value in content.items():
        placeholder = expected[key]
        shape = _find_slide_placeholder(slide, placeholder.placeholder_idx)
        if shape is None:
            raise CompositionError(
                "ERR_INTERNAL_PLACEHOLDER_MISSING",
                f"Placeholder {key} was not found on generated slide",
            )
        _apply_content_value(shape, placeholder.supported_content_types, value)


def _find_slide_placeholder(slide: Any, placeholder_idx: int) -> Any | None:
    for shape in slide.placeholders:
        if shape.placeholder_format.idx == placeholder_idx:
            return shape
    return None


def _apply_content_value(shape: Any, supported_types: list[str], value: Any) -> None:
    content = _normalize_content_value(value)
    kind = content["kind"]
    if kind not in supported_types:
        raise CompositionError(
            "ERR_VALIDATION_CONTENT_TYPE",
            f"Content type {kind!r} is not supported for this placeholder",
        )

    if kind in {"text", "markdown-text"}:
        _apply_text(shape, str(content["value"]), markdown=kind == "markdown-text")
        return
    if kind == "image":
        image_path = Path(str(content["path"]))
        if not image_path.exists():
            raise CompositionError("ERR_IO_NOT_FOUND", f"Image not found: {image_path}")
        shape.insert_picture(str(image_path))
        return
    if kind == "table":
        _apply_table(shape, content)
        return
    if kind == "chart":
        _apply_chart(shape, content)
        return

    raise CompositionError("ERR_VALIDATION_CONTENT_TYPE", f"Unsupported content type: {kind}")


def _normalize_content_value(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and "kind" in value:
        return value
    if isinstance(value, str):
        return {"kind": "text", "value": value}
    if isinstance(value, (int, float, bool)):
        return {"kind": "text", "value": str(value)}
    if isinstance(value, list):
        return {"kind": "markdown-text", "value": "\n".join(f"- {item}" for item in value)}
    raise CompositionError("ERR_VALIDATION_CONTENT_TYPE", f"Unsupported content payload: {value!r}")


def _apply_text(shape: Any, text: str, *, markdown: bool) -> None:
    value = _markdown_to_text(text) if markdown else text
    text_frame = shape.text_frame
    text_frame.clear()
    lines = value.splitlines() or [""]
    first_paragraph = text_frame.paragraphs[0]
    first_paragraph.text = lines[0]
    for line in lines[1:]:
        paragraph = text_frame.add_paragraph()
        paragraph.text = line


def _markdown_to_text(markdown: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        for prefix in ("# ", "## ", "### ", "- ", "* ", "> "):
            if line.startswith(prefix):
                line = line[len(prefix) :]
        cleaned_lines.append(line.replace("**", "").replace("__", "").replace("`", ""))
    return "\n".join(cleaned_lines).strip()


def _apply_table(shape: Any, content: dict[str, Any]) -> None:
    columns = content.get("columns", [])
    rows = content.get("rows", [])
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise CompositionError(
            "ERR_VALIDATION_TABLE_PAYLOAD",
            "Table payload requires 'columns' and 'rows' lists",
        )

    row_count = len(rows) + (1 if columns else 0)
    col_count = len(columns) if columns else (len(rows[0]) if rows else 0)
    if row_count <= 0 or col_count <= 0:
        raise CompositionError(
            "ERR_VALIDATION_TABLE_PAYLOAD",
            "Table payload must contain at least one row and one column",
        )

    graphic_frame = shape.insert_table(row_count, col_count)
    table = graphic_frame.table
    row_offset = 0
    if columns:
        for column_index, heading in enumerate(columns):
            table.cell(0, column_index).text = str(heading)
        row_offset = 1
    for row_index, row in enumerate(rows, start=row_offset):
        for column_index, cell in enumerate(row):
            table.cell(row_index, column_index).text = str(cell)


def _apply_chart(shape: Any, content: dict[str, Any]) -> None:
    chart_data = ChartData()
    categories = content.get("categories", [])
    series = content.get("series", [])
    chart_type_name = str(content.get("chart_type", "column_clustered")).upper()
    if not isinstance(categories, list) or not isinstance(series, list):
        raise CompositionError(
            "ERR_VALIDATION_CHART_PAYLOAD",
            "Chart payload requires 'categories' and 'series' lists",
        )

    chart_data.categories = categories
    for series_entry in series:
        if not isinstance(series_entry, dict):
            raise CompositionError(
                "ERR_VALIDATION_CHART_PAYLOAD",
                "Each chart series must be an object",
            )
        chart_data.add_series(
            str(series_entry.get("name", "Series")),
            series_entry.get("values", []),
        )

    if not hasattr(XL_CHART_TYPE, chart_type_name):
        raise CompositionError(
            "ERR_VALIDATION_CHART_PAYLOAD",
            f"Unsupported chart_type: {chart_type_name.lower()}",
        )
    chart_type = getattr(XL_CHART_TYPE, chart_type_name)
    shape.insert_chart(chart_type, chart_data)
