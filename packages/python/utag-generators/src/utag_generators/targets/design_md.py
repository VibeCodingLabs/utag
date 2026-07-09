"""DesignTokens -> DESIGN.md (google-labs-code/design.md, version: alpha)."""
from __future__ import annotations

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator


class DesignTokens(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    version: str = "alpha"
    colors: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, dict] = Field(default_factory=dict)
    rounded: dict[str, str] = Field(default_factory=dict)
    spacing: dict[str, str] = Field(default_factory=dict)
    components: dict[str, dict] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _primary_required(self) -> "DesignTokens":
        if self.colors and "primary" not in self.colors:
            raise ValueError("colors must define at least `primary` (spec: Colors section)")
        return self


SECTION_ORDER = ["Overview", "Colors", "Typography", "Layout", "Elevation & Depth",
                 "Shapes", "Components", "Do's and Don'ts"]


@register_generator("design-md")
class DesignMdGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        tokens = DesignTokens(
            name=module.name,
            colors={"primary": "#1a1c1e", "neutral": "#f7f5f2"},
        )
        fm = yaml.safe_dump(tokens.model_dump(exclude_defaults=False), sort_keys=False)
        body = "\n\n".join(
            f"## {s}\n\n{module.description or module.name} — {s.lower()} guidance."
            for s in SECTION_ORDER[:2]
        )
        return {"DESIGN.md": f"---\n{fm}---\n\n{body}\n"}
