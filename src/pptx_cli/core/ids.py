from __future__ import annotations

import re

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    normalized = _SLUG_RE.sub("-", value.strip().lower()).strip("-")
    return normalized or "item"


def uniquify(candidate: str, existing: set[str]) -> str:
    if candidate not in existing:
        existing.add(candidate)
        return candidate

    index = 2
    while f"{candidate}-{index}" in existing:
        index += 1

    unique_value = f"{candidate}-{index}"
    existing.add(unique_value)
    return unique_value
