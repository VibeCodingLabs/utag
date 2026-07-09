"""Typed validation reports (spec: validation_report contract, deterministic)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    error = "error"
    warning = "warning"
    info = "info"


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: Severity
    path: str = ""
    message: str


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact: str
    kind: str
    validator_id: str
    valid: bool
    repairable: bool = True
    attempt: int = 1
    findings: list[Finding] = Field(default_factory=list)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)  # keys in declaration order: deterministic

    @classmethod
    def ok(cls, artifact: str, kind: str, validator_id: str, attempt: int = 1) -> "ValidationReport":
        return cls(artifact=artifact, kind=kind, validator_id=validator_id, valid=True, attempt=attempt)

    @classmethod
    def fail(cls, artifact: str, kind: str, validator_id: str, findings: list[Finding],
             repairable: bool = True, attempt: int = 1) -> "ValidationReport":
        return cls(artifact=artifact, kind=kind, validator_id=validator_id, valid=False,
                   repairable=repairable, attempt=attempt, findings=findings)
