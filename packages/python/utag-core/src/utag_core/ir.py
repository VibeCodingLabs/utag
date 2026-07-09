"""Normalized intermediate representation (IR).

Every ingest source (prompt YAML, NL, KB file, transcript) normalizes into these
models; every target generator consumes only these models. Strict: extra
properties rejected (spec: structured_output_contract).
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ScalarKind(str, Enum):
    string = "string"
    integer = "integer"
    number = "number"
    boolean = "boolean"
    datetime = "datetime"
    any = "any"


class Constraint(_Strict):
    """Portable constraint; each target maps it to native syntax."""
    kind: str  # min_length|max_length|ge|le|pattern|enum|format
    value: Any


class FieldSpec(_Strict):
    name: str
    type: ScalarKind | str  # scalar kind or reference to another TypeSpec name
    required: bool = True
    nullable: bool = False
    array: bool = False
    description: str = ""
    default: Any = None
    constraints: list[Constraint] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _ident(cls, v: str) -> str:
        if not v or not v.replace("_", "a").replace("-", "a").isalnum():
            raise ValueError(f"invalid field name: {v!r}")
        return v


class TypeSpec(_Strict):
    name: str
    description: str = ""
    fields: list[FieldSpec] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _pascal(cls, v: str) -> str:
        if not v or not v[0].isalpha() or not v.replace("_", "a").isalnum():
            raise ValueError(f"invalid type name: {v!r}")
        return v


class ModuleSpec(_Strict):
    name: str
    description: str = ""
    types: list[TypeSpec] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)  # source path/hash/kind

    @field_validator("name")
    @classmethod
    def _ident(cls, v: str) -> str:
        if not v or not v.replace("_", "a").replace("-", "a").isalnum():
            raise ValueError(f"invalid module name: {v!r}")
        return v


class ProjectSpec(_Strict):
    name: str
    version: str = "0.1.0"
    modules: list[ModuleSpec] = Field(default_factory=list)


class ArtifactPlan(_Strict):
    """Explicit generation plan (spec: artifact-planner)."""
    target: str            # registered generator key
    module: ModuleSpec
    out_path: str
    validators: list[str] = Field(default_factory=list)
    max_attempts: int = 3
