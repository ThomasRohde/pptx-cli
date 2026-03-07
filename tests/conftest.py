from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMPLATE = ROOT / "Template.pptx"
SKIP_TEMPLATE_TESTS_ENV = "PPTX_SKIP_TEMPLATE_TESTS"
_TRUE_VALUES = {"1", "true", "yes", "on"}

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "template_integration: requires a local proprietary Template.pptx fixture",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    reason = _template_skip_reason()
    for item in items:
        fixture_names = getattr(item, "fixturenames", ())
        if "template_path" not in fixture_names:
            continue
        item.add_marker(pytest.mark.template_integration)
        if reason is not None:
            item.add_marker(pytest.mark.skip(reason=reason))


@pytest.fixture
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def template_path() -> Path:
    return TEMPLATE


@pytest.fixture
def manifest_dir(tmp_path: Path) -> Path:
    return tmp_path / "manifest"


def _template_skip_reason() -> str | None:
    if os.getenv(SKIP_TEMPLATE_TESTS_ENV, "").strip().lower() in _TRUE_VALUES:
        return (
            "Proprietary template integration tests skipped because "
            f"{SKIP_TEMPLATE_TESTS_ENV} is enabled."
        )
    if TEMPLATE.exists():
        return None
    return (
        "Proprietary template integration tests require a local Template.pptx "
        "fixture at the repository root."
    )
