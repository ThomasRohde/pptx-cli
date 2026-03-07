from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_cli.core.manifest_store import load_manifest
from pptx_cli.core.validation import validate_deck


def validate_command(manifest_dir: Path, deck_path: Path, *, strict: bool) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    result = validate_deck(manifest_dir, manifest, deck_path, strict=strict)
    return result.model_dump(mode="json")
