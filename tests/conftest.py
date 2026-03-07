from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TEMPLATE = ROOT / "Template.pptx"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def template_path() -> Path:
    return TEMPLATE


@pytest.fixture
def manifest_dir(tmp_path: Path) -> Path:
    return tmp_path / "manifest"
