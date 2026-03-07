from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_cli.core.manifest_store import load_annotations, load_manifest
from pptx_cli.core.validation import ValidationError


def doctor(manifest_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    report = manifest.compatibility_report.model_dump(mode="json")
    report["manifest"] = str(manifest_dir)
    return report


def list_layouts(manifest_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    annotations = load_annotations(manifest_dir)
    annotations_by_layout = {item.layout_id: item for item in annotations.layouts}
    return {
        "manifest": str(manifest_dir),
        "count": len(manifest.layouts),
        "layouts": [
            {
                "id": layout.id,
                "name": layout.name,
                "aliases": (
                    annotations_by_layout[layout.id].aliases
                    if layout.id in annotations_by_layout
                    else []
                ),
                "description": layout.description,
                "preview_path": layout.preview_path,
                "placeholder_count": len(layout.placeholders),
                "source_layout_index": layout.source_layout_index,
            }
            for layout in manifest.layouts
        ],
    }


def show_layout(manifest_dir: Path, layout_id: str) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    layout = next(
        (item for item in manifest.layouts if item.id == layout_id or item.name == layout_id),
        None,
    )
    if layout is None:
        raise ValidationError("ERR_VALIDATION_LAYOUT_UNKNOWN", f"Unknown layout: {layout_id}")
    return layout.model_dump(mode="json")


def list_placeholders(manifest_dir: Path, layout_id: str) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    layout = next(
        (item for item in manifest.layouts if item.id == layout_id or item.name == layout_id),
        None,
    )
    if layout is None:
        raise ValidationError("ERR_VALIDATION_LAYOUT_UNKNOWN", f"Unknown layout: {layout_id}")
    return {
        "layout_id": layout.id,
        "layout_name": layout.name,
        "placeholders": [item.model_dump(mode="json") for item in layout.placeholders],
    }


def show_theme(manifest_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    return manifest.presentation.get("theme", {})


def list_assets(manifest_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    return {
        "manifest": str(manifest_dir),
        "count": len(manifest.assets),
        "assets": [asset.model_dump(mode="json") for asset in manifest.assets],
    }
