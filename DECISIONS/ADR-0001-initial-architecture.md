# ADR-0001: Initial architecture scaffold

- **Status:** Accepted
- **Date:** 2026-03-07

## Context

The project is being scaffolded from `PRD.md` for a template-bound PowerPoint generation CLI. The PRD explicitly recommends Python 3.12+, a hybrid Open XML approach, Typer for CLI ergonomics, and an agent-first contract with stable machine-readable output.

The repository also needs to remain easy for both humans and coding agents to steer.

## Decision

We will scaffold the project as:

- a Python package named `pptx_cli`
- a public console script named `pptx`
- a `src/` layout
- a thin Typer CLI skeleton
- explicit documentation for architecture, testing, contribution, and agent behavior
- CI and quality tooling based on uv, Ruff, Pyright, and Pytest
- a single-source semantic versioning workflow suitable for major/minor/patch bumps

## Rationale

This shape aligns with the PRD while minimizing speculation.

A `src/` layout is conventional, test-friendly, and packaging-friendly. The `pptx_cli` package name avoids collision with the dependency namespace used by `python-pptx`. Typer provides a clean starting point for command composition, while Pydantic models will support the CLI envelope and guide contracts.

## Consequences

### Positive

- Immediate packaging and test structure
- Clear separation of CLI, models, and shared runtime helpers
- Low-friction path from scaffold to implementation
- Good compatibility with both human and agent-oriented workflows
- Clear path to publishing the package on PyPI as `pptx-cli`

### Negative

- Additional upfront documentation and contract files increase initial repo size
- Some implementation choices remain provisional until real template fixtures and manifest evolution are tested

## Provisional elements

The following remain intentionally provisional:

- exact manifest schema versioning policy
- first sanitized fixture set
- detailed chart/table implementation strategy beyond the v1 fidelity contract
