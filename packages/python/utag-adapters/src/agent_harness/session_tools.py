"""Generation + orchestration tools for the session: talk to utag and it makes
things — locally (registries, instant, validated) or via the control-plane
(jobs, observable, PR-deliverable). Config (~/.utag/config.yaml):
  control_plane_url / api_token   -> enables submit_job/job_status/list_jobs
  forge_jobs_root / audit_kit_dir -> mounts harness_tools() into the session
Every tool returns structured, honest results — validation verdicts included.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Tool

from .home import UtagHome


class GeneratedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    valid: bool | None = None
    validator_id: str = ""
    findings: list[str] = Field(default_factory=list)


class GenerateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    target: str
    out_dir: str = ""
    artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    error: str = ""


_TARGET_VALIDATOR = {
    "pydantic-models": "python-source", "zod-schemas": "typescript",
    "agent-skill": "skill-md", "prompt-yaml": "yaml", "openapi-3.1": "openapi-3.1",
    "design-md": "design-md", "go-harness": "go-source",
    "udc-design-md": "design-md", "udc-component": "typescript",
    "taxonomy-skill": "skill-md",
}


def _local_generate(target: str, input_path: str, out_dir: str) -> GenerateResult:
    import utag_generators  # noqa: F401
    from utag_core.registry import GENERATORS, get_generator, get_validator
    from utag_generators.ingest import ingest_prompt_yaml

    if target not in GENERATORS:
        return GenerateResult(ok=False, target=target,
                              error=f"unknown target; known: {sorted(GENERATORS)}")
    src = Path(input_path)
    if not src.is_file():
        return GenerateResult(ok=False, target=target, error=f"no such input file: {src}")
    if target == "taxonomy-skill":
        from utag_core.ir import ModuleSpec
        module = ModuleSpec(name=src.stem.replace("-", "_"),
                            provenance={"taxonomy_md": src.read_text()})
    else:
        module = ingest_prompt_yaml(src.read_text(), str(src))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    arts, ok = [], True
    vkind = _TARGET_VALIDATOR.get(target)
    for rel, content in sorted(get_generator(target).generate(module).items()):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        art = GeneratedArtifact(path=str(p))
        if vkind:
            r = get_validator(vkind)(str(p), content)
            art.valid, art.validator_id = r.valid, r.validator_id
            art.findings = [f"{f.severity.value}: {f.message}" for f in r.findings][:5]
            ok = ok and r.valid
        arts.append(art)
    return GenerateResult(ok=ok, target=target, out_dir=str(out), artifacts=arts)


def generation_tools(home: UtagHome, cp=None, out_dir: str = "out") -> list[Tool]:
    """cp: utag_worker.worker.ControlPlane or None (local-only)."""
    tools: list[Tool] = []

    def list_targets() -> list[str]:
        import utag_generators  # noqa: F401
        from utag_core.registry import GENERATORS
        return sorted(GENERATORS)

    def generate_artifact(target: str, input_path: str) -> GenerateResult:
        """Generate + validate locally, right now. Returns per-artifact verdicts."""
        return _local_generate(target, input_path, out_dir)

    tools.append(Tool(list_targets, name="list_targets", takes_ctx=False,
                      description="List every registered generator target."))
    tools.append(Tool(generate_artifact, name="generate_artifact", takes_ctx=False,
                      description="Generate typed artifacts from a prompt-yaml (or taxonomy) "
                                  "file into the workspace, validated. Instant, local."))
    if cp is not None:
        def submit_job(target: str, input_path: str) -> dict:
            """Queue on the control-plane (async, observable, PR-deliverable)."""
            p = Path(input_path)
            if not p.is_file():
                return {"error": f"no such input file: {p}"}
            j = cp._req("POST", "/v1/jobs", {"target": target, "backend": "session",
                                             "input_kind": "prompt-yaml", "input": p.read_text()})
            return {"job_id": j["id"], "status": j["status"]}

        def job_status(job_id: str) -> dict:
            j = cp._req("GET", f"/v1/jobs/{job_id}")
            return {k: j.get(k) for k in ("id", "target", "status", "error")}

        def list_jobs(limit: int = 10) -> list[dict]:
            jobs = cp._req("GET", f"/v1/jobs?limit={max(1, min(limit, 100))}") or []
            return [{k: j.get(k) for k in ("id", "target", "status")} for j in jobs]

        tools += [Tool(submit_job, name="submit_job", takes_ctx=False,
                       description="Queue a generation job on the control-plane."),
                  Tool(job_status, name="job_status", takes_ctx=False,
                       description="Check a control-plane job by id."),
                  Tool(list_jobs, name="list_jobs", takes_ctx=False,
                       description="List recent control-plane jobs.")]
    return tools


def session_toolset(home: UtagHome, out_dir: str = "out", model=None):
    """Everything the session mounts, driven by config: generation tools, optional
    control-plane tools, optional harness_tools (jobs/audits). Returns (tools, cp)."""
    cfg = home.config()
    cp = None
    if cfg.get("control_plane_url"):
        from utag_worker.worker import ControlPlane
        cp = ControlPlane(cfg["control_plane_url"], cfg.get("api_token", ""))
    tools = generation_tools(home, cp=cp, out_dir=cfg.get("out_dir", out_dir))
    try:
        from .veriforge_bridge import veriforge_tools
        tools += veriforge_tools(model=model)
    except Exception:
        pass  # utag-veriforge not installed: session boots without pipeline tools
    if cfg.get("forge_jobs_root") or cfg.get("audit_kit_dir"):
        from .registry import harness_tools
        kw = {}
        if cfg.get("forge_jobs_root"):
            kw["jobs_root"] = Path(cfg["forge_jobs_root"])
        if cfg.get("audit_kit_dir"):
            kw["audit_dir"] = Path(cfg["audit_kit_dir"])
            kw["audit_model"] = "test"  # replaced by real model at session build when used
        try:
            tools += harness_tools(**kw)
        except Exception:
            pass  # kit paths misconfigured: session still boots; /help explains
    return tools, cp
