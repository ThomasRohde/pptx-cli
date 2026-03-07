from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CliMessage(BaseModel):
    code: str
    message: str
    retryable: bool = False
    retry_after_ms: int | None = None
    suggested_action: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class Metrics(BaseModel):
    duration_ms: int
    operations_executed: int | None = None
    bytes_written: int | None = None


class Envelope(BaseModel):
    schema_version: str = "1.0"
    request_id: str
    ok: bool
    command: str
    result: dict[str, Any] | list[Any] | str | int | float | bool | None
    warnings: list[CliMessage] = Field(default_factory=list)
    errors: list[CliMessage] = Field(default_factory=list)
    metrics: Metrics


class GuideCommand(BaseModel):
    id: str
    summary: str
    mutates: bool
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    examples: list[str] = Field(default_factory=list)


class GuideDocument(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    compatibility: dict[str, str]
    commands: list[GuideCommand]
    exit_codes: dict[str, int]
    error_codes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    identifier_conventions: dict[str, str] = Field(default_factory=dict)
    concurrency: dict[str, Any] = Field(default_factory=dict)
    content_objects: dict[str, dict[str, Any]] = Field(default_factory=dict)
