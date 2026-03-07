from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_VERSION_RE = re.compile(r'__version__\s*=\s*"(?P<version>\d+\.\d+\.\d+)"')


@dataclass(frozen=True, slots=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> SemVer:
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError(f"Invalid semantic version: {value}")
        return cls(*(int(part) for part in parts))

    def bump(self, part: str) -> SemVer:
        if part == "major":
            return SemVer(self.major + 1, 0, 0)
        if part == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if part == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        raise ValueError(f"Unsupported version part: {part}")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def read_version_from_init(init_file: Path) -> SemVer:
    contents = init_file.read_text(encoding="utf-8")
    match = _VERSION_RE.search(contents)
    if match is None:
        raise ValueError(f"Could not find __version__ in {init_file}")
    return SemVer.parse(match.group("version"))


def write_version_to_init(init_file: Path, version: SemVer) -> None:
    contents = init_file.read_text(encoding="utf-8")
    updated = _VERSION_RE.sub(f'__version__ = "{version}"', contents, count=1)
    init_file.write_text(updated, encoding="utf-8")
