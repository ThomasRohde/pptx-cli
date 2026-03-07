from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_cli.core.manifest_store import write_manifest_package
from pptx_cli.core.template import (
    build_manifest_package,
    ensure_manifest_directories,
    plan_manifest_writes,
    write_fingerprints,
)


def plan_init(template: Path, output_dir: Path) -> dict[str, Any]:
    changes = plan_manifest_writes(template, output_dir)
    return {
        "template": str(template),
        "output_dir": str(output_dir),
        "changes": changes,
        "artifacts": [item["target"] for item in changes],
    }


def run_init(template: Path, output_dir: Path, *, dry_run: bool) -> dict[str, Any]:
    plan = plan_init(template, output_dir)
    if dry_run:
        return {
            "dry_run": True,
            "summary": {"total_outputs": len(plan["artifacts"])},
            "plan": plan,
        }

    ensure_manifest_directories(output_dir)
    manifest, annotations, init_report = build_manifest_package(template, output_dir)
    write_manifest_package(
        output_dir,
        manifest,
        annotations,
        init_report.model_dump(mode="json"),
    )
    write_fingerprints(output_dir, manifest)
    return {
        "dry_run": False,
        "summary": {
            "total_outputs": len(plan["artifacts"]),
            "layout_count": len(manifest.layouts),
            "asset_count": len(manifest.assets),
        },
        "plan": plan,
        "manifest": str(output_dir),
    }
