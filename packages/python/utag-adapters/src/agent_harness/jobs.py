"""forge-jobs manifest -> Pydantic AI Tool.

Mirrors schema/job.schema.json 1:1 (extra='forbid' == additionalProperties:false).
Tool behavior mirrors the kit's own guarantees: fail-fast preflight with honest
skip reasons (never fake success), manifest timeout respected, report located at
the lib.sh contract path FJ_STATE/output/<id>/<date>/report.md.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Tool

_ENV_NAME = r"^[A-Z][A-Z0-9_]*$"


class Schedule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    on_calendar: str = Field(min_length=1)
    enabled: bool


class RunSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str = Field(pattern=r"^scripts/")
    cwd: str | None = None
    timeout_seconds: int = Field(ge=10, le=86400)


class EnvSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    required: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)

    def model_post_init(self, __context) -> None:
        for name in self.required + self.optional:
            if not re.match(_ENV_NAME, name):
                raise ValueError(f"invalid env var name: {name!r}")


class Requires(BaseModel):
    model_config = ConfigDict(extra="forbid")
    commands: list[str]
    os: str | None = None


class JobManifest(BaseModel):
    """1:1 with forge-jobs schema/job.schema.json."""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str = Field(min_length=1)
    description: str = Field(min_length=10)
    category: str = Field(pattern=r"^[a-z0-9-]+$")
    tags: list[str] = Field(default_factory=list)
    schedule: Schedule
    run: RunSpec
    concurrency: Literal["forbid", "allow"] = "forbid"
    env: EnvSpec
    requires: Requires
    outputs: list[str] = Field(default_factory=list)


class JobResult(BaseModel):
    """Structured tool return. skipped_reason set => job never ran (honest fail-fast)."""
    job_id: str
    status: Literal["ok", "failed", "skipped", "timeout"]
    exit_code: int | None = None
    duration_seconds: float | None = None
    skipped_reason: str | None = None
    report_path: str | None = None
    report_text: str | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""


def load_manifest(job_dir: Path) -> JobManifest:
    return JobManifest.model_validate(yaml.safe_load((job_dir / "job.yaml").read_text()))


def _tail(s: str, n: int = 2000) -> str:
    return s[-n:]


def _preflight(m: JobManifest, env: dict[str, str]) -> str | None:
    missing_cmds = [c for c in m.requires.commands if shutil.which(c, path=env.get("PATH", os.defpath)) is None]
    if missing_cmds:
        return f"missing required commands: {', '.join(missing_cmds)} (apt hint per kit README)"
    missing_env = [v for v in m.env.required if not env.get(v)]
    if missing_env:
        return f"missing required env: {', '.join(missing_env)} — set in ~/.config/forge-cc/forge.env"
    return None


def _report_path(m: JobManifest, env: dict[str, str]) -> Path:
    # lib.sh contract: FJ_STATE="${FORGE_JOBS_STATE:-$HOME/.local/share/forge-jobs}"
    #                  REPORT="$FJ_STATE/output/$JOB_ID/$(date +%F)/report.md"
    state = env.get("FORGE_JOBS_STATE") or str(Path.home() / ".local/share/forge-jobs")
    return Path(state).expanduser() / "output" / m.id / date.today().isoformat() / "report.md"


def run_job(job_dir: Path, manifest: JobManifest | None = None,
            env_overrides: dict[str, str] | None = None,
            include_report_text: bool = True) -> JobResult:
    """Execute one forge-job synchronously. Never raises on job failure — returns structured status."""
    job_dir = job_dir.resolve()
    m = manifest or load_manifest(job_dir)
    env = {**os.environ, **(env_overrides or {})}

    if reason := _preflight(m, env):
        return JobResult(job_id=m.id, status="skipped", skipped_reason=reason)

    script = (job_dir / m.run.command).resolve()
    if not script.is_relative_to(job_dir):  # manifest pattern ^scripts/ enforces this; defense in depth
        return JobResult(job_id=m.id, status="skipped", skipped_reason=f"script escapes job dir: {script}")
    if not script.is_file():
        return JobResult(job_id=m.id, status="skipped", skipped_reason=f"script not found: {script}")

    cwd = (job_dir / m.run.cwd).resolve() if m.run.cwd else job_dir
    start = time.monotonic()
    try:
        proc = subprocess.run(
            ["bash", str(script)], cwd=str(cwd), env=env,
            capture_output=True, text=True, timeout=m.run.timeout_seconds,
        )
        status: Literal["ok", "failed"] = "ok" if proc.returncode == 0 else "failed"
        exit_code, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        elapsed = time.monotonic() - start
        return JobResult(job_id=m.id, status="timeout", duration_seconds=round(elapsed, 2),
                         stdout_tail=_tail(e.stdout or ""), stderr_tail=_tail(e.stderr or ""))
    elapsed = time.monotonic() - start

    rp = _report_path(m, env)
    report_text = None
    if include_report_text and rp.is_file():
        report_text = rp.read_text(errors="replace")[:20_000]

    return JobResult(
        job_id=m.id, status=status, exit_code=exit_code,
        duration_seconds=round(elapsed, 2),
        report_path=str(rp) if rp.is_file() else None,
        report_text=report_text,
        stdout_tail=_tail(out), stderr_tail=_tail(err),
    )


def job_tool(job_dir: Path, env_overrides: dict[str, str] | None = None) -> Tool:
    """Wrap one forge-job as a Pydantic AI Tool. Name: job_<id> (dashes -> underscores)."""
    job_dir = Path(job_dir).resolve()
    m = load_manifest(job_dir)

    def _run() -> JobResult:
        return run_job(job_dir, m, env_overrides)

    _run.__name__ = f"job_{m.id.replace('-', '_')}"
    desc = f"[forge-job {m.category}/{m.id}] {m.description}"
    if m.env.required:
        desc += f" Requires env: {', '.join(m.env.required)}."
    return Tool(_run, name=_run.__name__, description=desc, takes_ctx=False)
