"""IR/SkillSpec -> Agent Skills package (SKILL.md + frontmatter per open spec)."""
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SkillSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=64)
    description: str = Field(max_length=1024)
    license: str = "MIT"
    body: str

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not NAME_RE.match(v):
            raise ValueError("skill name: lowercase alnum + single hyphens, no lead/trail/dup hyphens")
        return v

    @field_validator("description")
    @classmethod
    def _desc(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("angle brackets not allowed in frontmatter")
        return v


@register_generator("agent-skill")
class AgentSkillGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        spec = SkillSpec(
            name=module.name.replace("_", "-"),
            description=module.description or f"Skill generated from module {module.name}.",
            body=_body(module),
        )
        skill_md = (
            f"---\nname: {spec.name}\ndescription: {spec.description}\n"
            f"license: {spec.license}\n---\n\n{spec.body}\n"
        )
        return {f"{spec.name}/SKILL.md": skill_md}


def _body(module: ModuleSpec) -> str:
    lines = [f"# {module.name}", "", module.description or "", "## Types", ""]
    for t in module.types:
        lines.append(f"- **{t.name}**: " + ", ".join(f.name for f in t.fields))
    return "\n".join(lines).strip()
