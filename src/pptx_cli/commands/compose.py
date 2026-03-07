from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_cli.core.composition import (
    build_presentation,
    create_single_slide_spec,
    parse_set_arguments,
    plan_output_change,
    save_presentation,
)
from pptx_cli.core.manifest_store import load_deck_spec, load_effective_manifest


def slide_create(
    manifest_dir: Path,
    layout_id: str,
    set_values: list[str],
    output_path: Path,
    *,
    dry_run: bool,
    overwrite: bool,
) -> dict[str, Any]:
    manifest = load_effective_manifest(manifest_dir)
    content = parse_set_arguments(set_values)
    spec = create_single_slide_spec(layout_id, content)
    planned_changes = [plan_output_change(output_path, overwrite=overwrite)]
    if not dry_run:
        prs = build_presentation(manifest_dir, manifest, spec)
        save_presentation(prs, output_path, overwrite=overwrite)
    return {
        "dry_run": dry_run,
        "manifest": str(manifest_dir),
        "layout": layout_id,
        "out": str(output_path),
        "overwrite": overwrite,
        "changes": planned_changes,
        "summary": {"slides": 1, "artifacts": 1},
    }


def deck_build(
    manifest_dir: Path,
    spec_path: Path,
    output_path: Path,
    *,
    dry_run: bool,
    overwrite: bool,
) -> dict[str, Any]:
    manifest = load_effective_manifest(manifest_dir)
    spec = load_deck_spec(spec_path)
    planned_changes = [plan_output_change(output_path, overwrite=overwrite)]
    if not dry_run:
        prs = build_presentation(manifest_dir, manifest, spec)
        save_presentation(prs, output_path, overwrite=overwrite)
    return {
        "dry_run": dry_run,
        "manifest": str(manifest_dir),
        "spec": str(spec_path),
        "out": str(output_path),
        "overwrite": overwrite,
        "changes": planned_changes,
        "summary": {"slides": len(spec.slides), "artifacts": 1},
        "metadata": spec.metadata,
    }
