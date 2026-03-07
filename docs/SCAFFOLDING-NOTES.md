# Scaffolding notes

## What was inferred from the PRD

- The project is a Python 3.12+ CLI, not a library-first package
- The public executable name is `pptx`
- The implementation package should avoid the `pptx` Python namespace due to `python-pptx`
- The project needs both human-readable docs and agent-readable operating guidance
- A thin runnable skeleton is appropriate; speculative business logic is not

## What was scaffolded

- Python project configuration (`pyproject.toml`, uv, Ruff, Pyright, pytest)
- `src/`-layout package scaffold under `src/pptx_cli/`
- thin Typer CLI with guide/init stubs and machine-envelope models
- core docs (`PROJECT.md`, `ARCHITECTURE.md`, `TESTING.md`, `CONTRIBUTING.md`, `SECURITY.md`)
- ADR and domain docs
- agent guidance and GitHub templates
- CI workflow and baseline repository hygiene files

## What still needs human input

- first sanitized `.pptx` fixtures for testing
- the first real manifest schema contents beyond the thin skeleton
- exact versioning policy for guide and manifest schema evolution

## Decisions captured after scaffolding

- PyPI is the intended public distribution channel
- the published package name is `pptx-cli`
- the installed console command remains `pptx`

## Highest-risk ambiguities

- chart/table fidelity edge cases once real templates are exercised
- Open XML edge cases not visible from the current sample material
- how wrapper CLIs should evolve after the thin Python scaffold phase
