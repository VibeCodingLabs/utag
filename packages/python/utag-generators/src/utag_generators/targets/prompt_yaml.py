"""Prompt-YAML round-trip: parse the user's prompt format <-> IR-adjacent model.

Format (from fixtures ingest-docs/categorize-file/generate-cobra/normalize-tool):
version, name, type, variables[{name,type,required,values?,default?}],
guardrails?, messages[{role,content}].
"""
from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator


class PromptVariable(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: str
    required: bool = False
    values: list[str] | None = None
    default: Any = None


class PromptMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str
    content: str


class PromptFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    name: str
    type: str = "system"
    variables: list[PromptVariable] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    messages: list[PromptMessage] = Field(default_factory=list)

    @classmethod
    def parse(cls, text: str) -> "PromptFile":
        return cls.model_validate(yaml.safe_load(text))

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.model_dump(exclude_defaults=False), sort_keys=False,
                              allow_unicode=True, default_flow_style=False)


@register_generator("prompt-yaml")
class PromptYamlGenerator:
    """Emit a prompt YAML whose variables mirror the first type's fields."""

    def generate(self, module: ModuleSpec) -> dict[str, str]:
        t = module.types[0] if module.types else None
        variables = [
            PromptVariable(name=f.name.upper(), type="string", required=f.required)
            for f in (t.fields if t else [])
        ]
        pf = PromptFile(
            version="1.0", name=module.name.replace("_", "-"),
            variables=variables,
            messages=[PromptMessage(role="system", content=(
                f"You generate {t.name if t else module.name} records. "
                "Output strict JSON only. Halt with: Task complete."))],
        )
        return {f"{pf.name}.prompt.yaml": pf.to_yaml()}
