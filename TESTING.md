# Testing

## Testing strategy

This project uses a layered testing approach:

1. **Unit tests** for CLI contract helpers, models, envelope formatting, and argument handling
2. **Command tests** for Typer command behavior and exit-code semantics
3. **Fixture-backed integration tests** for template initialization, manifest inspection, deck build, and validation flows
4. **Golden contract tests** for `guide` output, error codes, and machine-readable envelope stability

## Test pyramid

- many fast unit tests
- fewer command/integration tests
- a small number of end-to-end tests using sanitized `.pptx` fixtures

## Required commands

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

## Coverage expectations

- New command behavior should ship with tests
- Response envelope and error-code changes should always be covered by tests
- Core manifest and validation logic should favor deterministic fixture-based tests over ad hoc manual checks

## What every PR must test

- happy path for the changed behavior
- failure path with the expected error code or validation response
- machine-readable output shape if command behavior changes
- documentation updates when user-facing command semantics change

## AI-agent validation checklist

Before completing a change, agents should:

1. run targeted tests for the affected area
2. run `uv run pytest` if the change touches shared code or command routing
3. run Ruff and Pyright via `uv run` for code changes
4. verify docs when command names, output shapes, or examples change
5. avoid changing response-envelope semantics without updating guide and contract tests

## Fixture guidance

- Proprietary templates are not committed to the GitHub repository.
- Full fixture-backed integration tests run when a local untracked `Template.pptx` is available at the repository root.
- `tests/conftest.py` exposes shared pytest fixtures and skips proprietary-template integration tests automatically when that local fixture is missing.
- CI sets `PPTX_SKIP_TEMPLATE_TESTS=1` and runs the public test suite only.
- `tests/fixtures/templates/README.md` should document future sanitized fixtures if broader public integration coverage is added.
- Future fixture expansion should add additional sanitized `.pptx` files under `tests/fixtures/templates/` when broader scenario coverage is needed.

## Suggested near-term test modules

- `tests/test_cli.py`
- `tests/test_guide_command.py`
- `tests/test_envelope.py`
- `tests/test_init_command.py`
- `tests/test_validate_command.py`
