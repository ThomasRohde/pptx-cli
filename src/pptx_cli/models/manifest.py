from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PageSize(BaseModel):
    width_emu: int
    height_emu: int


class ThemeModel(BaseModel):
    name: str | None = None
    colors: dict[str, str] = Field(default_factory=dict)
    fonts: dict[str, str] = Field(default_factory=dict)
    effects: dict[str, str] = Field(default_factory=dict)


class AssetRef(BaseModel):
    id: str
    kind: Literal["image", "media", "embedded", "template", "theme", "xml"]
    path: str
    source_path: str | None = None
    sha256: str
    size_bytes: int


class ProtectedElement(BaseModel):
    element_id: str
    element_type: str
    name: str
    left_emu: int
    top_emu: int
    width_emu: int
    height_emu: int
    lock_policy: Literal["locked"] = "locked"
    asset_ref: str | None = None
    fingerprint: str


class PlaceholderContract(BaseModel):
    logical_name: str
    source_name: str
    placeholder_idx: int
    placeholder_type: str
    guidance_text: str | None = None
    guidance_lines: list[str] = Field(default_factory=list)
    supported_content_types: list[str]
    left_emu: int
    top_emu: int
    width_emu: int
    height_emu: int
    required: bool = False
    overflow_policy: Literal["fit", "warn", "truncate"] = "warn"
    text_defaults: dict[str, Any] = Field(default_factory=dict)
    inheritance_chain: list[str] = Field(default_factory=list)
    allowed_formatting_overrides: list[str] = Field(default_factory=list)


class LayoutContract(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    source_master_id: str
    source_layout_index: int
    source_layout_name: str
    description: str | None = None
    preview_path: str
    placeholders: list[PlaceholderContract] = Field(default_factory=list)
    protected_static_elements: list[ProtectedElement] = Field(default_factory=list)
    validation_rules: dict[str, Any] = Field(default_factory=dict)


class MasterContract(BaseModel):
    id: str
    name: str
    layout_ids: list[str] = Field(default_factory=list)


class TemplateInfo(BaseModel):
    name: str
    source_file: str
    source_hash: str
    extracted_at: datetime
    stored_template_path: str
    locale: str | None = None
    owner: str | None = None
    version: str | None = None


class CompatibilityFinding(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CompatibilityReport(BaseModel):
    status: Literal["ok", "warn", "error"] = "ok"
    findings: list[CompatibilityFinding] = Field(default_factory=list)


class ManifestDocument(BaseModel):
    manifest_version: Literal[1] = 1
    template: TemplateInfo
    presentation: dict[str, Any]
    masters: list[MasterContract]
    layouts: list[LayoutContract]
    assets: list[AssetRef] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    compatibility_report: CompatibilityReport = Field(default_factory=CompatibilityReport)
    fingerprints: dict[str, str] = Field(default_factory=dict)


class LayoutAnnotation(BaseModel):
    layout_id: str
    aliases: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    usage_notes: str | None = None


class TemplateAnnotations(BaseModel):
    semantic_tags: list[str] = Field(default_factory=list)
    operator_notes: str | None = None


class AnnotationsDocument(BaseModel):
    template_annotations: TemplateAnnotations = Field(default_factory=TemplateAnnotations)
    layouts: list[LayoutAnnotation] = Field(default_factory=list)


class InitReport(BaseModel):
    template: str
    output_dir: str
    manifest_path: str
    findings: list[CompatibilityFinding] = Field(default_factory=list)
    assets_copied: int = 0
    layout_count: int = 0
    placeholder_count: int = 0


class SlideSpec(BaseModel):
    layout: str
    content: dict[str, Any] = Field(default_factory=dict)


class DeckSpec(BaseModel):
    manifest: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    slides: list[SlideSpec]


class ValidationIssue(BaseModel):
    code: str
    severity: Literal["warning", "error"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    manifest_path: str
    deck_path: str
    ok: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    checked_slides: int = 0
    checked_layouts: int = 0


class ManifestDiffResult(BaseModel):
    breaking_changes: list[dict[str, Any]] = Field(default_factory=list)
    additive_changes: list[dict[str, Any]] = Field(default_factory=list)
    unchanged: list[str] = Field(default_factory=list)
