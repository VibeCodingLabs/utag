from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class ImplementationStatus(str, Enum):
    implemented = "implemented"
    planned = "planned"
    not_supported = "not_supported"

class PrimitiveSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    category: str
    description: str = ""

class ProviderGap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primitive_id: str
    competitor_status: ImplementationStatus
    utag_status: ImplementationStatus
    gap_notes: str = ""

class ToolProviderSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    description: str = ""
    capabilities: dict[str, ImplementationStatus] = Field(default_factory=dict)

class CapabilityMatrix(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primitives: list[PrimitiveSpec] = Field(default_factory=list)
    providers: list[ToolProviderSpec] = Field(default_factory=list)
