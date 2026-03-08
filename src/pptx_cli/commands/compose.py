from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_cli.core.composition import (
    CompositionError,
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
    notes: str | None,
    notes_file: Path | None,
    dry_run: bool,
    overwrite: bool,
) -> dict[str, Any]:
    manifest = load_effective_manifest(manifest_dir)
    content = parse_set_arguments(set_values)
    resolved_notes = _resolve_notes_input(notes, notes_file)
    spec = create_single_slide_spec(layout_id, content, notes=resolved_notes)
    notes_changes = _plan_notes_changes(spec)
    planned_changes = [plan_output_change(output_path, overwrite=overwrite), *notes_changes]
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
        "summary": {"slides": 1, "artifacts": 1, "notes_slides": len(notes_changes)},
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
    notes_changes = _plan_notes_changes(spec)
    planned_changes = [plan_output_change(output_path, overwrite=overwrite), *notes_changes]
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
        "summary": {
            "slides": len(spec.slides),
            "artifacts": 1,
            "notes_slides": len(notes_changes),
        },
        "metadata": spec.metadata,
    }


def _resolve_notes_input(notes: str | None, notes_file: Path | None) -> str | None:
    if notes is not None and notes_file is not None:
        raise CompositionError(
            "ERR_VALIDATION_INPUT",
            "Use either --notes or --notes-file, not both.",
        )
    if notes_file is None:
        return notes
    if not notes_file.exists():
        raise CompositionError(
            "ERR_IO_NOT_FOUND",
            f"Speaker notes file not found: {notes_file}",
        )
    return notes_file.read_text(encoding="utf-8")


def _plan_notes_changes(spec: Any) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for slide_index, slide in enumerate(spec.slides, start=1):
        if slide.notes is None:
            continue
        changes.append(
            {
                "target": f"slide[{slide_index}].notes",
                "operation": "create",
                "artifact_type": "speaker-notes",
                "text_length": len(slide.notes),
            }
        )
    return changes
