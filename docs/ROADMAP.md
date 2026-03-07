# Roadmap

This roadmap distinguishes between **confirmed** scope from `PRD.md` and **inferred** implementation sequencing used for scaffolding.

## Milestone 1 — CLI contract and manifest foundation

### Confirmed

- manifest initialization from one source template
- manifest inspection commands
- machine-readable response envelope
- `guide` command
- stable error and exit-code contract

### Inferred workstreams

- envelope and guide models
- command routing skeleton
- initial manifest output writers
- basic compatibility reporting

## Milestone 2 — Layout-aware generation

### Confirmed

- slide creation from approved layouts
- deck build from structured specs
- v1 support for text/image/table/chart/markdown-to-text

### Inferred workstreams

- placeholder mapping services
- template cloning pipeline
- structured dry-run summaries

## Milestone 3 — Validation and CI readiness

### Confirmed

- validate command with machine-readable diagnostics
- manifest diff
- CI-suitable exit codes

### Inferred workstreams

- fingerprint comparison services
- golden contract tests
- sanitized template fixtures

## Milestone 4 — Governance and deeper enterprise support

### Confirmed

- preview generation after v1
- post-v1 MCP work
- broader enterprise policy and registry features

### Inferred workstreams

- richer layout metadata
- preview renderer evaluation
- release hardening and packaging automation

## Risks and dependencies

- sanitized real-world template fixtures are required for credible integration testing
- XML edge cases may force architectural refinement in manifest and composition layers
- distribution strategy is still partially open while the repository remains private
