from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field

class AgentReadinessScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_score: int
    dimensions: dict[str, int] = Field(default_factory=dict)
    remediation_suggestions: list[str] = Field(default_factory=list)

class DocsSmellReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    smells_found: int
    details: list[str] = Field(default_factory=list)

class MCPToolQualityScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: str
    score: int
    warnings: list[str] = Field(default_factory=list)

class OperationCoverageReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    covered_operations: int
    total_operations: int

class RuntimeDriftReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drift_detected: bool
    drift_details: list[str] = Field(default_factory=list)

class UsageAnalyticsEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: str
    event_data: dict[str, str] = Field(default_factory=dict)
