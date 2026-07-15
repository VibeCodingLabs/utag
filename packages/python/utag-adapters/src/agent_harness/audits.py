"""audit-kit template -> ephemeral Pydantic AI subagent (subagent-as-tool).

Template fields map onto the agent verbatim:
  purpose + chain-of-verification + do-not-do + quality-bar -> instructions
  required-output.report-sections + definition-of-done      -> output_validator (ModelRetry on violation)
  scope.include/exclude                                     -> read-only file tools, path-contained

Enforced at the type boundary, matching the kit's own rules:
  - every required report section present
  - empty section => body is exactly a NONE FOUND statement with method
  - every finding carries P0/P1/P2 + evidence, or is marked NOT VERIFIED with a reason
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.usage import UsageLimits

# ---------------------------------------------------------------- template (mirrors _schema.json)


class AuditOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report: str = Field(pattern=r"\.md$")
    format: Literal["markdown"]


class AuditScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include: list[str]
    exclude: list[str]


class RequiredEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    types: list[str]
    items: list[str] = Field(min_length=1)


class RequiredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    report_sections: list[str] = Field(alias="report-sections", min_length=3)


class AuditDependencies(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    run_after: list[str] = Field(alias="run-after")
    feeds_into: list[str] = Field(alias="feeds-into")


class AuditTemplate(BaseModel):
    """1:1 with .github/audit/_schema.json."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    name: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    kind: Literal["audit-template"]
    output: AuditOutput
    purpose: str = Field(min_length=10)
    scope: AuditScope
    inputs: list[str] = Field(min_length=1)
    required_evidence: RequiredEvidence = Field(alias="required-evidence")
    schema_validation: list[str] = Field(alias="schema-validation")
    chain_of_verification: list[str] = Field(alias="chain-of-verification", min_length=3)
    do_not_do: list[str] = Field(alias="do-not-do", min_length=6)
    required_output: RequiredOutput = Field(alias="required-output")
    definition_of_done: list[str] = Field(alias="definition-of-done", min_length=5)
    quality_bar: list[str] = Field(alias="quality-bar", min_length=3)
    dependencies: AuditDependencies


def load_template(path: Path) -> AuditTemplate:
    return AuditTemplate.model_validate(yaml.safe_load(Path(path).read_text()))


# ---------------------------------------------------------------- structured report


class Finding(BaseModel):
    """quality-bar contract: severity + evidence, or NOT VERIFIED with reason."""
    id: str
    severity: Literal["P0", "P1", "P2"]
    description: str
    evidence: str = Field(default="", description="file:line range, command output, or artifact ref")
    not_verified_reason: str = Field(default="", description="set iff evidence could not be obtained")
    recommendation: str = ""


class ReportSection(BaseModel):
    title: str
    body: str = Field(description="markdown; if nothing found write 'NONE FOUND — <search method used>'")


class AuditReport(BaseModel):
    template: str
    report_file: str
    sections: list[ReportSection]
    findings: list[Finding]
    not_verified: list[str] = Field(default_factory=list, description="items that could not be verified + reason")
    chain_executed: list[str] = Field(description="chain-of-verification steps actually executed, in order")


# ---------------------------------------------------------------- read-only subagent tools


@dataclass
class AuditDeps:
    root: Path


def _contained(root: Path, rel: str) -> Path | None:
    p = (root / rel).resolve()
    return p if p.is_relative_to(root.resolve()) else None


def _in_scope(rel: str, scope: AuditScope) -> bool:
    inc = any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, g.rstrip("/**") + "/*") for g in scope.include) \
        if scope.include else True
    exc = any(fnmatch.fnmatch(rel, g) for g in scope.exclude)
    return inc and not exc


def _scoped_tools(scope: AuditScope) -> list[Tool]:
    def list_paths(ctx: RunContext[AuditDeps], glob: str = "**/*", limit: int = 200) -> list[str]:
        """List repo-relative file paths matching a glob, filtered to the audit scope."""
        root = ctx.deps.root.resolve()
        out: list[str] = []
        for p in sorted(root.glob(glob)):
            if not p.is_file():
                continue
            rel = p.relative_to(root).as_posix()
            if _in_scope(rel, scope):
                out.append(rel)
            if len(out) >= limit:
                break
        return out

    def read_file(ctx: RunContext[AuditDeps], path: str, max_bytes: int = 50_000) -> str:
        """Read a repo-relative file (read-only, path-contained, scope-checked).
        Returns 'ERROR: ...' text on scope/containment/missing-file — use list_paths to find valid targets."""
        rel = path.lstrip("/")
        p = _contained(ctx.deps.root, rel)
        if p is None:
            return f"ERROR: path escapes audit root: {rel}"
        if not _in_scope(rel, scope):
            return f"ERROR: path outside audit scope {scope.include}: {rel}"
        if not p.is_file():
            return f"ERROR: file not found: {rel} — call list_paths first"
        return p.read_bytes()[:max_bytes].decode("utf-8", errors="replace")

    return [Tool(list_paths, takes_ctx=True), Tool(read_file, takes_ctx=True)]


# ---------------------------------------------------------------- agent factory


def _instructions(t: AuditTemplate) -> str:
    def block(title: str, items: list[str], numbered: bool = False) -> str:
        marks = (f"{i}." for i in range(1, len(items) + 1)) if numbered else iter(lambda: "-", None)
        return f"## {title}\n" + "\n".join(f"{m} {it}" for m, it in zip(marks, items))

    return "\n\n".join([
        f"You are the '{t.name}' audit subagent (v{t.version}). Read-only. You never modify anything.",
        f"## Purpose\n{t.purpose}",
        f"## Target report\n{t.output.report}",
        block("Chain of verification — execute literally, in order", t.chain_of_verification, numbered=True),
        block("Hard prohibitions", t.do_not_do),
        block("Quality bar — every finding", t.quality_bar),
        block("Definition of done", t.definition_of_done),
        "## Honesty contract\nEvery claim needs evidence or the explicit marker NOT VERIFIED with a reason. "
        "An empty section is written as 'NONE FOUND — <search method used>'. Omission is fabrication.",
    ])


def build_audit_agent(template: AuditTemplate, model, *, retries: int = 2,
                      extra_tools: list[Tool] | None = None) -> Agent[AuditDeps, AuditReport]:
    agent: Agent[AuditDeps, AuditReport] = Agent(
        model,
        deps_type=AuditDeps,
        output_type=AuditReport,
        instructions=_instructions(template),
        tools=_scoped_tools(template.scope) + (extra_tools or []),
        retries=retries,
        name=f"audit_{template.name.lower().replace(' ', '_')}",
    )
    required = [s.strip().lower() for s in template.required_output.report_sections]

    @agent.output_validator
    def enforce_dod(ctx: RunContext[AuditDeps], report: AuditReport) -> AuditReport:
        titles = {s.title.strip().lower() for s in report.sections}
        if missing := [s for s in required if s not in titles]:
            raise ModelRetry(f"missing required report sections: {missing}. "
                             f"Required: {template.required_output.report_sections}")
        for s in report.sections:
            if not s.body.strip():
                raise ModelRetry(f"section '{s.title}' is empty — write 'NONE FOUND — <search method>' instead")
        for f in report.findings:
            if not f.evidence.strip() and not f.not_verified_reason.strip():
                raise ModelRetry(f"finding '{f.id}' has neither evidence nor a NOT VERIFIED reason — "
                                 "the quality bar forbids uncited claims")
        if len(report.chain_executed) < len(template.chain_of_verification):
            raise ModelRetry(f"chain_executed lists {len(report.chain_executed)} steps; template requires all "
                             f"{len(template.chain_of_verification)} executed (or explicitly marked NOT VERIFIED)")
        return report

    return agent


def audit_tool(template_path: Path, model, *, root: Path,
               usage_limits: UsageLimits | None = None) -> Tool:
    """Subagent-as-tool: ephemeral audit agent the parent harness can invoke by name."""
    t = load_template(Path(template_path))
    limits = usage_limits or UsageLimits(request_limit=25)
    tool_name = f"audit_{Path(template_path).stem.replace('-', '_')}"

    async def _run() -> AuditReport:
        agent = build_audit_agent(t, model)  # ephemeral: constructed per call, discarded after
        result = await agent.run(
            f"Run the '{t.name}' audit on the repository at the tool root. "
            f"Inputs to consume: {', '.join(t.inputs)}.",
            deps=AuditDeps(root=Path(root)),
            usage_limits=limits,
        )
        return result.output

    _run.__name__ = tool_name
    return Tool(_run, name=tool_name, takes_ctx=False,
                description=f"[audit-kit {t.name} v{t.version}] {t.purpose} Produces {t.output.report}. "
                            f"Run after: {', '.join(t.dependencies.run_after) or 'none'}.")
