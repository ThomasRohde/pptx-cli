from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.oxml.shapes.graphfrm import CT_GraphicalObjectFrame
from pptx.oxml.shapes.picture import CT_Picture
from pptx.shapes.placeholder import PlaceholderGraphicFrame, PlaceholderPicture
from pptx.util import Emu, Pt

from pptx_cli.core.io import load_json_or_yaml
from pptx_cli.core.manifest_store import template_copy_path
from pptx_cli.core.markdown import (
    ParsedParagraph,
    ParsedRun,
    looks_like_markdown,
    parse_markdown_paragraphs,
    parse_plain_text_paragraphs,
)
from pptx_cli.models.manifest import DeckSpec, LayoutContract, ManifestDocument, SlideSpec


class CompositionError(ValueError):
    code: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_IMAGE_FIT_ALIASES = {
    "contain": "fit",
    "cover": "cover",
    "crop": "cover",
    "fill": "cover",
    "fit": "fit",
}

_MARKDOWN_HEADING_SPACE_AFTER_PT = {
    1: 12.0,
    2: 10.0,
    3: 8.0,
}
_MARKDOWN_HEADING_SPACE_BEFORE_PT = 6.0
_MARKDOWN_BODY_SPACE_AFTER_PT = 6.0
_MARKDOWN_LIST_SPACE_AFTER_PT = 2.0
_MARKDOWN_BLOCK_SPACE_BEFORE_PT = 6.0


def plan_output_change(output_path: Path, *, overwrite: bool) -> dict[str, str]:
    if output_path.exists() and not overwrite:
        raise CompositionError(
            "ERR_CONFLICT_OUTPUT_EXISTS",
            f"Output already exists: {output_path}. Use --overwrite to replace it.",
        )
    operation = "replace" if output_path.exists() else "create"
    return {
        "target": str(output_path),
        "operation": operation,
        "artifact_type": "pptx",
    }


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


def save_presentation(prs: Any, output_path: Path, *, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise CompositionError(
            "ERR_CONFLICT_OUTPUT_EXISTS",
            f"Output already exists: {output_path}. Use --overwrite to replace it.",
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=output_path.suffix,
            dir=output_path.parent,
        ) as handle:
            temp_path = Path(handle.name)
        prs.save(str(temp_path))
        os.replace(temp_path, output_path)
    except PermissionError as exc:
        code = "ERR_CONFLICT_OUTPUT_EXISTS" if output_path.exists() else "ERR_IO_WRITE"
        if code == "ERR_CONFLICT_OUTPUT_EXISTS":
            message = f"Output file is in use or locked: {output_path}"
        else:
            message = f"Cannot write output file: {output_path}"
        raise CompositionError(code, message) from exc
    except OSError as exc:
        raise CompositionError("ERR_IO_WRITE", f"Cannot write output file: {output_path}") from exc
    finally:
        if temp_path is not None and temp_path.exists():
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
        _apply_image(shape, content)
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
        if looks_like_markdown(value):
            return {"kind": "markdown-text", "value": value}
        return {"kind": "text", "value": value}
    if isinstance(value, (int, float, bool)):
        return {"kind": "text", "value": str(value)}
    if isinstance(value, list):
        return {"kind": "markdown-text", "value": "\n".join(f"- {item}" for item in value)}
    raise CompositionError("ERR_VALIDATION_CONTENT_TYPE", f"Unsupported content payload: {value!r}")


def _apply_text(shape: Any, text: str, *, markdown: bool) -> None:
    text_frame = shape.text_frame
    text_frame.clear()
    paragraphs = parse_markdown_paragraphs(text) if markdown else parse_plain_text_paragraphs(text)

    previous: ParsedParagraph | None = None
    for index, parsed in enumerate(paragraphs):
        paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
        if parsed.level is not None:
            paragraph.level = parsed.level
        _write_paragraph_runs(paragraph, parsed)
        if markdown:
            _apply_markdown_paragraph_format(paragraph, parsed, previous, is_first=index == 0)
        previous = parsed


def _write_paragraph_runs(paragraph: Any, parsed: ParsedParagraph) -> None:
    first_run_spec = parsed.runs[0]
    paragraph.text = first_run_spec.text
    _apply_run_format(paragraph.runs[0], first_run_spec)

    for run_spec in parsed.runs[1:]:
        run = paragraph.add_run()
        run.text = run_spec.text
        _apply_run_format(run, run_spec)


def _apply_run_format(run: Any, parsed: ParsedRun) -> None:
    if parsed.bold:
        run.font.bold = True
    if parsed.italic:
        run.font.italic = True
    if parsed.code:
        run.font.name = "Courier New"


def _apply_markdown_paragraph_format(
    paragraph: Any,
    parsed: ParsedParagraph,
    previous: ParsedParagraph | None,
    *,
    is_first: bool,
) -> None:
    if parsed.kind == "heading":
        _apply_heading_runs(paragraph)
        if not is_first:
            paragraph.space_before = Pt(_MARKDOWN_HEADING_SPACE_BEFORE_PT)
        paragraph.space_after = Pt(
            _MARKDOWN_HEADING_SPACE_AFTER_PT.get(parsed.heading_level or 3, 8.0)
        )
        return

    if _starts_new_markdown_block(previous, parsed):
        paragraph.space_before = Pt(_MARKDOWN_BLOCK_SPACE_BEFORE_PT)

    if parsed.kind in {"bullet", "ordered"}:
        paragraph.space_after = Pt(_MARKDOWN_LIST_SPACE_AFTER_PT)
        return

    paragraph.space_after = Pt(_MARKDOWN_BODY_SPACE_AFTER_PT)


def _apply_heading_runs(paragraph: Any) -> None:
    for run in paragraph.runs:
        run.font.bold = True


def _starts_new_markdown_block(
    previous: ParsedParagraph | None,
    current: ParsedParagraph,
) -> bool:
    if previous is None:
        return False
    if current.kind in {"bullet", "ordered"}:
        return previous.kind != current.kind
    return previous.kind in {"bullet", "ordered"}


def _apply_image(shape: Any, content: dict[str, Any]) -> None:
    image_path = Path(str(content["path"]))
    if not image_path.exists():
        raise CompositionError("ERR_IO_NOT_FOUND", f"Image not found: {image_path}")

    placeholder_size = (int(shape.width), int(shape.height))
    image_fit = _normalize_image_fit(content.get("image_fit"))
    picture, image_size = _insert_placeholder_picture(shape, image_path)
    _apply_image_crop(picture, image_size, placeholder_size, image_fit)


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

    graphic_frame = _insert_placeholder_table(shape, row_count, col_count)
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
    _insert_placeholder_chart(shape, chart_type, chart_data)


def _normalize_image_fit(value: Any) -> str:
    if value is None:
        return "fit"
    if not isinstance(value, str):
        raise CompositionError(
            "ERR_VALIDATION_IMAGE_FIT",
            "image_fit must be one of: fit, contain, cover, fill, crop",
        )
    normalized = value.strip().lower()
    if normalized not in _IMAGE_FIT_ALIASES:
        raise CompositionError(
            "ERR_VALIDATION_IMAGE_FIT",
            "image_fit must be one of: fit, contain, cover, fill, crop",
        )
    return _IMAGE_FIT_ALIASES[normalized]


def _insert_placeholder_picture(
    shape: Any,
    image_path: Path,
) -> tuple[PlaceholderPicture, tuple[int, int]]:
    image_part, relationship_id = shape.part.get_or_add_image_part(str(image_path))
    image_size = image_part._px_size
    picture_element = CT_Picture.new_ph_pic(
        shape.shape_id,
        shape.name,
        image_part.desc,
        relationship_id,
    )
    shape._replace_placeholder_with(picture_element)
    return PlaceholderPicture(picture_element, shape._parent), image_size


def _insert_placeholder_table(shape: Any, rows: int, cols: int) -> PlaceholderGraphicFrame:
    graphic_frame = CT_GraphicalObjectFrame.new_table_graphicFrame(
        shape.shape_id,
        shape.name,
        rows,
        cols,
        shape.left,
        shape.top,
        shape.width,
        Emu(rows * 370840),
    )
    shape._replace_placeholder_with(graphic_frame)
    return PlaceholderGraphicFrame(graphic_frame, shape._parent)


def _insert_placeholder_chart(
    shape: Any,
    chart_type: XL_CHART_TYPE,
    chart_data: ChartData,
) -> PlaceholderGraphicFrame:
    relationship_id = shape.part.add_chart_part(chart_type, chart_data)
    graphic_frame = CT_GraphicalObjectFrame.new_chart_graphicFrame(
        shape.shape_id,
        shape.name,
        relationship_id,
        shape.left,
        shape.top,
        shape.width,
        shape.height,
    )
    shape._replace_placeholder_with(graphic_frame)
    return PlaceholderGraphicFrame(graphic_frame, shape._parent)


def _apply_image_crop(
    picture: PlaceholderPicture,
    image_size: tuple[int, int],
    placeholder_size: tuple[int, int],
    image_fit: str,
) -> None:
    if image_fit == "cover":
        picture._pic.crop_to_fit(image_size, placeholder_size)
        return

    image_width, image_height = image_size
    placeholder_width, placeholder_height = placeholder_size
    if image_width <= 0 or image_height <= 0:
        return
    if placeholder_width <= 0 or placeholder_height <= 0:
        return

    picture.crop_left = 0.0
    picture.crop_top = 0.0
    picture.crop_right = 0.0
    picture.crop_bottom = 0.0

    view_ratio = placeholder_width / placeholder_height
    image_ratio = image_width / image_height

    if image_ratio > view_ratio:
        padding = (image_ratio / view_ratio - 1.0) / 2.0
        picture.crop_top = -padding
        picture.crop_bottom = -padding
        return
    if image_ratio < view_ratio:
        padding = (view_ratio / image_ratio - 1.0) / 2.0
        picture.crop_left = -padding
        picture.crop_right = -padding
