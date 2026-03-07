# Contributing

Thanks for contributing to `pptx`.

## Workflow

1. Create a focused branch from `main`
2. Make a small, coherent change
3. Update tests and docs with the code change
4. Run local validation before opening a pull request
5. Open a PR with scope, rationale, and verification notes

## Branch and PR expectations

- Prefer one topic per PR
- Keep PRs reviewable; large speculative refactors are discouraged
- Link related issues or design notes where available
- Call out any schema, manifest, or CLI contract changes explicitly

## Code style expectations

- Follow existing patterns before introducing new abstractions
- Prefer typed models over ad hoc dictionaries in shared code paths
- Keep command handlers thin; move reusable logic into `core/` or dedicated service modules
- Preserve deterministic behavior in machine-readable output
- Do not rename public CLI commands or stable error codes casually

## Commit expectations

- Use clear, imperative commit messages
- Keep unrelated cleanup out of feature commits
- Mention breaking changes explicitly when they occur

## Versioning

- The project follows semantic versioning
- Package version is sourced from `src/pptx_cli/__init__.py`
- Use the bump helper instead of editing version strings in multiple files

```bash
uv run python scripts/bump_version.py patch
uv run python scripts/bump_version.py minor
uv run python scripts/bump_version.py major
```

## Review checklist

Before requesting review, confirm:

- [ ] tests were added or updated
- [ ] docs reflect the change
- [ ] CLI examples still work conceptually
- [ ] machine-readable output remains stable or was intentionally versioned
- [ ] risky file-write behavior still supports dry-run and safe output handling

## Architectural changes

For non-trivial architectural changes:

- update `ARCHITECTURE.md`
- add or amend an ADR under `DECISIONS/`
- explain trade-offs and migration impact in the PR description

## Documentation expectations

Any change to the following must update docs in the same PR:

- public commands or flags
- envelope schema
- error codes / exit codes
- manifest schema
- deck spec semantics

## When to leave a TODO instead of guessing

If the PRD or existing docs do not provide enough information:

- leave a guided `TODO:` in the relevant file
- explain the gap in the PR description
- avoid speculative feature behavior disguised as finished implementation
