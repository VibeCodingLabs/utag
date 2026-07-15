from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Any

class OpenAPISource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uri: str
    content: str = ""

class OpenAPIDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    paths: dict[str, Any] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)

class OpenAPIBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document: OpenAPIDocument
    resolved_refs: list[str] = Field(default_factory=list)

class OpenAPIDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    changed: list[str] = Field(default_factory=list)

class OverlayPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: list[dict[str, Any]] = Field(default_factory=list)

class ValidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    message: str
    severity: str

class BreakingChangeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    breaking_changes: list[str] = Field(default_factory=list)

class AgentReadinessReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_ready: bool
    warnings: list[str] = Field(default_factory=list)
