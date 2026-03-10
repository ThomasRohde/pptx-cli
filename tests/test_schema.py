from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from pptx_cli.cli import app
from pptx_cli.commands.schema import build_schema_document

runner = CliRunner()


def test_generic_schema_contains_deck_structure() -> None:
    text = build_schema_document()
    assert "<slide-schema>" in text
    assert "metadata:" in text
    assert "slides:" in text
    assert "title:" in text
    assert "body:" in text
    assert "notes:" in text


def test_generic_schema_documents_content_types() -> None:
    text = build_schema_document()
    assert "kind: image" in text
    assert "kind: table" in text
    assert "kind: chart" in text


def test_generic_schema_uses_xml_sections() -> None:
    text = build_schema_document()
    assert "<slide-schema>" in text
    assert "</slide-schema>" in text
    assert "<content-rules>" in text
    assert "</content-rules>" in text
    assert "<style-guide>" in text
    assert "</style-guide>" in text


def test_generic_schema_omits_layout() -> None:
    text = build_schema_document()
    assert "Do NOT include" in text
    assert "layout is assigned later" in text


def test_schema_command_outputs_text(tmp_path: str) -> None:
    result = runner.invoke(app, ["schema", "--no-template", "--no-copy"])
    assert result.exit_code == 0
    assert "metadata:" in result.stdout
    assert "slides:" in result.stdout


def test_schema_command_copies_to_clipboard() -> None:
    with patch("pptx_cli.cli.copy_to_clipboard", return_value=True) as mock_copy:
        result = runner.invoke(app, ["schema", "--no-template"])
    assert result.exit_code == 0
    mock_copy.assert_called_once()
    assert "copied to clipboard" in result.stderr


def test_schema_command_no_copy_skips_clipboard() -> None:
    with patch("pptx_cli.cli.copy_to_clipboard") as mock_copy:
        result = runner.invoke(app, ["schema", "--no-template", "--no-copy"])
    assert result.exit_code == 0
    mock_copy.assert_not_called()


def test_schema_with_template(template_path: str, manifest_dir: str) -> None:
    # First init a manifest so we can point --template at it
    init_result = runner.invoke(
        app,
        ["init", str(template_path), "--out", str(manifest_dir), "--format", "json"],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["schema", "--template", str(manifest_dir), "--no-copy"])
    assert result.exit_code == 0
    assert "<layouts>" in result.stdout
    assert "<deck-schema>" in result.stdout
    assert "layout:" in result.stdout
    assert "content:" in result.stdout


def test_template_schema_unified_sections(template_path: str, manifest_dir: str) -> None:
    init_result = runner.invoke(
        app,
        ["init", str(template_path), "--out", str(manifest_dir), "--format", "json"],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["schema", "--template", str(manifest_dir), "--no-copy"])
    assert result.exit_code == 0
    assert "<deck-schema>" in result.stdout
    assert "<layouts>" in result.stdout
    assert "<content-rules>" in result.stdout
    assert "<style-guide>" in result.stdout


def test_template_schema_has_layout_in_examples(template_path: str, manifest_dir: str) -> None:
    init_result = runner.invoke(
        app,
        ["init", str(template_path), "--out", str(manifest_dir), "--format", "json"],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["schema", "--template", str(manifest_dir), "--no-copy"])
    assert result.exit_code == 0
    assert "layout:" in result.stdout
    assert "content:" in result.stdout


def test_template_schema_no_generic_layout_warning(template_path: str, manifest_dir: str) -> None:
    init_result = runner.invoke(
        app,
        ["init", str(template_path), "--out", str(manifest_dir), "--format", "json"],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["schema", "--template", str(manifest_dir), "--no-copy"])
    assert result.exit_code == 0
    assert "Do NOT include" not in result.stdout


def test_no_template_flag_emits_generic() -> None:
    result = runner.invoke(app, ["schema", "--no-template", "--no-copy"])
    assert result.exit_code == 0
    assert "<slide-schema>" in result.stdout
    assert "Do NOT include" in result.stdout


def test_template_and_no_template_conflict() -> None:
    result = runner.invoke(app, ["schema", "--template", "some/dir", "--no-template", "--no-copy"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.stderr
