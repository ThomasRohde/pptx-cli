# AGENTS

## Project overview

`pptx` is a Python CLI for template-bound PowerPoint generation. It extracts a manifest from a real `.pptx` template, exposes layouts and placeholders as machine-readable contracts, and generates slides/decks inside that contract.

This repository is intentionally optimized for both humans and coding agents.

Use this file as the canonical workspace guide. Keep `.github/copilot-instructions.md` limited to Copilot-specific reminders so project rules stay in one place.

## Where to look first

1. `PRD.md` — product source of truth
2. `README.md` — user-facing CLI framing
3. `ARCHITECTURE.md` — implementation boundaries and package naming constraints
4. `src/pptx_cli/cli.py` — CLI entrypoint and command registration
5. `TESTING.md` — validation expectations
6. `CLI-MANIFEST.md` — machine-readable CLI contract rules
7. `src/pptx_cli/commands/` and `src/pptx_cli/models/` — current implementation patterns

## Authoritative files

- Product scope: `PRD.md`
- Architecture and trade-offs: `ARCHITECTURE.md`
- Contribution workflow: `CONTRIBUTING.md`
- Testing expectations: `TESTING.md`
- Repository-specific decisions: `DECISIONS/` and `/memories/repo/`

## Project structure

- `src/pptx_cli/cli.py` — Typer app, command routing, envelope emission
- `src/pptx_cli/commands/` — thin command orchestration
- `src/pptx_cli/core/` — reusable runtime, versioning, and future shared services
- `src/pptx_cli/models/` — typed shared contracts and schema-bearing models
- `tests/` — CLI contract, behavior, and future fixture-backed integration tests

## Coding rules

- Keep the public executable name as `pptx`
- Keep the Python package name as `pptx_cli`
- Do not introduce a Python package named `pptx`; it collides with `python-pptx`
- Keep stdout parseable in machine-readable mode
- Prefer typed models for shared contracts
- Keep command modules thin and move reusable logic into `core/`
- Preserve `--dry-run`, structured errors, and stable exit-code behavior

## Architectural invariants

- manifest facts and annotations are separate layers
- machine-readable responses use one stable envelope shape
- command discovery is available through `pptx guide`
- safe file-write semantics are required for mutating commands
- wrapper generation remains thin and delegates to the shared engine

## Build and test

Set up the development environment with:

```bash
uv sync --group dev
```

For code changes, run:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

For documentation-only changes, ensure examples, filenames, and command names still match the scaffold.

## Project-specific conventions

- Machine-readable envelopes use canonical dotted command IDs such as `guide.show` and `template.init`.
- `result` must always be present in machine-readable output; on failure it is `null`.
- Mutating commands must preserve `--dry-run` semantics and return structured change summaries.
- Additive changes are preferred over silent contract changes; do not rename error codes or exit-code categories casually.
- Use typed models for contracts before introducing ad hoc dictionaries that leak across modules.

## Key implementation landmarks

- `src/pptx_cli/cli.py` shows the expected command/envelope pattern.
- `src/pptx_cli/models/envelope.py` defines the stable response contract.
- `src/pptx_cli/commands/guide.py` is the reference read-only command.
- `src/pptx_cli/commands/init.py` currently contains scaffold-level planning logic; real manifest extraction should grow behind typed interfaces rather than inside the CLI entrypoint.
- `tests/test_cli.py` is the contract baseline for exit codes, envelopes, and machine-readable behavior.

## Project-specific gotchas

- Do not change CLI command names, response envelope fields, error-code taxonomy, or exit-code mapping without updating docs and tests in the same change.
- This scaffold currently proves the CLI contract more than the PowerPoint engine; avoid inventing high-confidence template behavior that the PRD does not guarantee.
- When functionality is still provisional, leave guided `TODO:` notes instead of speculative product decisions.

## What not to change casually

- CLI command names
- response envelope fields
- error-code taxonomy
- exit-code mapping
- manifest schema semantics
- package/import naming (`pptx_cli`)

## Handling ambiguity

If implementation details are unclear:

- use `PRD.md` first
- prefer small, reversible scaffolding choices
- leave guided `TODO:` markers instead of inventing product decisions
- document provisional assumptions in docs and ADRs

## When to stop and leave a TODO

Stop and leave a guided `TODO:` if:

- behavior would create a new product decision not present in `PRD.md`
- a schema or CLI contract change would be speculative
- a fixture or enterprise template assumption cannot be verified

## Expected output style

### Code

- typed
- small, composable modules
- minimal speculative business logic

### Docs

- concise but specific
- explicit about confirmed vs. inferred decisions
- examples should use `pptx`, not historical command names

### PRs

- include scope, rationale, verification, and any TODOs that remain
