from __future__ import annotations

from pptx_cli.models.envelope import GuideCommand, GuideDocument
from pptx_cli.models.manifest import DeckSpec, ManifestDocument, ValidationResult


def build_guide_document() -> GuideDocument:
    return GuideDocument(
        compatibility={
            "additive_changes": "minor",
            "breaking_changes": "major",
        },
        commands=[
            GuideCommand(
                id="guide.show",
                summary="Show the machine-readable CLI guide",
                mutates=False,
                examples=["pptx guide --format json"],
            ),
            GuideCommand(
                id="template.init",
                summary="Initialize a manifest package from a source template",
                mutates=True,
                output_schema={"$ref": "#/definitions/Envelope"},
                examples=["pptx init Template.pptx --out ./corp-template --dry-run"],
            ),
            GuideCommand(
                id="doctor.show",
                summary="Show manifest compatibility findings",
                mutates=False,
                examples=["pptx doctor --manifest ./corp-template --format json"],
            ),
            GuideCommand(
                id="layouts.list",
                summary="List available layouts from a manifest package",
                mutates=False,
                examples=["pptx layouts list --manifest ./corp-template --format json"],
            ),
            GuideCommand(
                id="layouts.show",
                summary="Show a single layout contract",
                mutates=False,
                examples=["pptx layouts show title-only --manifest ./corp-template --format json"],
            ),
            GuideCommand(
                id="placeholders.list",
                summary="List placeholders for a layout",
                mutates=False,
                examples=[
                    "pptx placeholders list title-only --manifest ./corp-template --format json"
                ],
            ),
            GuideCommand(
                id="theme.show",
                summary="Show theme metadata extracted into the manifest",
                mutates=False,
                examples=["pptx theme show --manifest ./corp-template --format json"],
            ),
            GuideCommand(
                id="assets.list",
                summary="List extracted assets from the manifest package",
                mutates=False,
                examples=["pptx assets list --manifest ./corp-template --format json"],
            ),
            GuideCommand(
                id="slide.create",
                summary="Create a slide from an approved layout",
                mutates=True,
                input_schema=DeckSpec.model_json_schema(),
                examples=[
                    "pptx slide create --manifest ./corp-template --layout title-only "
                    "--set title=Hello --out ./out/slide.pptx --dry-run"
                ],
            ),
            GuideCommand(
                id="deck.build",
                summary="Build a deck from a structured spec",
                mutates=True,
                input_schema=DeckSpec.model_json_schema(),
                examples=[
                    "pptx deck build --manifest ./corp-template --spec deck.yaml "
                    "--out ./out/deck.pptx --dry-run"
                ],
            ),
            GuideCommand(
                id="validate.run",
                summary="Validate a deck against a manifest package",
                mutates=False,
                output_schema=ValidationResult.model_json_schema(),
                examples=[
                    "pptx validate --manifest ./corp-template --deck ./out/deck.pptx "
                    "--strict --format json"
                ],
            ),
            GuideCommand(
                id="manifest.diff",
                summary="Compare two manifest packages and report additive vs. breaking changes",
                mutates=False,
                examples=["pptx manifest diff ./corp-template-v1 ./corp-template-v2 --format json"],
            ),
            GuideCommand(
                id="manifest.schema",
                summary="Emit the JSON schema for manifest.yaml",
                mutates=False,
                output_schema=ManifestDocument.model_json_schema(),
                examples=["pptx manifest schema --format json"],
            ),
            GuideCommand(
                id="wrapper.generate",
                summary="Generate a thin template-specific wrapper scaffold",
                mutates=True,
                examples=[
                    "pptx wrapper generate --manifest ./corp-template --out ./wrappers/acme "
                    "--dry-run"
                ],
            ),
        ],
        exit_codes={
            "success": 0,
            "validation_error": 10,
            "policy_error": 20,
            "conflict": 40,
            "io_error": 50,
            "internal_error": 90,
        },
        error_codes={
            "ERR_VALIDATION_LAYOUT_UNKNOWN": {"exit_code": 10, "retryable": False},
            "ERR_VALIDATION_PLACEHOLDER_UNKNOWN": {"exit_code": 10, "retryable": False},
            "ERR_VALIDATION_PLACEHOLDER_REQUIRED": {"exit_code": 10, "retryable": False},
            "ERR_VALIDATION_CONTENT_TYPE": {"exit_code": 10, "retryable": False},
            "ERR_IO_NOT_FOUND": {"exit_code": 50, "retryable": False},
            "ERR_CONFLICT_OUTPUT_EXISTS": {"exit_code": 40, "retryable": False},
            "ERR_INTERNAL_PLACEHOLDER_MISSING": {"exit_code": 90, "retryable": False},
        },
        identifier_conventions={
            "command_ids": (
                "canonical dotted identifiers like guide.show, layouts.list, or deck.build"
            ),
            "layout_ids": (
                "slugified manifest layout identifiers derived from template layout names"
            ),
            "placeholder_keys": (
                "logical placeholder keys such as title, subtitle, content_1, or picture"
            ),
            "manifest_path": "path to a manifest package directory containing manifest.yaml",
        },
        concurrency={
            "rule": (
                "Read commands can run in parallel; mutating commands writing the same "
                "output path must run sequentially."
            ),
            "safe_patterns": [
                "Run guide, layouts, theme, assets, and doctor commands in parallel",
                "Run deck.build and validate sequentially against the same output file",
            ],
        },
    )
