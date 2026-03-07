from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_cli.core.manifest_store import load_manifest
from pptx_cli.core.validation import diff_manifests
from pptx_cli.models.manifest import ManifestDocument


def manifest_diff(left_dir: Path, right_dir: Path) -> dict[str, Any]:
    left = load_manifest(left_dir)
    right = load_manifest(right_dir)
    diff = diff_manifests(left, right)
    return {
        "left": str(left_dir),
        "right": str(right_dir),
        **diff.model_dump(mode="json"),
    }


def manifest_schema() -> dict[str, Any]:
    return ManifestDocument.model_json_schema()
