"""MCP schemas: tool/resource/prompt contracts, gateway policy, quality reports."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from utag_core.schemas import SLUG, StrictSchema


class SideEffect(str, Enum):
    none = "none"
    read = "read"
    write = "write"
    destructive = "destructive"
    network = "network"


class PolicyStatus(str, Enum):
    allowed = "allowed"
    denied = "denied"
    review = "review"


class MCPSideEffectClassification(StrictSchema):
    tool: str = Field(pattern=SLUG)
    classification: SideEffect
    rationale: str = Field(min_length=1)


class MCPToolContract(StrictSchema):
    name: str = Field(pattern=SLUG)
    description: str = Field(min_length=1)
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    side_effect: SideEffect
    auth_scopes: list[str] = []
    policy_status: PolicyStatus = PolicyStatus.review


class MCPResourceContract(StrictSchema):
    uri: str = Field(min_length=1)
    description: str = Field(min_length=1)
    mime_type: str | None = None


class MCPPromptContract(StrictSchema):
    name: str = Field(pattern=SLUG)
    description: str = Field(min_length=1)
    arguments: list[str] = []


class GatewayRule(StrictSchema):
    tool: str = Field(pattern=SLUG)
    status: PolicyStatus
    max_side_effect: SideEffect = SideEffect.read


class MCPGatewayPolicy(StrictSchema):
    id: str = Field(pattern=SLUG)
    rules: list[GatewayRule] = []


class MCPToolQualityReport(StrictSchema):
    tool: str = Field(pattern=SLUG)
    score: float = Field(ge=0, le=1)
    findings: list[str] = []
    has_output_schema: bool = False
    has_auth_hints: bool = False


TOP_LEVEL = [
    MCPToolContract, MCPResourceContract, MCPPromptContract,
    MCPGatewayPolicy, MCPSideEffectClassification, MCPToolQualityReport,
]

EXAMPLES = {
    "MCPToolContract": {"name": "generate-artifact", "description": "Generate a typed artifact from IR",
                        "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
                        "side_effect": "write", "auth_scopes": ["artifacts:write"], "policy_status": "allowed"},
    "MCPResourceContract": {"uri": "utag://targets", "description": "Registered generator targets", "mime_type": "application/json"},
    "MCPPromptContract": {"name": "clarify-task", "description": "6-dim ambiguity clarification", "arguments": ["goal"]},
    "MCPGatewayPolicy": {"id": "default", "rules": [{"tool": "generate-artifact", "status": "allowed", "max_side_effect": "write"}]},
    "MCPSideEffectClassification": {"tool": "generate-artifact", "classification": "write",
                                    "rationale": "writes artifact files to the output directory"},
    "MCPToolQualityReport": {"tool": "generate-artifact", "score": 0.9, "findings": [],
                             "has_output_schema": True, "has_auth_hints": True},
}
