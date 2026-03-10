from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml

from pptx_cli import __version__
from pptx_cli.commands.compose import deck_build, slide_create
from pptx_cli.commands.guide import build_guide_document
from pptx_cli.commands.init import run_init
from pptx_cli.commands.inspect import (
    doctor,
    list_assets,
    list_layouts,
    list_placeholders,
    show_layout,
    show_theme,
)
from pptx_cli.commands.manifest_ops import manifest_diff, manifest_schema
from pptx_cli.commands.schema import build_schema_document, copy_to_clipboard
from pptx_cli.commands.validate import validate_command
from pptx_cli.commands.wrapper import wrapper_generate
from pptx_cli.core.composition import CompositionError
from pptx_cli.core.runtime import build_runtime_context, stdout_is_tty
from pptx_cli.core.validation import ValidationError
from pptx_cli.models.envelope import CliMessage, Envelope, Metrics

app = typer.Typer(
    help=(
        "Template-bound PowerPoint generation for enterprise decks. Supports text, "
        "images, tables, charts, markdown-text content in template-approved "
        "placeholders, and optional per-slide speaker notes."
    ),
    no_args_is_help=True,
)
layouts_app = typer.Typer(help="Inspect approved layouts from a manifest package.")
placeholders_app = typer.Typer(help="Inspect placeholders for a layout contract.")
theme_app = typer.Typer(help="Inspect extracted theme metadata.")
assets_app = typer.Typer(help="Inspect extracted asset references.")
slide_app = typer.Typer(help="Create slides from approved layouts.")
deck_app = typer.Typer(
    help=(
        "Build full decks from structured specs, including markdown-text content "
        "and optional per-slide speaker notes."
    )
)
manifest_app = typer.Typer(help="Work with manifest packages and schemas.")
wrapper_app = typer.Typer(help="Generate thin template-specific wrapper CLIs.")

app.add_typer(layouts_app, name="layouts")
app.add_typer(placeholders_app, name="placeholders")
app.add_typer(theme_app, name="theme")
app.add_typer(assets_app, name="assets")
app.add_typer(slide_app, name="slide")
app.add_typer(deck_app, name="deck")
app.add_typer(manifest_app, name="manifest")
app.add_typer(wrapper_app, name="wrapper")

FormatOption = Annotated[
    str | None,
    typer.Option("--format", help="Output format: json or text."),
]
DryRunOption = Annotated[
    bool,
    typer.Option("--dry-run", help="Preview changes without writing files."),
]
OverwriteOption = Annotated[
    bool,
    typer.Option(
        "--overwrite",
        "--force",
        help="Allow replacing an existing output file.",
    ),
]
ManifestOption = Annotated[
    Path,
    typer.Option("--manifest", help="Path to the manifest package directory."),
]

_EXIT_CODE_MAP = {
    "validation": 10,
    "policy": 20,
    "conflict": 40,
    "io": 50,
    "internal": 90,
}


def resolve_output_format(runtime: Any, explicit_format: str | None) -> str:
    if explicit_format is not None:
        return explicit_format
    if runtime.llm_mode or not stdout_is_tty():
        return "json"
    return "text"


def emit_json(envelope: Envelope) -> None:
    typer.echo(json.dumps(envelope.model_dump(mode="json", exclude_none=True), indent=2))


def emit_result(result: Any, envelope: Envelope, format: str) -> None:
    if format == "json":
        emit_json(envelope)
        return
    if format == "text":
        typer.echo(yaml.safe_dump(result, sort_keys=False, allow_unicode=True).rstrip())
        return
    raise typer.BadParameter("format must be 'json' or 'text'")


def _exit_code_for_error(error_code: str) -> int:
    if error_code.startswith("ERR_VALIDATION"):
        return _EXIT_CODE_MAP["validation"]
    if error_code.startswith("ERR_POLICY"):
        return _EXIT_CODE_MAP["policy"]
    if error_code.startswith("ERR_CONFLICT"):
        return _EXIT_CODE_MAP["conflict"]
    if error_code.startswith("ERR_IO"):
        return _EXIT_CODE_MAP["io"]
    return _EXIT_CODE_MAP["internal"]


def _message_for_error(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> CliMessage:
    if error_code.startswith("ERR_VALIDATION"):
        suggested_action = "fix_input"
    elif error_code.startswith("ERR_IO"):
        suggested_action = "retry"
    else:
        suggested_action = "escalate"
    retryable = error_code.startswith("ERR_IO")
    return CliMessage(
        code=error_code,
        message=message,
        retryable=retryable,
        suggested_action=suggested_action,
        details=details or {},
    )


def fail(
    command: str,
    runtime: Any,
    format: str,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    error = _message_for_error(error_code, message, details)
    envelope = Envelope(
        request_id=runtime.request_id,
        ok=False,
        command=command,
        result=None,
        warnings=[],
        errors=[error],
        metrics=Metrics(duration_ms=runtime.duration_ms),
    )
    emit_result(None, envelope, format)
    raise typer.Exit(code=_exit_code_for_error(error_code))


def success(
    command: str,
    runtime: Any,
    format: str,
    result: Any,
    *,
    warnings: list[CliMessage] | None = None,
) -> None:
    envelope = Envelope(
        request_id=runtime.request_id,
        ok=True,
        command=command,
        result=result,
        warnings=warnings or [],
        errors=[],
        metrics=Metrics(duration_ms=runtime.duration_ms),
    )
    emit_result(result, envelope, format)


def execute(command: str, format: str | None, func: Any) -> None:
    runtime = build_runtime_context()
    resolved_format = resolve_output_format(runtime, format)
    try:
        result = func()
    except typer.Exit:
        raise
    except CompositionError as exc:
        fail(command, runtime, resolved_format, exc.code, str(exc))
    except ValidationError as exc:
        fail(command, runtime, resolved_format, exc.code, str(exc))
    except FileNotFoundError as exc:
        fail(command, runtime, resolved_format, "ERR_IO_NOT_FOUND", str(exc))
    except PermissionError as exc:
        fail(command, runtime, resolved_format, "ERR_IO_WRITE", str(exc))
    except OSError as exc:
        fail(command, runtime, resolved_format, "ERR_IO_WRITE", str(exc))
    except ValueError as exc:
        fail(command, runtime, resolved_format, "ERR_VALIDATION_INPUT", str(exc))
    except Exception as exc:
        fail(command, runtime, resolved_format, "ERR_INTERNAL_UNHANDLED", str(exc))
    success(command, runtime, resolved_format, result)


def _version_callback(value: bool) -> None:
    if not value:
        return
    typer.echo(__version__)
    raise typer.Exit()


@app.callback()
def app_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed version and exit.",
        ),
    ] = False,
) -> None:
    """pptx CLI."""


@app.command("guide")
def guide(format: FormatOption = None) -> None:
    """Show the machine-readable CLI guide."""

    execute("guide.show", format, lambda: build_guide_document().model_dump(mode="json"))


@app.command("schema")
def schema_command(
    template: Annotated[
        Path | None,
        typer.Option("--template", help="Path to a manifest package directory."),
    ] = None,
    no_template: Annotated[
        bool,
        typer.Option("--no-template", help="Emit generic schema without template layouts."),
    ] = False,
    no_copy: Annotated[
        bool,
        typer.Option("--no-copy", help="Skip copying output to the clipboard."),
    ] = False,
) -> None:
    """Print the deck-spec YAML reference (for pasting into LLM prompts)."""
    if template is not None and no_template:
        typer.echo("Error: --template and --no-template are mutually exclusive.", err=True)
        raise typer.Exit(code=1)

    effective_template = template
    if not no_template and effective_template is None:
        # Auto-discover manifest in cwd
        for candidate in [Path("manifest.yaml"), Path("manifest/manifest.yaml")]:
            if candidate.exists():
                effective_template = candidate.parent
                break
        if effective_template is None:
            # Fall back to generic schema with a hint
            typer.echo(
                "Hint: use --template <dir> for a layout-aware schema, "
                "or --no-template for the generic version.",
                err=True,
            )

    if effective_template is not None and not (effective_template / "manifest.yaml").exists():
        typer.echo(
            f"Error: manifest not found at '{effective_template / 'manifest.yaml'}'.\n"
            f"Run 'pptx init <template.pptx> --out {effective_template}' first.",
            err=True,
        )
        raise typer.Exit(code=1)

    text = build_schema_document(effective_template)
    typer.echo(text)
    if not no_copy:
        if copy_to_clipboard(text):
            typer.echo("(copied to clipboard)", err=True)
        else:
            typer.echo("(clipboard copy failed – install xclip or pipe manually)", err=True)


@app.command("init")
def init_command(
    template: Annotated[Path, typer.Argument(help="Path to the source .pptx template")],
    out: Annotated[Path, typer.Option("--out", help="Output directory for the manifest package")],
    dry_run: DryRunOption = False,
    format: FormatOption = None,
) -> None:
    """Initialize a manifest package from a source template."""

    runtime = build_runtime_context()
    resolved_format = resolve_output_format(runtime, format)
    if not template.exists():
        fail(
            "template.init",
            runtime,
            resolved_format,
            "ERR_IO_NOT_FOUND",
            f"Template not found: {template}",
            {"template": str(template)},
        )
    if template.suffix.lower() != ".pptx":
        fail(
            "template.init",
            runtime,
            resolved_format,
            "ERR_VALIDATION_TEMPLATE_TYPE",
            "Template input must be a .pptx file",
            {"template": str(template)},
        )
    try:
        result = run_init(template, out, dry_run=dry_run)
    except OSError as exc:
        fail("template.init", runtime, resolved_format, "ERR_IO_WRITE", str(exc))
    except Exception as exc:
        fail("template.init", runtime, resolved_format, "ERR_INTERNAL_UNHANDLED", str(exc))
    success("template.init", runtime, resolved_format, result)


@app.command("doctor")
def doctor_command(manifest: ManifestOption, format: FormatOption = None) -> None:
    """Show compatibility findings for a manifest package."""

    execute("doctor.show", format, lambda: doctor(manifest))


@layouts_app.command("list")
def layouts_list(manifest: ManifestOption, format: FormatOption = None) -> None:
    """List available layouts from a manifest package."""

    execute("layouts.list", format, lambda: list_layouts(manifest))


@layouts_app.command("show")
def layouts_show(
    layout_id: Annotated[str, typer.Argument(help="Layout ID or source layout name")],
    manifest: ManifestOption,
    format: FormatOption = None,
) -> None:
    """Show a single layout contract."""

    execute("layouts.show", format, lambda: show_layout(manifest, layout_id))


@placeholders_app.command("list")
def placeholders_list_command(
    layout_id: Annotated[str, typer.Argument(help="Layout ID or source layout name")],
    manifest: ManifestOption,
    format: FormatOption = None,
) -> None:
    """List placeholders for a layout."""

    execute("placeholders.list", format, lambda: list_placeholders(manifest, layout_id))


@theme_app.command("show")
def theme_show(manifest: ManifestOption, format: FormatOption = None) -> None:
    """Show extracted theme metadata."""

    execute("theme.show", format, lambda: show_theme(manifest))


@assets_app.command("list")
def assets_list_command(manifest: ManifestOption, format: FormatOption = None) -> None:
    """List extracted assets."""

    execute("assets.list", format, lambda: list_assets(manifest))


@slide_app.command("create")
def slide_create_command(
    manifest: ManifestOption,
    layout: Annotated[str, typer.Option("--layout", help="Layout ID from the manifest")],
    out: Annotated[Path, typer.Option("--out", help="Output .pptx file")],
    set_values: Annotated[
        list[str] | None,
        typer.Option(
            "--set",
            help=(
                "Placeholder assignment like key=value, key=@file, or key=@notes.md "
                "for markdown-text."
            ),
        ),
    ] = None,
    notes: Annotated[
        str | None,
        typer.Option(
            "--notes",
            help="Speaker notes text for the slide. Markdown-looking multiline text is supported.",
        ),
    ] = None,
    notes_file: Annotated[
        Path | None,
        typer.Option(
            "--notes-file",
            help="Path to a UTF-8 text or markdown file to use as speaker notes.",
        ),
    ] = None,
    dry_run: DryRunOption = False,
    overwrite: OverwriteOption = False,
    format: FormatOption = None,
) -> None:
    """Create a deck containing a single slide from an approved layout.

    Use --set key=@notes.md or a multiline markdown-looking value to populate
    markdown-text placeholders with headings, lists, and inline emphasis.
    Use --notes or --notes-file for slide-level speaker notes.
    """

    execute(
        "slide.create",
        format,
        lambda: slide_create(
            manifest,
            layout,
            list(set_values or []),
            out,
            notes=notes,
            notes_file=notes_file,
            dry_run=dry_run,
            overwrite=overwrite,
        ),
    )


@deck_app.command("build")
def deck_build_command(
    manifest: ManifestOption,
    spec: Annotated[
        Path,
        typer.Option(
            "--spec",
            help=(
                "Path to the YAML or JSON deck spec. Use kind: markdown-text or multiline "
                "markdown strings for rich text content."
            ),
        ),
    ],
    out: Annotated[Path, typer.Option("--out", help="Output .pptx file")],
    dry_run: DryRunOption = False,
    overwrite: OverwriteOption = False,
    format: FormatOption = None,
) -> None:
    """Build a deck from a structured spec.

    Deck specs can provide markdown-text content explicitly or rely on multiline
    markdown-looking strings for headings, lists, and inline emphasis. Each slide
    may also provide an optional `notes` field for speaker notes.
    """

    execute(
        "deck.build",
        format,
        lambda: deck_build(
            manifest,
            spec,
            out,
            dry_run=dry_run,
            overwrite=overwrite,
        ),
    )


@app.command("validate")
def validate_deck_command(
    manifest: ManifestOption,
    deck: Annotated[Path, typer.Option("--deck", help="Path to the generated .pptx deck")],
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Escalate warnings into validation failures where applicable.",
        ),
    ] = False,
    format: FormatOption = None,
) -> None:
    """Validate a generated deck against the manifest contract."""

    execute("validate.run", format, lambda: validate_command(manifest, deck, strict=strict))


@manifest_app.command("diff")
def manifest_diff_command(
    left: Annotated[Path, typer.Argument(help="Left-hand manifest directory")],
    right: Annotated[Path, typer.Argument(help="Right-hand manifest directory")],
    format: FormatOption = None,
) -> None:
    """Compare two manifest packages."""

    execute("manifest.diff", format, lambda: manifest_diff(left, right))


@manifest_app.command("schema")
def manifest_schema_command(format: FormatOption = None) -> None:
    """Emit the JSON schema for manifest.yaml."""

    execute("manifest.schema", format, manifest_schema)


@wrapper_app.command("generate")
def wrapper_generate_command(
    manifest: ManifestOption,
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="Output directory for the generated wrapper package",
        ),
    ],
    dry_run: DryRunOption = False,
    format: FormatOption = None,
) -> None:
    """Generate a thin template-specific wrapper scaffold."""

    execute("wrapper.generate", format, lambda: wrapper_generate(manifest, out, dry_run=dry_run))


def main() -> None:
    app()
