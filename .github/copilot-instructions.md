# Copilot instructions

Use `AGENTS.md` as the canonical workspace guide. This file should only contain Copilot-specific reminders that supplement, rather than duplicate, the project-wide instructions.

## Copilot-specific reminders

- Follow existing patterns before introducing new abstractions
- Prefer updating `AGENTS.md` when the project-wide guidance changes
- Keep terminal and JSON output terse, deterministic, and easy for agents to parse

## Preferred patterns

- use typed models for shared contracts
- keep Typer command handlers thin
- put reusable logic in `src/pptx_cli/core/`
- keep machine-readable output stable and explicit
- prefer additive evolution over silent breaking changes

## Naming conventions

- CLI executable: `pptx`
- Python package: `pptx_cli`
- command IDs in machine-readable envelopes: dotted form like `guide.show`, `template.init`, or similar stable canonical names
- tests: `test_*.py`

## Testing expectations

- add or update tests with code changes
- validate command behavior and structured output for CLI changes
- preserve dry-run and safe-write semantics in tests for mutating commands

## Documentation expectations

- update docs in the same PR when commands, examples, or contracts change
- keep examples aligned with the current scaffold and command names
- leave guided `TODO:` blocks instead of guessing product decisions
