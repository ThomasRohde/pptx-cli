from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from pptx_cli.core.versioning import read_version_from_init, write_version_to_init


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bump the project semantic version, commit it, and optionally push.",
    )
    parser.add_argument(
        "part",
        choices=["major", "minor", "patch"],
        help="Which semantic version segment to increment.",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Commit locally but do not push.",
    )
    return parser


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    init_file = repo_root / "src" / "pptx_cli" / "__init__.py"

    current = read_version_from_init(init_file)
    updated = current.bump(args.part)
    write_version_to_init(init_file, updated)

    print(f"{current} -> {updated}")

    _run(["git", "add", str(init_file)], cwd=repo_root)
    _run(["git", "commit", "-m", f"chore: bump version to {updated}"], cwd=repo_root)

    if not args.no_push:
        _run(["git", "push"], cwd=repo_root)
        print(f"Pushed {updated}. The publish workflow runs automatically on main/master.")
    else:
        print("Committed locally. Push with: git push")


if __name__ == "__main__":
    main()
