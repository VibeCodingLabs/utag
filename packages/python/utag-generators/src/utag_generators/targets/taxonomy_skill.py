"""Faceted taxonomy record -> Agent Skills package (SKILL.md).

Frontmatter derives from the master_mapped_taxonomy facets (name/description
per Agent Skills limits; full facet record preserved under the spec-allowed
`metadata` key). Body lists the tool families a subagent in this facet scope
would carry. Output must pass the registered skill-md validator.
"""
from __future__ import annotations

import yaml

from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator


@register_generator("taxonomy-skill")
class TaxonomySkillGenerator:
    """module.provenance['taxonomy_md'] = raw taxonomy file text (any corpus dialect).
    module.provenance['tools'] = optional comma-separated tool names to document."""

    def generate(self, module: ModuleSpec) -> dict[str, str]:
        from agent_harness.taxonomy import parse_frontmatter, skill_frontmatter

        facets = parse_frontmatter(module.provenance["taxonomy_md"])
        fm = skill_frontmatter(facets)
        tools = [t.strip() for t in module.provenance.get("tools", "").split(",") if t.strip()]
        lines = [f"# {fm['name']}", "", facets.summary or facets.title, "",
                 "## Scope", "",
                 f"Facet path: `{facets.path() or facets.slug()}`."]
        if facets.stack_layer:
            lines += ["", f"Stack layers: {', '.join(facets.stack_layer)}."]
        if tools:
            lines += ["", "## Tools", ""] + [f"- `{t}`" for t in tools]
        if facets.workflow:
            lines += ["", "## Workflows", ""] + [f"- {w}" for w in facets.workflow]
        body = "\n".join(lines).rstrip() + "\n"
        fm_yaml = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=100000)
        return {f"{fm['name']}/SKILL.md": f"---\n{fm_yaml}---\n\n{body}"}
