"""SubAgents: ephemeral pydantic-ai agents equipped with heterogeneous tools —
CLI binaries (incl. cobra harnesses), Skills, OpenAPI endpoints (REST/CRUD verbs),
the openapi.tools knowledge base, forge-jobs, audit-kit templates, and MCP
toolsets (passthrough). Claude-Code-style subagent-per-task, provider-agnostic.

Taxonomy-ready: SubAgentSpec carries an optional <industry>/<domain>/<service>/
<niche>/<task> Taxonomy; taxonomy_subagents() maps taxonomy rows to specs
(feed it master_mapped_taxonomy.md rows when supplied — nothing is invented here).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, Tool
from pydantic_ai.usage import UsageLimits

from .audits import audit_tool
from .jobs import job_tool

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
ALL_METHODS = {"GET", "PUT", "POST", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"}


# ---------------------------------------------------------------- spec

class Taxonomy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    industry: str
    domain: str
    service: str
    niche: str = ""
    task: str = ""

    def path(self) -> str:
        return "/".join(p for p in (self.industry, self.domain, self.service,
                                    self.niche, self.task) if p)


class FlagSpec(BaseModel):
    """Viper-style typed flag: declared surface only — the model sets values,
    never invents flags (mirrors cobra persistent/local flag discipline)."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    type: Literal["string", "int", "bool"] = "string"
    default: str = ""
    description: str = ""


class CliToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    argv: list[str] = Field(min_length=1)
    description: str = Field(min_length=10)
    flags: list[FlagSpec] = Field(default_factory=list)
    timeout_seconds: int = Field(default=60, ge=1, le=3600)
    allow_extra_args: bool = False  # off = fixed argv only (no injection surface)


class OpenAPIToolsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec_path: str            # OpenAPI 3.x JSON/YAML on disk
    base_url: str
    allow_methods: set[str] = Field(default_factory=lambda: set(SAFE_METHODS))
    bearer_token_env: str = ""  # env var NAME only; value read at call time, never stored


class SubAgentSpec(BaseModel):
    """Everything needed to mint an ephemeral subagent. Strict; LLM-produceable."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    purpose: str = Field(min_length=10)
    instructions: list[str] = Field(default_factory=list)
    taxonomy: Taxonomy | None = None
    cli_tools: list[CliToolSpec] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)        # SKILL.md dirs
    openapi: OpenAPIToolsSpec | None = None
    openapi_kb_path: str = ""                              # openapi.tools registry json
    job_dirs: list[str] = Field(default_factory=list)      # forge-jobs
    audit_templates: list[str] = Field(default_factory=list)
    audit_root: str = "."
    request_limit: int = Field(default=25, ge=1, le=200)


# ---------------------------------------------------------------- tool factories

class CliResult(BaseModel):
    exit_code: int
    stdout_tail: str
    stderr_tail: str
    timed_out: bool = False


def cli_tool(spec: CliToolSpec) -> Tool:
    """Any CLI (incl. utag go-harness / cobra binaries) as a structured tool.
    Fixed argv by default — the model cannot inject arguments unless opted in."""
    if shutil.which(spec.argv[0]) is None and not Path(spec.argv[0]).is_file():
        raise FileNotFoundError(f"cli tool {spec.name}: binary not found: {spec.argv[0]}")

    declared = {f.name: f for f in spec.flags}

    def _run(flag_values: dict[str, str] | None = None,
             extra_args: list[str] | None = None) -> CliResult:
        argv = list(spec.argv)
        for k, v in (flag_values or {}).items():
            f = declared.get(k)
            if f is None:
                return CliResult(exit_code=2, stdout_tail="",
                                 stderr_tail=f"undeclared flag: --{k} (declared: {sorted(declared)})")
            if f.type == "bool":
                if str(v).lower() in ("1", "true", "yes"):
                    argv.append(f"--{f.name}")
            elif f.type == "int":
                try:
                    argv.append(f"--{f.name}={int(v)}")
                except (TypeError, ValueError):
                    return CliResult(exit_code=2, stdout_tail="",
                                     stderr_tail=f"flag --{k} expects int, got {v!r}")
            else:
                argv.append(f"--{f.name}={v}")
        argv += (list(extra_args or []) if spec.allow_extra_args else [])
        try:
            p = subprocess.run(argv, capture_output=True, text=True,
                               timeout=spec.timeout_seconds)
            return CliResult(exit_code=p.returncode, stdout_tail=p.stdout[-4000:],
                             stderr_tail=p.stderr[-4000:])
        except subprocess.TimeoutExpired as e:
            return CliResult(exit_code=-1, stdout_tail=(e.stdout or "")[-2000:],
                             stderr_tail=(e.stderr or "")[-2000:], timed_out=True)

    _run.__name__ = f"cli_{spec.name}"
    desc = spec.description
    if spec.flags:
        desc += " Flags: " + "; ".join(
            f"--{f.name} ({f.type}{', default ' + f.default if f.default else ''}) {f.description}".strip()
            for f in spec.flags)
    return Tool(_run, name=_run.__name__, description=desc, takes_ctx=False)


def skill_tool(skill_dir: Path) -> Tool:
    """SKILL.md as an on-demand instruction tool: the subagent pulls the skill body
    when its description says it applies (progressive disclosure, like Claude skills)."""
    text = (Path(skill_dir) / "SKILL.md").read_text()
    fm = yaml.safe_load(text[4:].split("\n---\n", 1)[0]) if text.startswith("---\n") else {}
    name, desc = fm.get("name", Path(skill_dir).name), fm.get("description", "")
    body = text.split("\n---\n", 1)[1] if "\n---\n" in text else text

    def _read() -> str:
        return body

    _read.__name__ = f"skill_{name.replace('-', '_')}"
    return Tool(_read, name=_read.__name__, takes_ctx=False,
                description=f"[skill {name}] {desc}")


class HttpResult(BaseModel):
    status: int
    headers: dict[str, str]
    body: str = ""  # empty for HEAD by contract


def openapi_endpoint_tools(spec: OpenAPIToolsSpec) -> list[Tool]:
    """One tool per OpenAPI operation (REST/CRUD verbs). Safe methods by default;
    mutating verbs are explicit opt-in — consequential actions never sneak in."""
    import os
    raw = Path(spec.spec_path).read_text()
    doc = json.loads(raw) if spec.spec_path.endswith(".json") else yaml.safe_load(raw)
    allow = {m.upper() for m in spec.allow_methods} & ALL_METHODS
    tools: list[Tool] = []
    for path, ops in (doc.get("paths") or {}).items():
        for method, op in ops.items():
            m = method.upper()
            if m not in allow or not isinstance(op, dict):
                continue
            op_id = op.get("operationId") or f"{method}_{path}".replace("/", "_")

            def _call(path_params: dict[str, str] | None = None,
                      query: dict[str, str] | None = None,
                      body_json: str = "",
                      _m=m, _path=path) -> HttpResult:
                url_path = _path
                for k, v in (path_params or {}).items():
                    url_path = url_path.replace("{" + k + "}", urllib.parse.quote(str(v), safe=""))
                url = spec.base_url.rstrip("/") + url_path
                if query:
                    url += "?" + urllib.parse.urlencode(query)
                req = urllib.request.Request(url, method=_m,
                                             data=body_json.encode() if body_json else None)
                if body_json:
                    req.add_header("Content-Type", "application/json")
                if spec.bearer_token_env and os.environ.get(spec.bearer_token_env):
                    req.add_header("Authorization", "Bearer " + os.environ[spec.bearer_token_env])
                try:
                    with urllib.request.urlopen(req, timeout=30) as r:
                        body = "" if _m == "HEAD" else r.read(200_000).decode("utf-8", "replace")
                        return HttpResult(status=r.status, headers=dict(r.headers), body=body)
                except urllib.error.HTTPError as e:
                    return HttpResult(status=e.code, headers=dict(e.headers or {}),
                                      body=(e.read() or b"")[:4000].decode("utf-8", "replace"))

            tname = f"api_{op_id}".replace("-", "_")[:64]
            _call.__name__ = tname
            desc = f"[{m} {path}] " + (op.get("summary") or op.get("description") or op_id)
            tools.append(Tool(_call, name=tname, description=desc, takes_ctx=False))
    return tools


def openapi_kb_tool(registry_path: Path) -> Tool:
    """Search the openapi.tools knowledge base (195 tools) by category/use-case/tag/language."""
    kb = json.loads(Path(registry_path).read_text())["tools"]

    def search_openapi_tools(query: str = "", category: str = "", use_case: str = "",
                             language: str = "", limit: int = 10) -> list[dict]:
        q = query.lower()
        out = []
        for t in kb:
            if category and category.lower() not in (t.get("primary_category", "") + " "
                                                     + t.get("secondary_category", "")).lower():
                continue
            if use_case and use_case not in t.get("use_cases", []):
                continue
            if language and language.lower() not in [l.lower() for l in t.get("languages", [])]:
                continue
            hay = json.dumps(t).lower()
            if q and q not in hay:
                continue
            out.append({k: t.get(k) for k in ("slug", "name", "primary_category",
                                              "use_cases", "languages", "type", "website")})
            if len(out) >= limit:
                break
        return out

    return Tool(search_openapi_tools, name="search_openapi_tools", takes_ctx=False,
                description="Search the openapi.tools registry (195 tools) by free text, "
                            "category, use_case, or language. Returns candidates for toolchain decisions.")


# ---------------------------------------------------------------- factory

def build_subagent(spec: SubAgentSpec, model: Any, *, mcp_toolsets: list | None = None) -> Agent:
    """Ephemeral subagent per Claude-Code doctrine: constructed per task, discarded after.
    mcp_toolsets: pydantic-ai MCP toolsets (e.g. MCPServerStdio) passed through untouched."""
    tools: list[Tool] = []
    tools += [cli_tool(c) for c in spec.cli_tools]
    tools += [skill_tool(Path(s)) for s in spec.skills]
    if spec.openapi:
        tools += openapi_endpoint_tools(spec.openapi)
    if spec.openapi_kb_path:
        tools.append(openapi_kb_tool(Path(spec.openapi_kb_path)))
    tools += [job_tool(Path(d)) for d in spec.job_dirs]
    tools += [audit_tool(Path(t), model, root=Path(spec.audit_root))
              for t in spec.audit_templates]
    parts = [f"You are the '{spec.name}' subagent. Purpose: {spec.purpose}"]
    if spec.taxonomy:
        parts.append(f"Taxonomy scope: {spec.taxonomy.path()} — stay within it.")
    parts += spec.instructions
    return Agent(model, tools=tools, instructions="\n\n".join(parts),
                 toolsets=mcp_toolsets or [], name=f"subagent_{spec.name}")


def subagent_tool(spec: SubAgentSpec, model: Any) -> Tool:
    """Subagent-as-tool for the parent harness (the audits.py pattern, generalized)."""
    limits = UsageLimits(request_limit=spec.request_limit)

    async def _run(task: str) -> str:
        agent = build_subagent(spec, model)  # ephemeral
        result = await agent.run(task, usage_limits=limits)
        return str(result.output)

    _run.__name__ = f"subagent_{spec.name.replace('-', '_')}"
    return Tool(_run, name=_run.__name__, takes_ctx=False,
                description=f"[subagent {spec.name}] {spec.purpose}"
                            + (f" Scope: {spec.taxonomy.path()}." if spec.taxonomy else ""))


def taxonomy_subagents(rows: list[dict], defaults: dict | None = None) -> list[SubAgentSpec]:
    """master_mapped_taxonomy.md rows -> SubAgentSpecs. Requires the real taxonomy
    rows as input — this function maps, it does not invent industries or tasks."""
    specs = []
    for row in rows:
        tax = Taxonomy.model_validate({k: row.get(k, "") for k in
                                       ("industry", "domain", "service", "niche", "task")})
        specs.append(SubAgentSpec.model_validate({
            "name": tax.path().replace("/", "-")[:60].rstrip("-"),
            "purpose": row.get("purpose") or f"Execute {tax.task or tax.service} work in {tax.path()}.",
            "taxonomy": tax.model_dump(), **(defaults or {})}))
    return specs
