"""Faceted taxonomy against the REAL uploaded files (all three frontmatter
dialects), taxonomy->SKILL.md through our skill-md validator, facet->subagent,
and viper-style typed CLI flags."""
from pathlib import Path

import pytest

import utag_generators  # noqa: F401  registers generators+validators

from agent_harness import (
    CliToolSpec, FlagSpec, SubAgentSpec, cli_tool,
    parse_taxonomy_file, skill_frontmatter, subagent_spec_from_facets,
)
from utag_core.ir import ModuleSpec
from utag_core.registry import get_generator, get_validator

TAX = Path(__file__).parents[2] / "fixtures" / "kits" / "taxonomies"
MASTER = TAX / "master_mapped_taxonomy.md"
PIPELINE = TAX / "ai_agent_pipeline_taxonomy.md"      # ```yaml fenced dialect
OFFERING = TAX / "full_software_and_ai_taxonomy.md"   # ```yaml fenced dialect


@pytest.mark.parametrize("path", [MASTER, PIPELINE, OFFERING], ids=lambda p: p.stem)
def test_real_taxonomy_files_parse(path):
    f = parse_taxonomy_file(path)
    assert f.id and f.title  # every corpus file carries File_ID + Title
    assert f.slug() == f.slug().lower()


def test_master_facets_normalized():
    f = parse_taxonomy_file(MASTER)
    assert f.id == "master_mapped_taxonomy_graphrag_agentic_systems"  # identifier kept verbatim
    assert f.slug() == "master-mapped-taxonomy-graphrag-agentic-systems"  # naming normalizes
    assert "taxonomy" in f.tags and "graphrag" in f.tags  # lowercased per its own rule


def test_taxonomy_to_skill_passes_agentskills_validator():
    module = ModuleSpec(name="tax_skill", provenance={
        "taxonomy_md": MASTER.read_text(),
        "tools": "job_repo_audit, audit_refactors, api_getItem"})
    files = get_generator("taxonomy-skill").generate(module)
    (rel, content), = files.items()
    report = get_validator("skill-md")(rel, content)
    assert report.valid, report.to_json()
    assert rel.split("/")[0] == rel.split("/")[0].lower()
    assert "metadata" in content and "graphrag" in content  # facets preserved under metadata
    # deterministic
    assert files == get_generator("taxonomy-skill").generate(module)


def test_facets_to_subagent_spec():
    f = parse_taxonomy_file(MASTER)
    spec = SubAgentSpec.model_validate(subagent_spec_from_facets(f))
    assert spec.taxonomy and spec.taxonomy.industry  # facet-derived scope
    assert "Stay within stack layers" not in "".join(spec.instructions) or f.stack_layer


def test_cli_flags_typed_and_declared_only():
    spec = CliToolSpec(
        name="printer", argv=["printf", "%s\\n"], allow_extra_args=True,
        description="Print declared flag surface like a cobra binary would.",
        flags=[FlagSpec(name="log-level", type="string", default="info"),
               FlagSpec(name="port", type="int"),
               FlagSpec(name="verbose", type="bool")])
    t = cli_tool(spec)
    assert "--log-level" in t.description and "--port" in t.description
    ok = t.function(flag_values={"log-level": "debug", "port": "8080", "verbose": "true"})
    assert ok.exit_code == 0
    undeclared = t.function(flag_values={"rm": "-rf"})
    assert undeclared.exit_code == 2 and "undeclared flag" in undeclared.stderr_tail
    badint = t.function(flag_values={"port": "not-a-number"})
    assert badint.exit_code == 2 and "expects int" in badint.stderr_tail
