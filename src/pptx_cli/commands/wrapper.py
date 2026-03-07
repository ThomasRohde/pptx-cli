from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx_cli.core.ids import slugify
from pptx_cli.core.io import atomic_write_text, ensure_directory
from pptx_cli.core.manifest_store import load_manifest


def wrapper_generate(manifest_dir: Path, output_dir: Path, *, dry_run: bool) -> dict[str, Any]:
    manifest = load_manifest(manifest_dir)
    package_name = f"{slugify(manifest.template.name).replace('-', '_')}_wrapper"
    cli_name = f"{slugify(manifest.template.name)}-pptx"
    files = {
        output_dir / "pyproject.toml": _pyproject(package_name, cli_name),
        output_dir / "README.md": _readme(cli_name),
        output_dir
        / "src"
        / package_name
        / "__init__.py": '"""Generated wrapper for pptx-cli."""\n',
        output_dir / "src" / package_name / "cli.py": _cli_module(package_name),
    }
    changes = [
        {
            "target": str(path),
            "operation": "replace" if path.exists() else "create",
            "artifact_type": "python-source" if path.suffix == ".py" else "project-file",
        }
        for path in files
    ]
    if not dry_run:
        for path, content in files.items():
            ensure_directory(path.parent)
            atomic_write_text(path, content)
    return {
        "dry_run": dry_run,
        "manifest": str(manifest_dir),
        "out": str(output_dir),
        "package_name": package_name,
        "cli_name": cli_name,
        "changes": changes,
        "summary": {"artifacts": len(files)},
    }


def _pyproject(package_name: str, cli_name: str) -> str:
    distribution_name = package_name.replace("_", "-")
    return (
        "[build-system]\n"
        'requires = ["hatchling>=1.27.0"]\n'
        'build-backend = "hatchling.build"\n\n'
        "[project]\n"
        f'name = "{distribution_name}"\n'
        'version = "0.1.0"\n'
        'description = "Generated wrapper for pptx-cli"\n'
        'requires-python = ">=3.12"\n'
        'dependencies = ["pptx-cli>=0.1.0", "typer>=0.15.1"]\n\n'
        "[project.scripts]\n"
        f'{cli_name} = "{package_name}.cli:main"\n\n'
        "[tool.hatch.build.targets.wheel]\n"
        f'packages = ["src/{package_name}"]\n'
    )


def _readme(cli_name: str) -> str:
    return (
        f"# {cli_name}\n\n"
        "Generated template wrapper for `pptx-cli`.\n\n"
        "This wrapper delegates to the shared engine and expects a colocated manifest "
        "package or a manually supplied path.\n"
    )


def _cli_module(package_name: str) -> str:
    return (
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n"
        "from typing import Annotated\n\n"
        "import typer\n\n"
        "from pptx_cli.cli import emit_json\n"
        "from pptx_cli.commands.compose import deck_build, slide_create\n"
        "from pptx_cli.commands.inspect import list_layouts\n"
        "from pptx_cli.commands.validate import validate_command\n"
        "from pptx_cli.core.runtime import build_runtime_context\n"
        "from pptx_cli.models.envelope import Envelope, Metrics\n\n"
        'app = typer.Typer(help="Generated wrapper CLI for a specific manifest package.")\n\n'
        "\n"
        "def _default_manifest() -> Path:\n"
        '    return Path(__file__).resolve().parents[2] / "manifest"\n\n'
        "\n"
        '@app.command("guide")\n'
        "def guide() -> None:\n"
        "    runtime = build_runtime_context()\n"
        "    envelope = Envelope(\n"
        "        request_id=runtime.request_id,\n"
        "        ok=True,\n"
        '        command="guide.show",\n'
        "        result={\n"
        '            "wrapper": True,\n'
        '            "commands": [\n'
        '                "layouts list",\n'
        '                "slide create",\n'
        '                "deck build",\n'
        '                "validate",\n'
        "            ],\n"
        '            "manifest": str(_default_manifest()),\n'
        "        },\n"
        "        warnings=[],\n"
        "        errors=[],\n"
        "        metrics=Metrics(duration_ms=runtime.duration_ms),\n"
        "    )\n"
        "    emit_json(envelope)\n\n"
        "\n"
        '@app.command("layouts-list")\n'
        "def layouts_list(\n"
        '    manifest: Annotated[Path, typer.Option("--manifest")] = _default_manifest(),\n'
        ") -> None:\n"
        "    runtime = build_runtime_context()\n"
        "    result = list_layouts(manifest)\n"
        "    envelope = Envelope(\n"
        "        request_id=runtime.request_id,\n"
        "        ok=True,\n"
        '        command="layouts.list",\n'
        "        result=result,\n"
        "        warnings=[],\n"
        "        errors=[],\n"
        "        metrics=Metrics(duration_ms=runtime.duration_ms),\n"
        "    )\n"
        "    emit_json(envelope)\n\n"
        "\n"
        '@app.command("slide-create")\n'
        "def slide_create_command(\n"
        '    layout: Annotated[str, typer.Option("--layout")],\n'
        '    out: Annotated[Path, typer.Option("--out")],\n'
        '    set_values: Annotated[list[str] | None, typer.Option("--set")] = None,\n'
        '    manifest: Annotated[Path, typer.Option("--manifest")] = _default_manifest(),\n'
        ") -> None:\n"
        "    runtime = build_runtime_context()\n"
        "    result = slide_create(manifest, layout, list(set_values or []), out, dry_run=False)\n"
        "    envelope = Envelope(\n"
        "        request_id=runtime.request_id,\n"
        "        ok=True,\n"
        '        command="slide.create",\n'
        "        result=result,\n"
        "        warnings=[],\n"
        "        errors=[],\n"
        "        metrics=Metrics(duration_ms=runtime.duration_ms),\n"
        "    )\n"
        "    emit_json(envelope)\n\n"
        "\n"
        '@app.command("deck-build")\n'
        "def deck_build_command(\n"
        '    spec: Annotated[Path, typer.Option("--spec")],\n'
        '    out: Annotated[Path, typer.Option("--out")],\n'
        '    manifest: Annotated[Path, typer.Option("--manifest")] = _default_manifest(),\n'
        ") -> None:\n"
        "    runtime = build_runtime_context()\n"
        "    result = deck_build(manifest, spec, out, dry_run=False)\n"
        "    envelope = Envelope(\n"
        "        request_id=runtime.request_id,\n"
        "        ok=True,\n"
        '        command="deck.build",\n'
        "        result=result,\n"
        "        warnings=[],\n"
        "        errors=[],\n"
        "        metrics=Metrics(duration_ms=runtime.duration_ms),\n"
        "    )\n"
        "    emit_json(envelope)\n\n"
        "\n"
        '@app.command("validate")\n'
        "def validate_command_wrapper(\n"
        '    deck: Annotated[Path, typer.Option("--deck")],\n'
        '    manifest: Annotated[Path, typer.Option("--manifest")] = _default_manifest(),\n'
        ") -> None:\n"
        "    runtime = build_runtime_context()\n"
        "    result = validate_command(manifest, deck, strict=False)\n"
        "    envelope = Envelope(\n"
        "        request_id=runtime.request_id,\n"
        '        ok=result["ok"],\n'
        '        command="validate.run",\n'
        "        result=result,\n"
        "        warnings=[],\n"
        "        errors=[],\n"
        "        metrics=Metrics(duration_ms=runtime.duration_ms),\n"
        "    )\n"
        "    emit_json(envelope)\n\n"
        "\n"
        "def main() -> None:\n"
        "    app()\n"
    )
