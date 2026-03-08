# PRD: PPTX CLI

## Working title

**PPTX CLI** — a template-initialized PowerPoint generation CLI that extracts a manifest from an enterprise PowerPoint file and then generates slides and decks that remain locked to the original corporate visual identity.

## 1. Executive summary

Current AI-driven slide generation usually fails at the exact point where enterprise users care most: corporate fidelity. Agents can generate plausible slides, but they often drift from the official template, misuse layouts, miss placeholder rules, flatten styling inconsistently, or recreate design elements approximately rather than exactly.

This product takes a different approach.

Instead of asking an agent to "make slides that look like the template," the CLI is initialized from an actual enterprise PowerPoint file. During initialization, it extracts a detailed manifest describing the presentation's structure and reusable assets: theme, masters, layouts, placeholders, text styles, geometry, static branding elements, image assets, slide size, and other layout constraints.

After initialization, all generation happens **against the extracted manifest and preserved template assets**, not against an inferred style description. The result is a CLI whose commands and options are aligned with the template itself, so a user or coding agent can say things like:

- create a title + two-column slide with this content
- create a section divider using the approved layout
- build a 6-slide deck using layouts A, B, C
- validate this generated deck against template version X

The core product thesis is simple:

**Do not reconstruct the corporate design. Preserve it, expose it, and generate inside its boundaries.**

## 2. Problem statement

Enterprise users increasingly want to use ChatGPT, Codex, GitHub Copilot, and other agents to generate PowerPoint decks. However, direct slide generation is unreliable when strict corporate visual identity (CVI) is required.

Common failure modes include:

- approximate rather than exact reproduction of theme colors, fonts, spacing, and slide composition
- incorrect or inconsistent use of slide layouts
- poor handling of placeholders, especially when layouts differ subtly
- static branding elements being moved, duplicated, or omitted
- fragile prompts that produce different results across runs
- generators creating slides that look fine visually but are not structurally aligned with the original template
- inability to guarantee compatibility across template versions
- no formal representation of the template that an agent can reason over

The real requirement is not "AI slide generation." The real requirement is:

**template-bound slide composition with exact enterprise fidelity, exposed through an agent-friendly CLI.**

## 3. Product vision

Create a CLI that turns a sample PowerPoint template into a reusable, versioned, machine-readable presentation specification.

That specification must be rich enough to support:

- deterministic slide generation
- AI-agent-friendly command usage
- strict reuse of enterprise masters and layouts
- exact placement of content into approved placeholders
- validation of output against the source template
- future evolution as the enterprise template changes

The product should feel like a compiler toolchain for enterprise presentations:

- **init**: compile a PowerPoint template into a manifest package
- **inspect**: expose layouts, placeholders, assets, and rules
- **compose**: create slides and decks from approved layouts
- **validate**: check whether a deck conforms to the template contract
- **diff**: compare template versions and detect breaking changes

## 4. Goals

### Primary goals

1. Enable 1:1 reuse of enterprise PowerPoint CVI by preserving original template assets and structure.
2. Provide a manifest-driven CLI interface that can be used reliably by humans and AI coding agents.
3. Support deterministic generation of slides and decks from approved layouts.
4. Make template rules explicit, inspectable, and versionable.
5. Reduce prompt fragility by moving presentation rules out of prompts and into a machine-readable contract.

### Secondary goals

1. Make it easy to upgrade to a new enterprise template version.
2. Support automated validation in CI.
3. Support downstream generation from structured content such as JSON, YAML, Markdown frontmatter, or LLM output.
4. Support reusable deck recipes and slide composition workflows.
5. Support a thin template-specific wrapper CLI generated from a manifest package for teams that want a dedicated executable surface.

## 5. Non-goals

The first release should **not** attempt to solve all PowerPoint automation problems.

Out of scope for v1:

- arbitrary editing of any existing presentation without template constraints
- perfect round-tripping of every PowerPoint feature ever created
- full support for advanced animations, transitions, embedded video, VBA, SmartArt rewriting, or highly custom chart internals beyond the supported v1 placeholder contract
- converting free-form natural language directly into a finished deck without an explicit layout/content mapping step
- redesigning or normalizing a poor-quality source template
- support for every office format besides `.pptx`
- shipping an MCP server in v1

The CLI should be opinionated: it exists to generate slides that conform to a known enterprise template, not to be a generic PowerPoint editor.

## 6. Key product principles

### 6.1 Preserve, don’t imitate

The engine should preferentially preserve and clone template assets from the original `.pptx` rather than restyle content from scratch.

### 6.2 Layouts are contracts

Each approved slide layout is a typed contract with named placeholders, geometry, allowed content types, and optional rules.

### 6.3 Manifest is the source of truth

The extracted manifest is the contract between the template and the generator. Humans and agents should inspect the same contract.

### 6.4 Deterministic first

Given the same manifest, content payload, and CLI version, output should be reproducible.

### 6.5 Validate everything

Every generated deck should be optionally validated against the manifest and original template fingerprints.

### 6.6 Agent-friendly by design

Commands, flags, schemas, and outputs should be explicit, typed, discoverable, and stable.

### 6.7 CLI behaves like an API

The CLI should expose a machine-readable contract with a stable response envelope, structured errors, documented exit codes, and a built-in guide command so agents can drive it zero-shot without scraping prose.

## 7. Users and personas

### Primary users

- enterprise architects
- strategy teams
- consulting teams inside large organizations
- corporate communications teams with strict branding requirements
- internal platform teams building document-generation workflows

### Secondary users

- AI coding agents such as Codex, GitHub Copilot, Claude Code, Gemini CLI, or internal orchestration agents
- CI/CD pipelines producing decks from structured data
- Power users who want reproducible deck generation from scripts

## 8. User stories

### Initialization

- As a user, I want to point the CLI at a corporate PowerPoint file and initialize a manifest package from it.
- As a user, I want the tool to detect available masters, layouts, placeholders, and theme assets.
- As a user, I want the tool to warn me when the template contains unsupported constructs that could break exact rendering.

### Inspection

- As a user, I want to list all approved layouts and see their names, purposes, placeholders, and preview metadata.
- As a user, I want to inspect the placeholder schema of a layout before generating slides.
- As an AI agent, I want machine-readable layout metadata so I can choose the right layout programmatically.

### Composition

- As a user, I want to create a slide using an approved layout and fill only the approved placeholders.
- As a user, I want to create a deck from a YAML or JSON spec referencing approved layouts.
- As an AI agent, I want a stable CLI command surface that maps directly to layout contracts.

### Validation and governance

- As a user, I want to validate that a generated deck conforms to the original template contract.
- As a platform owner, I want to track template versions and detect when a new template changes a layout or placeholder contract.
- As a CI pipeline, I want a non-zero exit code if generated output violates layout or branding rules.

## 9. Product scope

The product has five major capabilities.

### 9.1 Template initialization

Input:

- exactly one source `.pptx` file per manifest package in v1
- optional metadata such as organization, business unit, template name, version, locale, and owner

Output:

- manifest package directory, for example:

```text
my-template/
  manifest.yaml
  manifest.schema.json
  annotations.yaml
  assets/
    images/
    media/
    embedded/
  previews/
    layouts/
  fingerprints/
    parts.json
  reports/
    init-report.json
```

The init step must:

- unpack and inspect the PresentationML package
- extract presentation size and document properties
- identify slide masters, layouts, themes, placeholders, text styles, and static graphical elements
- assign stable IDs to layouts and placeholders
- emit a separate `annotations.yaml` file for optional human-authored annotations on top of extracted layout metadata, for example semantic purpose, usage notes, and aliases
- preserve references to original masters, layouts, and related assets
- compute fingerprints for important XML parts and assets
- emit warnings for unsupported or risky constructs

### 9.2 Manifest inspection

The CLI must let users inspect the manifest.

Examples:

```bash
pptx layouts list --manifest ./my-template
pptx layouts show executive-two-column --manifest ./my-template
pptx placeholders list executive-two-column --manifest ./my-template
pptx theme show --manifest ./my-template
pptx doctor --manifest ./my-template
```

Expected inspection output:

- human-readable terminal views
- JSON/YAML machine-readable output modes
- preview metadata in v1, with a single canonical future preview path field per layout and rendering support deferred to a later phase

### 9.3 Slide and deck composition

The CLI must support two modes:

1. **direct composition commands**
2. **spec-driven composition**

Examples:

```bash
pptx slide create \
  --manifest ./my-template \
  --layout executive-two-column \
  --set title="Enterprise AI Operating Model" \
  --set left_body=@left.md \
  --set right_body=@right.md \
  --notes-file speaker-notes.md \
  --out slide.pptx
```

```bash
pptx deck build \
  --manifest ./my-template \
  --spec deck.yaml \
  --out operating-model.pptx
```

Composition rules:

- only approved layouts can be used
- only declared placeholders can be filled
- content types must match placeholder types
- v1 supported placeholder content types are text, images, tables, charts, and markdown-to-text mappings
- speaker notes are optional per-slide metadata, not placeholder content types, and may use the same markdown-to-text formatting pipeline
- v1 tables and charts preserve approved placeholder geometry and accept structured data population, but do not guarantee full preservation of advanced workbook internals or highly custom styling behaviors
- static brand elements remain untouched unless explicitly marked overridable
- theme and master dependencies must be preserved
- output should open in PowerPoint without repair prompts

### 9.4 Validation

The CLI must provide both structural and visual-fidelity validation.

Structural validation checks:

- correct master/layout usage
- placeholder mapping correctness
- required placeholder presence
- unsupported object insertion
- broken relationships or missing assets
- schema compliance of deck spec inputs

Fidelity validation checks:

- retained theme references
- expected slide size and orientation
- unchanged static elements where required
- geometry tolerances for placeholders and locked objects
- fingerprint comparison for protected template components

Example:

```bash
pptx validate \
  --manifest ./my-template \
  --deck operating-model.pptx
```

### 9.5 Template versioning and diff

The CLI should allow comparison of manifest versions.

Example:

```bash
pptx manifest diff ./template-v1 ./template-v2
```

Diff categories:

- added or removed layouts
- placeholder contract changes
- renamed layout aliases
- theme changes
- font changes
- geometry changes
- asset changes
- potentially breaking changes vs. additive changes

## 10. Functional requirements

### FR-1: Initialize from sample PowerPoint

The system shall initialize a manifest package from exactly one source `.pptx` file in v1.

### FR-2: Extract presentation structure

The system shall extract presentation-level metadata including slide size, master list, layout list, theme references, and asset relationships.

### FR-3: Extract layout contracts

The system shall create a typed representation of each layout, including:

- layout ID
- layout name
- source master
- placeholder list
- placeholder IDs and indices
- geometry
- content type expectations
- default text style metadata where available
- protected static elements

### FR-4: Preserve static template components

The system shall preserve or clone original master/layout/static elements rather than recreating them from abstract styling rules whenever possible.

### FR-5: Generate command surface from manifest

The system shall expose layout-aware commands and/or options derived from the manifest.

This may include:

- layout names as validated arguments
- placeholder names as allowed keys for `--set`
- schema export for external tooling
- completion scripts generated from the manifest

### FR-6: Create slide from approved layout

The system shall create a new slide from an approved layout and populate placeholders from provided content.

### FR-7: Create deck from spec

The system shall create a deck from a structured spec file containing ordered slide definitions.

### FR-8: Support multiple content sources

The system shall accept inline strings, files, structured JSON/YAML, and markdown content as input sources for placeholders.

The v1 supported placeholder content types shall include:

- text
- image
- table
- chart
- markdown-to-text

The system shall also support optional per-slide speaker notes supplied either
through the structured deck spec or dedicated direct-command inputs. These notes
are slide metadata rather than placeholders and reuse the markdown-to-text
formatting pipeline for rich presenter text.

### FR-9: Validate output

The system shall validate output decks against the manifest and return machine-friendly errors.

### FR-10: Report unsupported template features

The system shall emit a compatibility report during initialization describing unsupported or risky template constructs.

### FR-11: Version and diff manifests

The system shall version manifest packages and identify breaking vs. non-breaking template changes.

### FR-12: Export machine-readable schemas

The system shall export JSON Schema and/or OpenAPI-like command metadata for integration with agents, MCP servers, or downstream tooling.

### FR-13: Support manifest annotations

The system shall support editable manifest annotations for layout semantics, intended usage, aliases, and operator notes without mutating the extracted source facts.

The v1 storage model for these annotations shall be a separate `annotations.yaml` file layered on top of `manifest.yaml`.

### FR-14: Generate wrapper CLI

The system shall support generation of a thin template-specific wrapper CLI from a manifest package, while keeping the main dynamic `pptx` executable as the primary interface.

The v1 wrapper output shall be a Python package scaffold that exposes template-specific commands and delegates to the shared core engine.

### FR-15: Return a structured response envelope

The system shall support a structured response envelope for every command in machine-readable mode.

The envelope shall include, at minimum:

- `schema_version`
- `request_id`
- `ok`
- `command`
- `result`
- `warnings`
- `errors`
- `metrics`

On failure, `result` shall be `null` rather than omitted.

### FR-16: Emit machine-readable errors and stable exit codes

The system shall emit structured errors with stable machine-readable error codes, human-readable messages, and optional structured details.

The system shall define and document stable exit code categories so CI pipelines and agents can distinguish validation errors, permission or policy failures, conflicts, I/O failures, and internal errors without parsing prose.

### FR-17: Provide a machine-readable guide command

The system shall provide a `guide` command that returns the CLI command catalog, input and output schema references, error code taxonomy, exit-code mapping, identifier conventions, and representative examples.

### FR-18: Support dry-run for mutating commands

The system shall support `--dry-run` on mutating commands that create or modify on-disk artifacts, including template initialization, slide creation, deck build, and wrapper generation.

Dry-run responses shall include a structured change summary describing the outputs that would be created or modified.

### FR-19: Return change records for writes

The system shall return structured change records for mutating commands, including the target artifact, operation type, and resulting output metadata.

Where meaningful, change records should include before/after or create/replace semantics.

### FR-20: Use safe file-write semantics

The system shall write generated artifacts using safe file-write semantics, including temporary-file staging and atomic replacement where the operating system and output type allow it.

### FR-21: Support agent-oriented output controls

The system shall support agent-oriented output behavior including:

- JSON output intended for machine parsing on stdout
- progress and diagnostics on stderr
- minimal-output behavior when `LLM=true` is set
- deterministic precedence of explicit flags over environment variables over TTY defaults

## 11. Non-functional requirements

### Determinism

Given the same inputs, output should be stable and reproducible.

### Fidelity

The system should maximize fidelity to the original template by retaining source masters, layouts, theme references, and approved geometry.

### Transparency

All extracted assumptions, warnings, and unsupported features must be visible to the user.

All machine-readable responses should expose warnings and errors in structured form without forcing agents to parse terminal prose.

### Portability

The CLI should run on Windows, macOS, and Linux without requiring Microsoft PowerPoint to be installed.

### Performance

Initialization should complete fast enough for normal enterprise template sizes. Deck generation should be suitable for interactive use and CI.

### Safety

The tool should never silently degrade fidelity. When exact preservation is not possible, it should warn or fail according to policy.

The default policy mode in v1 should be **warn mode**, with `--strict` available for CI and governance workflows.

Mutating commands should support preview-first workflows via `--dry-run` and should avoid destructive in-place writes when safe replacement is possible.

### Observability

Machine-readable responses should include basic execution metrics such as duration and, where relevant, counts of generated or validated artifacts.

### Extensibility

The manifest schema and plugin model should support future capabilities such as charts, icons, tables, or enterprise-specific rules.

## 12. Proposed CLI design

## 12.1 Top-level commands

```text
pptx guide
pptx init
pptx doctor
pptx layouts list
pptx layouts show
pptx placeholders list
pptx theme show
pptx assets list
pptx slide create
pptx deck build
pptx validate
pptx manifest diff
pptx manifest schema
pptx completions generate
```

## 12.2 Response and output contract

The CLI should support a machine-readable mode whose stdout always returns a single structured JSON envelope.

Recommended envelope shape:

```json
{
  "schema_version": "1.0",
  "request_id": "req_20260307_120000_abcd",
  "ok": true,
  "command": "layouts.list",
  "result": {},
  "warnings": [],
  "errors": [],
  "metrics": {
    "duration_ms": 42
  }
}
```

Output rules:

- stdout is reserved for the structured response in machine-readable mode
- stderr is used for progress, warnings, and diagnostics intended for humans
- success output should be terse and factual
- failure output should be rich in structured diagnostics
- `errors` and `warnings` are always arrays
- `result` is always present

The CLI should default to minimal non-decorative output when `LLM=true` is set, while preserving the same command semantics and safety checks.

## 12.3 Dynamic manifest-aligned behavior

The CLI should not necessarily generate a brand-new executable per template. Instead, it should behave as a dynamic template-aware CLI whose validated arguments and completions come from the manifest.

Examples:

- `pptx slide create --layout executive-two-column`
- placeholder keys validated against that layout contract
- shell completions showing available layouts and placeholders
- generated help text enriched with layout descriptions from the manifest

Optional future mode:

- `pptx wrapper generate` generates a thin wrapper CLI for a specific template package in v1

In v1, this command should generate a Python package scaffold rather than a shell-only wrapper or multi-target bundle.

## 12.4 Guide and compatibility contract

The `pptx guide` command should expose a machine-readable description of:

- top-level commands and subcommands
- input and output schema references
- supported flags and options
- error-code taxonomy
- exit-code mapping
- identifier and reference conventions, for example manifest paths, layout IDs, placeholder keys, and asset references
- compatibility policy for additive vs. breaking schema changes
- representative examples for common workflows

The CLI should version its machine-readable schema contract explicitly so agents can detect and adapt to breaking changes.

## 12.5 Example commands

### Initialize template

```bash
pptx init enterprise-template.pptx --out ./corp-template
```

### Discover CLI contract

```bash
pptx guide --format json
```

### List layouts

```bash
pptx layouts list --manifest ./corp-template --format json
```

### Show layout contract

```bash
pptx layouts show executive-summary --manifest ./corp-template
```

### Create slide from layout

```bash
pptx slide create \
  --manifest ./corp-template \
  --layout executive-summary \
  --set title="Target State Architecture" \
  --set subtitle="Q2 2026" \
  --set body=@body.md \
  --out summary-slide.pptx
```

### Build full deck

```bash
pptx deck build \
  --manifest ./corp-template \
  --spec ./deck.yaml \
  --out target-state-architecture.pptx
```

### Validate output

```bash
pptx validate \
  --manifest ./corp-template \
  --deck ./target-state-architecture.pptx \
  --strict
```

### Preview a write without modifying files

```bash
pptx deck build \
  --manifest ./corp-template \
  --spec ./deck.yaml \
  --out target-state-architecture.pptx \
  --dry-run
```

## 13. Deck spec design

The product should support a structured deck spec.

Example:

```yaml
manifest: ./corp-template
metadata:
  title: Enterprise AI Operating Model
  author: Thomas Rohde
  template_version: 1.2.0
slides:
  - layout: title-slide
    content:
      title: Enterprise AI Operating Model
      subtitle: March 2026
  - layout: section-divider
    content:
      title: Why this change
    notes: |
      - Pause before the transition
      - Re-anchor the audience on governance and brand fidelity
  - layout: executive-two-column
    content:
      title: Core idea
      left_body: |
        Preserve the template.
        Generate inside its rules.
      right_body: |
        Expose layouts and placeholders
        as a machine-readable contract.
```

The CLI should validate this spec against both a deck-spec schema and the template manifest.

For mutating workflows, the system should also be able to emit a structured build summary describing which slides, assets, and output artifacts would be created.

## 14. Manifest schema requirements

The manifest should be human-readable and machine-validated.

Recommended primary format:

- `manifest.yaml` for readability
- `manifest.schema.json` for validation

### Minimum manifest sections

```yaml
manifest_version: 1
template:
  name: Corporate Enterprise Template
  source_file: enterprise-template.pptx
  source_hash: sha256:...
  extracted_at: 2026-03-06T10:00:00Z
presentation:
  page_size:
    width_emu: 12192000
    height_emu: 6858000
  theme:
    name: Corporate Theme
    colors: {}
    fonts: {}
    effects: {}
masters: []
layouts: []
assets: []
rules: {}
capabilities: {}
compatibility_report: {}
fingerprints: {}
```

Companion annotations file for v1:

```yaml
template_annotations:
  semantic_tags: []
layouts: []
```

### Layout contract model

Each layout should include:

- stable ID
- user-friendly name
- aliases
- source master ID
- source layout relationship ID
- description or intended usage if inferable or manually annotated
- optional operator-authored semantic annotations and usage notes
- preview asset path
- placeholder definitions
- protected static elements
- optional editable free-form zones
- validation rules

In v1, `preview asset path` should be a single canonical field reserved for future rendered preview output, even when no preview image exists yet.

### Placeholder model

Each placeholder should include:

- stable logical name
- PowerPoint placeholder idx
- source type
- supported content types: text, image, table, chart, markdown-text, bullet-list, quote, etc., with v1 guaranteeing text, image, table, chart, and markdown-to-text
- geometry in EMU
- inheritance chain (master -> layout -> slide)
- text defaults where available
- required/optional flag
- overflow policy
- allowed formatting overrides if any

For v1 charts and tables, the fidelity contract is:

- preserve the approved placeholder geometry and placement contract
- accept structured data inputs for population
- preserve basic template-bound container behavior where possible
- treat advanced embedded workbook behavior and highly custom chart internals as best-effort rather than guaranteed

### Protected static element model

Each protected element should include:

- element ID
- element type
- location and size
- lock policy
- asset reference if applicable
- fingerprint/hash for integrity checking

## 15. Architecture

## 15.1 Product architecture

The product should have four core layers.

### A. Package analysis layer

Responsibilities:

- open `.pptx` as an Open Packaging Convention zip package
- inspect PresentationML XML parts
- traverse relationships between presentation, masters, layouts, themes, slides, media, and embedded objects
- extract structure and fingerprints

### B. Manifest compiler layer

Responsibilities:

- normalize extracted data into a stable internal model
- assign stable IDs and names
- infer layout contracts
- emit manifest, schema, annotations template, preview metadata, and compatibility report

### C. Composition engine

Responsibilities:

- create new presentations or slides from preserved template structures
- clone approved layouts and dependent assets
- map input content into placeholders
- preserve branding/static structures
- write valid `.pptx` output

### D. Validation engine

Responsibilities:

- validate input specs
- validate generated output
- compare against source manifest fingerprints and rules
- emit machine-readable diagnostics
- default to warn mode unless strict policy is requested

### E. CLI contract layer

Responsibilities:

- define the structured response envelope and schema versioning policy
- map typed domain and validation outcomes into stable error codes and exit codes
- expose the `guide` command and per-command schema metadata
- enforce output-mode behavior for JSON, human-readable help, and `LLM=true`
- standardize dry-run summaries and change-record shapes for mutating commands

## 15.2 Recommended implementation approach

The safest design is a **hybrid implementation**:

- use direct PresentationML / Open XML package inspection and manipulation for template fidelity and structural correctness
- use a higher-level PowerPoint library selectively where it helps and does not compromise fidelity

The engine should treat the source template as a structured package, not just as a drawing surface.

## 16. Recommended tech stack

### Primary recommendation

**Language:** Python 3.12+

Why:

- strong fit for CLI development
- easy adoption in enterprise developer workflows
- strong ecosystem for YAML/JSON/schema tooling
- good fit for AI-agent-oriented automation
- matches the likely usage pattern of adjacent automation CLIs

### Core libraries

- **Typer** for CLI experience
- **Pydantic v2** for typed models and schema generation
- **lxml** for precise XML parsing and manipulation
- **zipfile** / package utilities for `.pptx` package handling
- **python-pptx** selectively for supported presentation operations and inspection convenience
- **Pillow** for preview/image handling where needed
- **rich** for terminal inspection output
- **jsonschema** for spec validation

### Optional commercial engine path

- **Aspose.Slides for Python via .NET** as an optional premium backend for scenarios that require deeper PowerPoint feature coverage

For v1, the implementation should target the open-source backend only. Commercial backend support should remain an explicit extension point rather than a day-one delivery requirement.

### Why not rely solely on a generation library?

Because the goal is not merely to create slides. The goal is to preserve enterprise fidelity from a source template. High-level generation libraries are useful, but on their own they are not sufficient as the core abstraction for exact template preservation.

The same principle applies to the CLI surface: a collection of ad hoc terminal commands is not sufficient for robust agent orchestration. The CLI contract must itself be designed as a stable machine interface.

## 17. Rendering strategy

The rendering strategy is the heart of the product.

### Preferred strategy

1. initialize from a real enterprise `.pptx`
2. preserve original masters, layouts, and theme dependencies
3. generate slides by cloning approved layout structures
4. populate only approved placeholders and editable zones
5. keep protected static elements untouched
6. validate output before success

### Avoided strategy

- interpret the template once
- regenerate the design from abstract style tokens alone
- hope the generated output visually matches the source

That second strategy is exactly what causes drift.

## 18. Fidelity model

The PRD should define what "1:1 rendition" means in practice.

### Guaranteed in scope

- same slide size and orientation
- same masters/layout relationships
- same theme references where preserved
- same approved static elements
- same placeholder positions and dimensions
- same brand assets referenced from the template package where preserved
- deterministic mapping of content into approved placeholders

### Best-effort / conditional

- exact text reflow where content length differs materially from template expectations
- advanced charts with non-trivial embedded workbook behavior
- advanced table and chart styling behaviors beyond placeholder-bound structured data population
- animations and transition behaviors
- unusual third-party embedded objects

The CLI should be honest: exact fidelity is strongest when it preserves and composes from the original template assets. Where PowerPoint behavior is content-sensitive, the tool should surface that explicitly.

## 19. Error handling and policy modes

The CLI should distinguish machine-readable error codes from human-readable messages.

Recommended error-code families:

- `ERR_VALIDATION_*` for invalid inputs, schema mismatches, and unsupported placeholder mappings
- `ERR_POLICY_*` for strict-mode or governance-policy failures
- `ERR_CONFLICT_*` for stale manifests, fingerprint conflicts, or output-path collisions
- `ERR_IO_*` for file-system and package read/write failures
- `ERR_INTERNAL_*` for unexpected implementation failures

Recommended exit-code categories:

- `0` success
- `10` validation or schema error
- `20` permission or policy failure
- `40` conflict or stale-state failure
- `50` I/O or packaging failure
- `90` internal error

The CLI should support policy modes.

### Strict mode

- fail on unsupported constructs
- fail on undeclared placeholders
- fail when required placeholders are missing
- fail when protected elements change

### Warn mode

- generate output but emit warnings
- this is the default v1 policy mode

### Relaxed mode

- allow specific declared overrides for advanced use cases

For commands that write files, the CLI should also support:

- `--dry-run` to preview outputs without writing
- explicit override flags for dangerous operations such as overwriting existing outputs or bypassing fingerprint checks
- structured change summaries in both dry-run and apply flows

## 20. Extensibility

Future extension points:

- custom content mappers for charts, tables, icons, and diagram blocks
- markdown-to-slide content transformation plugins
- MCP server wrapper for use by coding agents after v1
- Confluence/SharePoint/Jira integration for artifact-fed deck generation
- enterprise policy packs for naming, footer rules, confidentiality markings, and cover-page requirements
- multi-template registries

## 21. Example end-to-end workflow

### Step 1: Initialize

```bash
pptx init ./enterprise-template.pptx --out ./corp-template
```

### Step 2: Inspect

```bash
pptx layouts list --manifest ./corp-template
pptx layouts show executive-two-column --manifest ./corp-template
```

### Step 3: Build deck spec

Create `deck.yaml`.

### Step 4: Generate

```bash
pptx deck build --manifest ./corp-template --spec deck.yaml --out out/deck.pptx
```

Optional preview-first step:

```bash
pptx deck build --manifest ./corp-template --spec deck.yaml --out out/deck.pptx --dry-run
```

### Step 5: Validate

```bash
pptx validate --manifest ./corp-template --deck out/deck.pptx --strict
```

### Step 6: Diff when template changes

```bash
pptx manifest diff ./corp-template-v1 ./corp-template-v2
```

## 22. Acceptance criteria for v1

The product is successful for v1 if all of the following are true:

1. A user can initialize a manifest from a real enterprise `.pptx` template.
2. The tool extracts layouts, placeholders, theme metadata, and protected static elements into a readable manifest package.
3. A user can inspect available layouts and their placeholder contracts from the CLI.
4. A user can generate a new slide or deck using approved layouts only.
5. Generated slides preserve the original template structure closely enough to pass visual review by template owners for the supported layout set.
6. The tool detects and reports unsupported or risky template constructs.
7. The tool validates generated decks and can fail CI when contracts are violated.
8. Template updates can be diffed and breaking changes identified.
9. The CLI exposes a machine-readable `guide` contract and stable JSON response envelope suitable for agent use.
10. Mutating commands support `--dry-run` with structured change summaries.
11. Errors and exit codes are stable enough for shell scripts, CI, and agents to branch without parsing prose.

## 23. Suggested phased roadmap

### Phase 1: Manifest extraction foundation

- open `.pptx`
- parse masters, layouts, themes, placeholders
- emit manifest and compatibility report
- define response envelope, error taxonomy, and guide command
- list/show inspection commands

### Phase 2: Template-preserving slide creation

- create presentation from initialized template package
- clone approved layout structures
- fill text, image, table, and chart placeholders within the v1 fidelity contract
- validate output

### Phase 3: Deck specs and CI

- deck spec schema
- deck build command
- validation command with exit codes
- dry-run summaries and change records for write commands
- manifest diff

### Phase 4: Advanced enterprise features

- chart/table plugins
- preview generation
- manifest annotations
- registry and template governance features

## 24. Risks and mitigations

### Risk: PowerPoint has many edge cases

Mitigation:

- explicitly scope supported features
- emit compatibility reports during init
- preserve original assets instead of recreating them

### Risk: “1:1” is over-promised

Mitigation:

- define fidelity contract clearly
- validate output structurally
- use strict policy modes
- document unsupported constructs transparently

### Risk: Template quality varies

Mitigation:

- doctor/init report highlights problematic templates
- support manual annotations for ambiguous layouts

### Risk: Dynamic CLI surface becomes confusing

Mitigation:

- keep top-level commands stable
- inject manifest-aware validation, help text, and completions rather than inventing too many generated commands

### Risk: CLI is agent-friendly in theory but brittle in practice

Mitigation:

- use one structured response envelope in machine-readable mode
- publish a `guide` command with schemas, examples, and error codes
- keep stdout parseable and move progress chatter to stderr
- require dry-run for risky workflows during automation and CI adoption

## 25. Resolved v1 decisions

The following product decisions are now fixed for v1:

1. Manifest packages are initialized from exactly one source template `.pptx` per package.
2. The manifest supports editable manual annotations for semantic layout purpose, aliases, and operator notes.
3. Layout previews are represented as metadata in v1, but actual preview rendering is deferred.
4. V1 placeholder content support includes text, images, tables, charts, and markdown-to-text mappings.
5. Warn mode is the default policy; strict mode remains available and recommended for CI and governance workflows.
6. An MCP server is explicitly deferred until after v1.
7. A template-specific wrapper CLI generator is included in v1.
8. V1 targets the open-source backend only; commercial backend support is deferred as an extension point.
9. V1 charts and tables preserve approved placeholder geometry and support structured data population, but do not promise full advanced workbook or highly custom styling fidelity.
10. Manual annotations are stored in a separate `annotations.yaml` file rather than inline in `manifest.yaml`.
11. `wrapper generate` emits a Python package scaffold in v1.
12. Preview metadata uses a single canonical preview path field per layout.
13. The CLI adopts an agent-first machine contract with a structured response envelope, stable error codes, exit-code mapping, and a built-in `guide` command.
14. Mutating commands support `--dry-run` and structured change summaries.
15. V1 supports optional per-slide speaker notes using text/markdown formatting, but notes are not part of the placeholder contract and are never required by default.

## 26. Recommendation

This product is worth building.

It addresses the actual failure mode in AI-generated enterprise slides: not lack of content generation, but lack of template-bound structure and exact corporate fidelity.

The strongest implementation is not a "smart prompt for slide creation." It is a **manifest compiler plus template-preserving composition engine**.

That is the right abstraction for enterprise PowerPoint generation.

## 27. One-line product definition

**PPTX is a template-initialized, manifest-driven PowerPoint generator that preserves enterprise masters, layouts, and branding rules so humans and AI agents can create slides that stay inside the original corporate design contract.**
