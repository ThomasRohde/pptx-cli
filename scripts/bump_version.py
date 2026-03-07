from __future__ import annotations

import argparse
from pathlib import Path

from pptx_cli.core.versioning import read_version_from_init, write_version_to_init


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bump the project semantic version in a single source of truth.",
    )
    parser.add_argument(
        "part",
        choices=["major", "minor", "patch"],
        help="Which semantic version segment to increment.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    init_file = repo_root / "src" / "pptx_cli" / "__init__.py"

    current = read_version_from_init(init_file)
    updated = current.bump(args.part)
    write_version_to_init(init_file, updated)

    print(f"{current} -> {updated}")


if __name__ == "__main__":
    main()
