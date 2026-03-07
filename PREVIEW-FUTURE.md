# Preview Rendering Future Plan

## Status

Draft implementation plan for adding real layout preview image generation to `pptx`.

## Current state

Today the manifest package exposes preview metadata only:

- each layout gets a canonical `preview_path`
- `capabilities.preview_rendering` is `false`
- `pptx init` creates `previews/layouts/.keep` rather than actual image files

This matches the current product and architecture documents:

- `PRD.md` defers real preview rendering beyond v1
- `ARCHITECTURE.md` calls out preview/backend coupling as an open design question

## Goal

Add optional, high-fidelity layout preview PNG generation during `pptx init` while preserving the existing manifest contract and keeping non-Windows environments functional.

## Non-goals

- making PowerPoint a required dependency for the CLI
- building a custom cross-platform slide renderer in the first iteration
- changing the existing `preview_path` field shape
- blocking manifest extraction if preview rendering is unavailable
- asserting pixel-perfect image output in cross-platform CI

## Recommended first implementation

Use an optional Windows-only backend based on PowerPoint COM automation.

Rationale:

- highest expected fidelity to the original enterprise template
- smallest implementation compared with a custom renderer
- keeps the current cross-platform CLI behavior intact by making previews optional

## Product behavior

### Proposed CLI surface

Add an opt-in flag to `pptx init`:

```bash
pptx init Template.pptx --out ./corp-template --render-previews
```

Recommended first-step behavior:

- if `--render-previews` is omitted, behavior stays exactly as it is today
- if `--render-previews` is provided on Windows with PowerPoint available, write PNG previews
- if `--render-previews` is provided but the backend is unavailable, complete `init` and emit a structured warning

Future extension if needed:

```bash
pptx init Template.pptx --out ./corp-template --preview-backend auto
pptx init Template.pptx --out ./corp-template --preview-backend powerpoint
pptx init Template.pptx --out ./corp-template --preview-backend none
pptx init Template.pptx --out ./corp-template --preview-backend require
```

Do not add the backend selector in the first PR unless it is needed immediately. `--render-previews` is the smaller, more reversible contract.

## Output contract

The existing manifest field should remain authoritative:

- `layouts[].preview_path = previews/layouts/{layout_id}.png`

When previews are rendered, the files at those paths should exist.

The init result and report should add preview-specific fields such as:

- `previews_requested`
- `previews_rendered`
- `preview_backend`
- `preview_failures`

Recommended warning code:

- `WARN_PREVIEW_BACKEND_UNAVAILABLE`

Possible additional warning codes:

- `WARN_PREVIEW_RENDER_FAILED`
- `WARN_PREVIEW_EXPORT_PARTIAL`

## Architecture

### New module

Add a new reusable module:

- `src/pptx_cli/core/preview_rendering.py`

Suggested responsibilities:

- define a renderer interface
- generate deterministic preview slides for each layout
- call the selected backend
- return structured preview results to `init`

### Suggested types

Keep the models small and typed:

- `PreviewRenderRequest`
- `PreviewArtifact`
- `PreviewRenderResult`
- `PreviewRenderWarning`
- `PreviewRenderer` protocol or abstract base class

### Backend classes

Start with two implementations:

- `NoopPreviewRenderer`
  - returns a structured "not rendered" result
- `PowerPointComPreviewRenderer`
  - Windows-only
  - uses `pywin32`
  - exports slides to PNG using Microsoft PowerPoint

## Rendering workflow

### 1. Build the manifest as today

Keep manifest extraction unchanged until preview generation begins. This avoids coupling preview failures to extraction logic.

### 2. Build a temporary preview deck

Create one slide per layout using the original template and `source_layout_index`.

Recommended implementation:

- open the stored template copy or source template
- create a new presentation containing one slide per layout
- preserve layout order so exported slide numbers map deterministically to layouts

### 3. Populate placeholders with deterministic sample content

Empty layouts are often not informative, so preview slides should be lightly populated.

Recommended sample policy:

- title placeholders: `"Sample Title"`
- subtitle placeholders: `"Sample Subtitle"`
- body placeholders: short 2-3 line text
- picture placeholders: a bundled sample image asset
- table placeholders: a small 2x2 table
- chart placeholders: a tiny synthetic chart series

Rules:

- sample content must be deterministic
- sample content must be visually neutral
- sample content must not imply product behavior not guaranteed elsewhere

Prefer reusing the existing composition helpers rather than creating a second placeholder-writing path.

### 4. Export slides to PNG

The PowerPoint COM backend should:

1. open the temporary preview deck invisibly
2. export each slide as PNG to a temporary directory
3. map slide `n` to the corresponding layout `layout_id`
4. write each exported image to `previews/layouts/{layout_id}.png`

### 5. Write preview files safely

Preview image writes should follow the same safety principles as other mutating commands:

- stage in a temp directory
- only move final PNGs into `previews/layouts/` after export succeeds
- avoid leaving partial files behind on failure

### 6. Emit structured result metadata

The init response and report should include:

- total layouts considered
- preview count written
- backend name
- warnings and failures by layout where applicable

## File-by-file plan

### `src/pptx_cli/cli.py`

- add `--render-previews` to `pptx init`
- preserve current output envelope and exit code behavior

### `src/pptx_cli/commands/init.py`

- thread preview options into `run_init()`
- include preview summary in dry-run and apply results

### `src/pptx_cli/core/template.py`

- stop treating preview generation as permanently deferred
- keep canonical `preview_path`
- extend init planning to include preview PNG targets when requested
- replace `.keep` behavior with conditional preview generation

### `src/pptx_cli/core/preview_rendering.py`

- add renderer abstraction
- implement temp preview deck generation
- implement preview result reporting

### `src/pptx_cli/core/composition.py`

- expose reusable helpers if needed for deterministic placeholder population
- avoid duplicating image/table/chart insertion logic

### `src/pptx_cli/models/manifest.py`

- keep schema changes minimal
- avoid changing `preview_path`
- only add fields if required for stable reporting

### `src/pptx_cli/models/envelope.py`

- no schema change required unless init result warnings need typed additions

### `pyproject.toml`

- add an optional Windows preview dependency group for `pywin32`
- do not make it a default dependency

### Documentation

Update:

- `README.md`
- `ARCHITECTURE.md`
- `TESTING.md`
- `FEEDBACK.md` only if it is being used as a tracked status artifact

## Suggested implementation phases

### Phase 1: Scaffolding and contract

Deliverables:

- `--render-previews` flag
- preview planning in dry-run output
- preview renderer abstraction
- noop renderer with structured warning path

Acceptance criteria:

- `pptx init --dry-run --render-previews` reports planned PNG outputs
- init still succeeds on systems without PowerPoint

### Phase 2: Windows PowerPoint COM backend

Deliverables:

- temporary preview deck generation
- COM export to PNG
- atomic placement into `previews/layouts/`

Acceptance criteria:

- on a Windows machine with PowerPoint, preview PNGs are generated for all layouts
- `preview_path` files exist after init

### Phase 3: Diagnostics and polish

Deliverables:

- per-layout preview warnings
- clearer init report fields
- README guidance for enabling previews on Windows

Acceptance criteria:

- failures are visible through structured warnings
- partial preview success does not produce raw tracebacks

## Testing plan

### Unit tests

Add tests for:

- preview target planning
- renderer selection
- warning behavior when preview rendering is requested but unavailable
- stable mapping from layout IDs to preview output paths

These should not require PowerPoint.

### Integration tests

Add integration tests for:

- `pptx init --dry-run --render-previews`
- init report/output fields when previews are requested
- successful preview artifact creation with a mocked renderer

### Windows-only smoke test

Add an opt-in smoke test gated by environment, for example:

- `PPTX_TEST_POWERPOINT_COM=true`

This test can:

- run on a Windows machine with PowerPoint installed
- initialize a manifest with `--render-previews`
- assert that PNGs exist for a subset or all layouts

Do not make this test mandatory for normal cross-platform CI.

## Operational concerns

### Dependency management

Do not install `pywin32` everywhere. Keep it optional.

### Resource cleanup

The COM backend must always:

- close the presentation
- quit PowerPoint if this process launched it
- clean up temp files/directories on success and failure

### Determinism

Preview generation should be deterministic enough for inspection and documentation, but exact PNG bytes may vary across Office versions. Avoid hash-based assertions on rendered images.

## Open decisions

### TODO: Decide whether `capabilities.preview_rendering` reflects engine support or actual generated artifacts

Why it matters:

- engine support is global
- artifact presence is package-specific

Recommended first choice:

- leave manifest capability semantics simple
- report actual preview generation in init result and init report instead

### TODO: Decide whether preview slides should be empty or sample-populated

Why it matters:

- empty previews may hide placeholder intent
- sample-populated previews are more useful but require content policy

Recommended first choice:

- populate with deterministic neutral samples

### TODO: Decide whether partial preview generation should be a warning or a failure in `--strict`

Why it matters:

- teams may want CI to fail if preview artifacts are expected but missing

Recommended first choice:

- warning by default
- leave stricter policy for a later phase unless there is a clear requirement now

## Rollout recommendation

Implement this in small PRs:

1. preview contract and noop scaffolding
2. Windows COM backend
3. docs, smoke test, and diagnostics polish

This keeps the change reviewable and avoids coupling a new rendering backend to manifest extraction all at once.
