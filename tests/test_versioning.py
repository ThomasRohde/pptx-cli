from __future__ import annotations

from pathlib import Path

from pptx_cli.core.versioning import SemVer, read_version_from_init, write_version_to_init


def test_semver_bump_rules() -> None:
    assert str(SemVer.parse("1.2.3").bump("patch")) == "1.2.4"
    assert str(SemVer.parse("1.2.3").bump("minor")) == "1.3.0"
    assert str(SemVer.parse("1.2.3").bump("major")) == "2.0.0"


def test_read_and_write_version_round_trip(tmp_path: Path) -> None:
    init_file = tmp_path / "__init__.py"
    init_file.write_text('__version__ = "0.1.0"\n', encoding="utf-8")

    version = read_version_from_init(init_file)
    assert str(version) == "0.1.0"

    write_version_to_init(init_file, version.bump("minor"))
    assert init_file.read_text(encoding="utf-8") == '__version__ = "0.2.0"\n'
