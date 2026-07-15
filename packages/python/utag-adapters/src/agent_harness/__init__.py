"""agent-harness adapters: forge-jobs manifests and audit-kit templates as Pydantic AI tools.

Two thin bridges, zero rewrites of existing kits:
- jobs:   <category>/<job>/job.yaml + scripts/run.sh  -> Tool (subprocess, structured JobResult)
- audits: .github/audit/<name>.yml                    -> ephemeral subagent Tool (structured AuditReport,
          definition-of-done enforced via output_validator + ModelRetry)
"""

from .jobs import JobManifest, JobResult, load_manifest, job_tool, run_job
from .audits import AuditTemplate, AuditReport, Finding, ReportSection, load_template, build_audit_agent, audit_tool
from .registry import discover_jobs, discover_audit_templates, harness_tools
from .home import SkillRef, SlashCommand, UtagHome
from .models_catalog import ModelInfo, load_catalog, models, provider_env
from .session import EXPERT_PROMPT, Session, skill_loader_tool
from .session_tools import GenerateResult, generation_tools, session_toolset
from .veriforge_bridge import (HeuristicScorer, LLMScorer, NullAsker, PydanticAIClient,
                               build_agents, enhance, veriforge_tools, vf_agent)
from .taxonomy import (FacetFrontmatter, parse_frontmatter, parse_taxonomy_file,
                       skill_frontmatter, subagent_spec_from_facets)
from .subagents import (SubAgentSpec, Taxonomy, CliToolSpec, FlagSpec, OpenAPIToolsSpec,
                        build_subagent, subagent_tool, cli_tool, skill_tool,
                        openapi_endpoint_tools, openapi_kb_tool, taxonomy_subagents)

__all__ = [
    "JobManifest", "JobResult", "load_manifest", "job_tool", "run_job",
    "AuditTemplate", "AuditReport", "Finding", "ReportSection",
    "load_template", "build_audit_agent", "audit_tool",
    "discover_jobs", "discover_audit_templates", "harness_tools",
    "SubAgentSpec", "Taxonomy", "CliToolSpec", "FlagSpec", "OpenAPIToolsSpec",
    "SkillRef", "SlashCommand", "UtagHome",
    "ModelInfo", "load_catalog", "models", "provider_env",
    "EXPERT_PROMPT", "Session", "skill_loader_tool",
    "GenerateResult", "generation_tools", "session_toolset",
    "HeuristicScorer", "LLMScorer", "NullAsker", "PydanticAIClient",
    "build_agents", "enhance", "veriforge_tools", "vf_agent",
    "FacetFrontmatter", "parse_frontmatter", "parse_taxonomy_file",
    "skill_frontmatter", "subagent_spec_from_facets",
    "build_subagent", "subagent_tool", "cli_tool", "skill_tool",
    "openapi_endpoint_tools", "openapi_kb_tool", "taxonomy_subagents",
]

__version__ = "0.1.0"
