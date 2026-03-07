from __future__ import annotations

from pathlib import Path

import pptx_cli.core.io as io
import pptx_cli.models.manifest as manifest_models

MANIFEST_FILE = "manifest.yaml"
ANNOTATIONS_FILE = "annotations.yaml"
REPORT_FILE = "reports/init-report.json"
SCHEMA_FILE = "manifest.schema.json"
TEMPLATE_COPY_FILE = "assets/source-template.pptx"


def manifest_path(manifest_dir: Path) -> Path:
    return manifest_dir / MANIFEST_FILE


def annotations_path(manifest_dir: Path) -> Path:
    return manifest_dir / ANNOTATIONS_FILE


def report_path(manifest_dir: Path) -> Path:
    return manifest_dir / REPORT_FILE


def schema_path(manifest_dir: Path) -> Path:
    return manifest_dir / SCHEMA_FILE


def template_copy_path(manifest_dir: Path) -> Path:
    return manifest_dir / TEMPLATE_COPY_FILE


def load_manifest(manifest_dir: Path) -> manifest_models.ManifestDocument:
    payload = io.load_json_or_yaml(manifest_path(manifest_dir))
    return manifest_models.ManifestDocument.model_validate(payload)


def load_annotations(manifest_dir: Path) -> manifest_models.AnnotationsDocument:
    payload = io.load_json_or_yaml(annotations_path(manifest_dir))
    return manifest_models.AnnotationsDocument.model_validate(payload)


def load_deck_spec(spec_path: Path) -> manifest_models.DeckSpec:
    payload = io.load_json_or_yaml(spec_path)
    return manifest_models.DeckSpec.model_validate(payload)


def write_manifest_package(
    manifest_dir: Path,
    manifest: manifest_models.ManifestDocument,
    annotations: manifest_models.AnnotationsDocument,
    init_report: dict[str, object],
) -> None:
    io.write_yaml(manifest_path(manifest_dir), manifest.model_dump(mode="json", exclude_none=True))
    io.write_json(
        schema_path(manifest_dir),
        manifest_models.ManifestDocument.model_json_schema(),
    )
    io.write_yaml(
        annotations_path(manifest_dir),
        annotations.model_dump(mode="json", exclude_none=True),
    )
    io.write_json(report_path(manifest_dir), init_report)
