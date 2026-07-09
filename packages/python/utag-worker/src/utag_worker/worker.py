"""utag-worker: claims jobs from the control-plane over HTTP, runs
ingest -> generate -> validate through the existing registries, posts results.

stdlib-only HTTP (urllib) — zero extra deps. Twelve-factor config via env:
UTAG_CONTROL_PLANE_URL, UTAG_API_TOKEN, UTAG_POLL_SECONDS.
Terminal vs repairable: generation exceptions fail the job with the error
surfaced; per-artifact validation failures are reported, never hidden.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

import utag_generators  # noqa: F401  registers generators + validators
from utag_core.registry import get_generator, get_validator
from utag_generators.ingest import ingest_json_record, ingest_prompt_yaml

TARGET_VALIDATOR = {
    "pydantic-models": "python-source", "zod-schemas": "typescript",
    "agent-skill": "skill-md", "prompt-yaml": "yaml", "openapi-3.1": "openapi-3.1",
    "design-md": "design-md", "generator": "python-source", "go-harness": "go-source",
}


class ControlPlane:
    def __init__(self, base: str, token: str = ""):
        self.base, self.token = base.rstrip("/"), token

    def _req(self, method: str, path: str, body: dict | None = None):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status == 204:
                return None
            return json.loads(r.read() or b"{}")

    def claim(self) -> dict | None:
        return self._req("POST", "/v1/worker/claim", {})

    def complete(self, job_id: str, status: str, error: str = "",
                 artifacts: list[dict] | None = None) -> None:
        self._req("POST", f"/v1/jobs/{job_id}/complete",
                  {"status": status, "error": error, "artifacts": artifacts or []})


def run_job(job: dict) -> tuple[str, str, list[dict]]:
    """-> (status, error, artifacts). Pure function of the job payload."""
    try:
        kind = job.get("input_kind", "prompt-yaml")
        if kind == "prompt-yaml":
            module = ingest_prompt_yaml(job["input"], f"job:{job['id']}")
        elif kind == "json-record":
            module = ingest_json_record(job["input"], "Record", f"job:{job['id']}")
        elif kind == "ir-json":
            from utag_core.ir import ModuleSpec
            module = ModuleSpec.model_validate_json(job["input"])
        else:
            return "failed", f"unsupported input_kind: {kind}", []
        gen = get_generator(job["target"])
        vkind = TARGET_VALIDATOR.get(job["target"])
        artifacts, any_invalid = [], False
        for rel, content in sorted(gen.generate(module).items()):
            report = get_validator(vkind)(rel, content) if vkind else None
            if report is not None and not report.valid:
                any_invalid = True
            artifacts.append({"path": rel, "content": content,
                              "report": report.to_json() if report else ""})
        if any_invalid:
            return "failed", "one or more artifacts failed validation (see reports)", artifacts
        return "succeeded", "", artifacts
    except Exception as exc:  # terminal for this job; loop survives
        return "failed", f"{type(exc).__name__}: {exc}", []


def loop(cp: ControlPlane, poll_seconds: float = 1.0, max_jobs: int | None = None) -> int:
    done = 0
    while max_jobs is None or done < max_jobs:
        try:
            job = cp.claim()
        except urllib.error.URLError:
            time.sleep(poll_seconds)
            continue
        if job is None:
            time.sleep(poll_seconds)
            continue
        status, error, artifacts = run_job(job)
        cp.complete(job["id"], status, error, artifacts)
        done += 1
    return done


def main() -> int:
    cp = ControlPlane(os.environ.get("UTAG_CONTROL_PLANE_URL", "http://127.0.0.1:8080"),
                      os.environ.get("UTAG_API_TOKEN", ""))
    loop(cp, float(os.environ.get("UTAG_POLL_SECONDS", "1")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
