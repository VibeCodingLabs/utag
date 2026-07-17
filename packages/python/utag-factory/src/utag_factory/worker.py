"""Worker: claim jobs from the stream, execute typed job kinds in a sandbox,
retry per the template taxonomy, dead-letter what's exhausted, and record
run evidence both to the observe store and the `utag:events` firehose.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from utag_core.observe import Recorder
from utag_core.schemas.factory import (
    DeadLetterEntry, FactoryJob, JobKind, JobStatus, ResourceContract,
)

from utag_factory.config import FactoryConfig
from utag_factory.queue import Message, StreamQueue, backoff_s, classify_exception, is_retryable
from utag_factory.sandbox import pick_sandbox
from utag_factory.store import JobStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class JobError(Exception):
    """Raised by kind handlers when the job itself failed (non-zero exit etc.)."""


def _kind_run_python(payload: dict, job: FactoryJob, worker: "Worker") -> dict:
    script = payload.get("script")
    if not isinstance(script, str) or not script.strip():
        raise ValueError("run-python payload needs a non-empty `script` (schema_invalid)")
    with tempfile.TemporaryDirectory(prefix=f"utag-{job.id}-") as td:
        workdir = Path(td)
        (workdir / "script.py").write_text(script)
        # system python3 via the sandbox's scrubbed PATH — the venv under /home
        # is deliberately invisible inside bwrap
        result = worker.sandbox.run(workdir, ["python3", "script.py"], job.resources)
    if result.timed_out:
        raise TimeoutError(f"job {job.id} exceeded {job.resources.max_wall_time_s}s")
    if result.exit_code != 0:
        raise JobError(f"exit {result.exit_code}: {result.stderr[-500:]}")
    return {"stdout": result.stdout, "stderr": result.stderr,
            "duration_ms": result.duration_ms, "truncated": result.truncated,
            "isolation": worker.sandbox.isolation.value}


def _kind_generate_artifact(payload: dict, job: FactoryJob, worker: "Worker") -> dict:
    import utag_generators  # noqa: F401  registers everything
    from utag_core.registry import get_generator
    from utag_generators.ingest import ingest_prompt_yaml

    target = payload.get("target")
    source = payload.get("prompt_yaml")
    if not target or not source:
        raise ValueError("generate-artifact payload needs `target` and `prompt_yaml` (schema_invalid)")
    module = ingest_prompt_yaml(source, f"job:{job.id}")
    files = get_generator(target).generate(module)
    out_dir = worker.cfg.data_dir() / "artifacts" / job.id
    digests = {}
    for rel, content in sorted(files.items()):
        p = out_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        digests[rel] = hashlib.sha256(content.encode()).hexdigest()
    return {"artifact_dir": str(out_dir), "files": digests}


KIND_HANDLERS = {
    JobKind.run_python: _kind_run_python,
    JobKind.generate_artifact: _kind_generate_artifact,
}


class Worker:
    def __init__(self, cfg: FactoryConfig, store: JobStore, queue: StreamQueue,
                 name: str = "worker-1"):
        self.cfg = cfg
        self.store = store
        self.queue = queue
        self.name = name
        self.sandbox = pick_sandbox(cfg.profile.execution)

    # -- public API -------------------------------------------------------------
    def submit(self, kind: JobKind, payload: dict,
               resources: ResourceContract | None = None) -> FactoryJob:
        job_id = f"job-{hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]}"
        ref, sha = self.store.put_payload(job_id, payload)
        job = FactoryJob(id=job_id, kind=kind, status=JobStatus.queued,
                         payload_ref=ref, payload_sha256=sha,
                         resources=resources or _default_resources(),
                         isolation=self.sandbox.isolation,
                         max_attempts=self.cfg.profile.retries.maximum_attempts,
                         created_at=_now_iso(), updated_at=_now_iso())
        self.store.put(job)
        self.queue.enqueue(self.cfg.streams.jobs, {"job_id": job.id, "payload_ref": ref})
        self._event(job, "utag.job.queued")
        return job

    def run_once(self, block_ms: int = 10) -> FactoryJob | None:
        messages = self.queue.claim(block_ms=block_ms) or self.queue.reclaim()
        if not messages:
            return None
        return self._process(messages[0])

    # -- internals ---------------------------------------------------------------
    def _process(self, msg: Message) -> FactoryJob:
        not_before = float(msg.fields.get("not_before", 0))
        if time.time() < not_before:  # backoff not elapsed: requeue untouched
            self.queue.enqueue(msg.stream, msg.fields)
            self.queue.ack(msg)
            return self.store.get(msg.fields["job_id"])
        job = self.store.get(msg.fields["job_id"])
        rec = Recorder()
        job = self.store.transition(job.id, JobStatus.running, worker=self.name,
                                    run_id=rec.run_id, attempts=job.attempts + 1)
        rec.event("utag.worker.claim", job_id=job.id, worker=self.name,
                  attempt=str(job.attempts))
        try:
            with rec.span("utag.run", job_id=job.id, kind=job.kind.value):
                payload = self.store.get_payload(job.payload_ref)
                result = KIND_HANDLERS[job.kind](payload, job, self)
        except Exception as exc:  # noqa: BLE001 — classified below, never swallowed
            return self._handle_failure(msg, job, rec, exc)
        self.store.put_result(job.id, result)
        job = self.store.transition(job.id, JobStatus.succeeded)
        rec.metric("utag_runs_total", 1, kind=job.kind.value)
        rec.event("utag.worker.complete", job_id=job.id, status="succeeded")
        self._flush(job, rec, "succeeded")
        self.queue.ack(msg)
        return job

    def _handle_failure(self, msg: Message, job: FactoryJob, rec: Recorder,
                        exc: Exception) -> FactoryJob:
        failure = classify_exception(exc)
        fingerprint = f"{failure.value}:{job.kind.value}:{type(exc).__name__}"
        policy = self.cfg.profile.retries
        rec.metric("utag_validation_failures_total", 1, kind=job.kind.value)
        rec.event("utag.worker.complete", job_id=job.id, status="failed",
                  failure=failure.value)
        if is_retryable(failure, policy) and job.attempts < job.max_attempts:
            delay = backoff_s(job.attempts, policy)
            fields = dict(msg.fields)
            fields["not_before"] = str(time.time() + delay)
            self.queue.enqueue(msg.stream, fields)
            self.queue.ack(msg)
            job = self.store.transition(job.id, JobStatus.queued,
                                        failure_class=failure,
                                        failure_fingerprint=fingerprint)
            self._flush(job, rec, "retrying")
            return job
        entry = DeadLetterEntry(
            original_job_pointer=job.payload_ref, attempts=job.attempts,
            failure_class=failure, failure_fingerprint=fingerprint,
            execution_trace_ref=rec.run_id, provider_history=[self.name],
            resource_usage={"attempts": float(job.attempts)})
        self.queue.dead_letter(msg, entry)
        job = self.store.transition(job.id, JobStatus.dead_letter,
                                    failure_class=failure,
                                    failure_fingerprint=fingerprint)
        self._flush(job, rec, "dead-letter")
        return job

    def _event(self, job: FactoryJob, name: str) -> None:
        self.queue.publish_event({"name": name, "job_id": job.id,
                                  "kind": job.kind.value, "status": job.status.value,
                                  "at": _now_iso()})

    def _flush(self, job: FactoryJob, rec: Recorder, outcome: str) -> None:
        rec.flush()
        self.queue.publish_event({"name": "utag.job.finished", "job_id": job.id,
                                  "kind": job.kind.value, "status": job.status.value,
                                  "outcome": outcome, "run_id": rec.run_id,
                                  "at": _now_iso()})


def _default_resources() -> ResourceContract:
    return ResourceContract(max_memory_bytes=1024**3, max_wall_time_s=900,
                            max_output_bytes=1024**2)
