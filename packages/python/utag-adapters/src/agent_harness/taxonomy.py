"""Faceted taxonomy: parse master_mapped_taxonomy-style frontmatter into strict
facets, derive SubAgentSpecs and SKILL.md frontmatter from them.

Facet set mirrors master_mapped_taxonomy.md (14 controlled-vocabulary facets +
governed tag arrays). Values normalize to lowercase-hyphen per its own rule.
Parser accepts the three real front-matter dialects in the corpus:
  ---\\n<yaml>\\n---   |   ---\\n<yaml>\\n***   |   leading ```yaml fenced block
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG = re.compile(r"[^a-z0-9]+")


def norm(v: str) -> str:
    return _SLUG.sub("-", str(v).strip().lower()).strip("-")


def _listy(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [norm(p) for p in re.split(r"[,;]", v) if p.strip()]
    return [norm(x) for x in v]


class FacetFrontmatter(BaseModel):
    """Strict facet record (master_mapped_taxonomy schema). Unknown keys are
    dropped by the parser, not invented; extras forbidden here."""
    model_config = ConfigDict(extra="forbid")
    id: str = ""
    title: str = ""
    summary: str = ""
    version: str = ""
    industry: str = ""
    domain: str = ""
    service_type: list[str] = Field(default_factory=list)
    niche: list[str] = Field(default_factory=list)
    workflow: list[str] = Field(default_factory=list)
    brand: str = ""
    artifact_type: str = ""
    stack_layer: list[str] = Field(default_factory=list)
    interface_type: list[str] = Field(default_factory=list)
    api_kind: list[str] = Field(default_factory=list)
    library_framework: list[str] = Field(default_factory=list)
    maturity: str = ""
    tags: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    apis: list[str] = Field(default_factory=list)

    @field_validator("industry", "domain", "brand", "artifact_type", "maturity", mode="before")
    @classmethod
    def _norm_scalar(cls, v):
        return norm(v) if v else ""

    @field_validator("service_type", "niche", "workflow", "stack_layer", "interface_type",
                     "api_kind", "library_framework", "tags", "tools", "platforms", "apis",
                     mode="before")
    @classmethod
    def _norm_list(cls, v):
        return _listy(v)

    def slug(self) -> str:
        base = self.id or self.title or "unnamed"
        return norm(base)[:60].strip("-") or "unnamed"

    def path(self) -> str:
        parts = [self.industry, self.domain,
                 self.service_type[0] if self.service_type else "",
                 self.niche[0] if self.niche else "",
                 self.workflow[0] if self.workflow else ""]
        return "/".join(p for p in parts if p)


_KEYMAP = {"file_id": "id", "file-id": "id"}
_KNOWN = set(FacetFrontmatter.model_fields)


def parse_frontmatter(text: str) -> FacetFrontmatter:
    """Extract the leading metadata block in any of the corpus dialects."""
    block = None
    if text.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n(?:---|\*\*\*)\s*\n", text, re.S)
        if m:
            block = m.group(1)
    if block is None:
        m = re.search(r"```yaml\s*\n(.*?)\n```", text, re.S)
        if m:
            block = m.group(1)
    if block is None:
        raise ValueError("no frontmatter block found (---/***/```yaml dialects supported)")
    # corpus dialect 4: a ```yaml fence nested INSIDE the --- block
    fence = re.search(r"```yaml\s*\n(.*?)\n```", block, re.S)
    if fence:
        block = fence.group(1)
    elif block.lstrip().startswith("```"):
        block = re.sub(r"^\s*```[a-z]*\s*\n|\n```\s*$", "", block, flags=re.S)
    try:
        raw = yaml.safe_load(block) or {}
    except yaml.YAMLError:
        m2 = re.search(r"```yaml\s*\n(.*?)\n```", text, re.S)
        if not m2:
            raise
        raw = yaml.safe_load(m2.group(1)) or {}
    data = {}
    for k, v in raw.items():
        key = _KEYMAP.get(str(k).lower().replace(" ", "_"), str(k).lower())
        if key in _KNOWN:
            data[key] = v
    return FacetFrontmatter.model_validate(data)


def parse_taxonomy_file(path: Path) -> FacetFrontmatter:
    return parse_frontmatter(Path(path).read_text(errors="replace"))


def skill_frontmatter(f: FacetFrontmatter) -> dict:
    """Facets -> Agent Skills frontmatter (name<=64 lc-hyphen, description<=1024,
    facets preserved under the spec-allowed `metadata` key)."""
    name = f.slug()[:64].strip("-")
    use_when = ", ".join((f.workflow or f.niche or [f.domain or "this domain"])[:3])
    desc = (f.summary.strip() or f.title.strip() or name).replace("<", "").replace(">", "")
    desc = f"{desc} Use when working on {use_when}."[:1024]
    meta = {k: v for k, v in f.model_dump().items()
            if v and k not in ("id", "title", "summary", "version")}
    return {"name": name, "description": desc, "license": "Proprietary", "metadata": meta}


def subagent_spec_from_facets(f: FacetFrontmatter, **overrides) -> dict:
    """FacetFrontmatter -> SubAgentSpec kwargs (dict so callers stay decoupled)."""
    from .subagents import SubAgentSpec, Taxonomy  # local import: avoid cycle
    tax = Taxonomy(industry=f.industry or "general", domain=f.domain or "general",
                   service=(f.service_type[0] if f.service_type else "service"),
                   niche=(f.niche[0] if f.niche else ""),
                   task=(f.workflow[0] if f.workflow else ""))
    spec = {"name": f.slug()[:60].strip("-") or "subagent",
            "purpose": (f.summary or f.title or f.slug()).strip()[:400] + " (facet-scoped subagent.)",
            "taxonomy": tax.model_dump(),
            "instructions": [f"Stay within stack layers: {', '.join(f.stack_layer)}."]
            if f.stack_layer else []}
    spec.update(overrides)
    return SubAgentSpec.model_validate(spec).model_dump()
