"""Discovery: point at the kits on disk, get back Tool lists for the harness agent.

Opt-in by design (minimal-core doctrine): nothing is registered unless a path is given,
and category/name filters let the user pull in only the packs they want.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Tool
from pydantic_ai.usage import UsageLimits

from .audits import audit_tool, load_template
from .jobs import JobManifest, job_tool, load_manifest

_SKIP_DIRS = {"shared", "schema", "tools", "docs", ".git"}


def discover_jobs(jobs_root: Path, categories: set[str] | None = None) -> dict[Path, JobManifest]:
    """Find every <category>/<job>/job.yaml under a forge-jobs checkout. Invalid manifests raise."""
    jobs_root = Path(jobs_root).resolve()
    found: dict[Path, JobManifest] = {}
    for manifest_path in sorted(jobs_root.glob("*/*/job.yaml")):
        job_dir = manifest_path.parent
        category = job_dir.parent.name
        if category in _SKIP_DIRS:
            continue
        if categories and category not in categories:
            continue
        found[job_dir] = load_manifest(job_dir)
    return found


def discover_audit_templates(audit_dir: Path, names: set[str] | None = None) -> dict[Path, str]:
    """Find every audit template YAML (excluding _schema.json/README). Returns path -> template name."""
    audit_dir = Path(audit_dir).resolve()
    found: dict[Path, str] = {}
    for p in sorted(audit_dir.glob("*.yml")):
        if names and p.stem not in names:
            continue
        found[p] = load_template(p).name
    return found


def harness_tools(*, jobs_root: Path | None = None, job_categories: set[str] | None = None,
                  audit_dir: Path | None = None, audit_names: set[str] | None = None,
                  audit_model=None, audit_root: Path | None = None,
                  audit_usage_limits: UsageLimits | None = None) -> list[Tool]:
    """One call: kits on disk -> list[Tool] for Agent(tools=...). Everything opt-in."""
    tools: list[Tool] = []
    if jobs_root is not None:
        tools += [job_tool(d) for d in discover_jobs(Path(jobs_root), job_categories)]
    if audit_dir is not None:
        if audit_model is None or audit_root is None:
            raise ValueError("audit tools need audit_model and audit_root")
        tools += [audit_tool(p, audit_model, root=Path(audit_root), usage_limits=audit_usage_limits)
                  for p in discover_audit_templates(Path(audit_dir), audit_names)]
    return tools
