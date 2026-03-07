# Project

## Problem statement

- Enterprise teams want AI-assisted deck generation, but they cannot accept visual drift from approved PowerPoint templates.
- Existing generation approaches recreate styling approximately instead of preserving masters, layouts, placeholders, and protected branding assets.
- The real need is template-bound composition with exact or policy-governed fidelity, exposed through a CLI that humans, CI systems, and coding agents can drive reliably.

## Target users

- Enterprise architects
- Strategy and consulting teams
- Corporate communications teams
- Internal platform teams building document-generation workflows
- AI coding agents and CI pipelines consuming structured CLI contracts

## Goals

- Preserve and reuse enterprise PowerPoint template structure 1:1 where supported
- Expose layouts and placeholders as machine-readable contracts
- Generate slides and decks deterministically from approved layouts
- Validate outputs against manifest rules and protected template fingerprints
- Provide an agent-first CLI contract with stable JSON envelopes, error codes, exit codes, and guide metadata

## Non-goals

- Generic PowerPoint editing outside template constraints
- Full support for every PowerPoint feature ever created
- Free-form prompt-to-finished-deck generation without explicit layout mapping
- MCP server delivery in v1
- Full advanced chart workbook fidelity in v1

## Scope boundaries

- v1 uses exactly one source `.pptx` per manifest package
- v1 supports text, image, table, chart, and markdown-to-text placeholders
- v1 preview support is metadata-only
- v1 wrapper generation outputs a Python package scaffold
- v1 targets the open-source backend only

## Constraints

- Must run on Windows, macOS, and Linux
- Must not require Microsoft PowerPoint to be installed
- Must preserve safe file-write semantics for generated outputs
- Must keep the public CLI executable name as `pptx`
- Must avoid Python package-name collision with `python-pptx`; implementation package should not be named `pptx`

## Assumptions

- Python 3.12+ is the primary delivery runtime
- The packaging/distribution name can remain `pptx-cli` while the executable is `pptx`
- PyPI is the primary public distribution channel for packaged releases
- Manifest inspection and validation are core to adoption, not optional niceties
- Agent automation depends on a stable guide + envelope contract from day one

## Success criteria

- Initialize manifests from enterprise templates
- Inspect layouts and placeholder contracts from the CLI
- Build slides/decks only from approved layouts
- Validate generated decks in local workflows and CI
- Provide machine-readable CLI behavior suitable for coding agents

## Open questions

- TODO: Decide the first sanitized sample template and fixture set for automated testing
  - Why it matters: Integration tests need stable real-world template coverage.
  - How to fill this in: Choose 1–3 representative templates with different layout complexity and sanitize proprietary content before committing.
  - Example: "Minimal corporate template", "dense consulting template", "communications cover-page template".
