from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Any

class OpenAPIEditorModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_uri: str
    positions: dict[str, Any] = Field(default_factory=dict)
    errors: list[Any] = Field(default_factory=list)

class ArazzoEditorModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workflow_id: str
    nodes: list[Any] = Field(default_factory=list)
    edges: list[Any] = Field(default_factory=list)

class OverlayEditorModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_uri: str
    actions: list[Any] = Field(default_factory=list)

class DiffReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    changes_by_pointer: dict[str, str] = Field(default_factory=dict)

class ValidationPanelModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    findings_by_severity: dict[str, list[Any]] = Field(default_factory=dict)
    findings_by_source: dict[str, list[Any]] = Field(default_factory=dict)
