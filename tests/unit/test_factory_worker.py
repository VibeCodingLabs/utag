"""F2: sandboxes + worker loop — real execution, honest retries, DLQ, evidence."""
from __future__ import annotations

from pathlib import Path

import fakeredis
import pytest

from utag_core.schemas.factory import JobKind, JobStatus, ResourceContract
from utag_factory.config import load_config
from utag_factory.queue import StreamQueue
from utag_factory.sandbox import BwrapSandbox, ProcessSandbox, bwrap_available, pick_sandbox
from utag_factory.store import JobStore
from utag_factory.worker import Worker

ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT)
FAST = ResourceContract(max_memory_bytes=512 * 1024**2, max_wall_time_s=5,
                        max_output_bytes=64 * 1024)


@pytest.fixture()
def worker(tmp_path, monkeypatch):
    monkeypatch.setenv("UTAG_FACTORY_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("UTAG_OBSERVE_DIR", str(tmp_path / "observe"))
    queue = StreamQueue(fakeredis.FakeRedis(), CFG.profile.queue, consumer_name="t-1")
    queue.ensure_groups()
    return Worker(load_config(ROOT), JobStore(tmp_path / "jobs.db"), queue, name="t-1")


def test_run_python_succeeds_with_evidence(worker, tmp_path):
    job = worker.submit(JobKind.run_python, {"script": "print('hello from sandbox')"},
                        resources=FAST)
    done = worker.run_once()
    assert done.id == job.id and done.status == JobStatus.succeeded
    result = worker.store.get_result(job.id)
    assert result["stdout"].strip() == "hello from sandbox"
    assert result["isolation"] in ("bwrap", "process")
    evidence = list((tmp_path / "observe").glob("*.jsonl"))
    assert evidence and "utag.worker.claim" in evidence[0].read_text()
    events = worker.queue.r.xrange(CFG.streams.events)
    names = [dict((k.decode(), v.decode()) for k, v in f.items())["name"] for _i, f in events]
    assert names == ["utag.job.queued", "utag.job.finished"]


def test_failing_script_retries_then_dead_letters(worker):
    job = worker.submit(JobKind.run_python, {"script": "import sys; sys.exit(3)"},
                        resources=FAST)
    # exit-code failures classify as deterministic -> terminal on first attempt
    done = worker.run_once()
    assert done.status == JobStatus.dead_letter
    (entry,) = worker.queue.dead_letters()
    assert entry.original_job_pointer == f"payload:{job.id}"
    assert entry.failure_class.value == "deterministic_failure_repeated"
    assert worker.queue.pending() == 0


def test_timeout_is_retryable_until_exhausted(worker):
    slow = ResourceContract(max_memory_bytes=512 * 1024**2, max_wall_time_s=1,
                            max_output_bytes=64 * 1024)
    job = worker.submit(JobKind.run_python,
                        {"script": "import time; time.sleep(30)"}, resources=slow)
    statuses = []
    for _ in range(20):  # drain including backoff requeues
        done = worker.run_once(block_ms=1)
        if done is None:
            continue
        statuses.append(done.status)
        if done.status == JobStatus.dead_letter:
            break
        # collapse the backoff so the test doesn't sleep
        for mid, fields in worker.queue.r.xrange(CFG.streams.jobs):
            if b"not_before" in fields:
                worker.queue.r.xdel(CFG.streams.jobs, mid)
                f = {k.decode(): v.decode() for k, v in fields.items()}
                f["not_before"] = "0"
                worker.queue.enqueue(CFG.streams.jobs, f)
    final = worker.store.get(job.id)
    assert final.status == JobStatus.dead_letter
    assert final.attempts == CFG.profile.retries.maximum_attempts
    assert final.failure_class.value == "provider_timeout"


def test_generate_artifact_kind_writes_validated_files(worker):
    prompt = (ROOT / "fixtures/prompts/categorize-file.prompt.yaml").read_text()
    job = worker.submit(JobKind.generate_artifact,
                        {"target": "pydantic-models", "prompt_yaml": prompt},
                        resources=FAST)
    done = worker.run_once()
    assert done.status == JobStatus.succeeded
    result = worker.store.get_result(job.id)
    assert result["files"], "no artifacts produced"
    first = next(iter(result["files"]))
    assert (Path(result["artifact_dir"]) / first).is_file()


def test_invalid_payload_is_terminal(worker):
    worker.submit(JobKind.run_python, {"script": ""}, resources=FAST)
    done = worker.run_once()
    assert done.status == JobStatus.dead_letter          # schema_invalid: never retried
    assert done.failure_class.value == "schema_invalid"


def test_pick_sandbox_prefers_bwrap():
    sandbox = pick_sandbox(CFG.profile.execution)
    expected = BwrapSandbox if bwrap_available() else ProcessSandbox
    assert isinstance(sandbox, expected)


@pytest.mark.skipif(not bwrap_available(), reason="bwrap unavailable")
def test_bwrap_blocks_home_and_network(tmp_path):
    sandbox = BwrapSandbox()
    script = tmp_path / "script.py"
    script.write_text(
        "import os, socket\n"
        "print('home_visible', os.path.exists(os.path.expanduser('~/.bashrc'))"
        " or os.path.exists('/home'))\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=1)\n"
        "    print('network', 'up')\n"
        "except OSError:\n"
        "    print('network', 'down')\n")
    result = sandbox.run(tmp_path, ["python3", "script.py"], FAST)
    assert result.exit_code == 0, result.stderr
    assert "home_visible False" in result.stdout
    assert "network down" in result.stdout


def test_process_sandbox_output_cap(tmp_path):
    tiny = ResourceContract(max_memory_bytes=512 * 1024**2, max_wall_time_s=5,
                            max_output_bytes=100)
    script = tmp_path / "script.py"
    script.write_text("print('x' * 10000)")
    result = ProcessSandbox().run(tmp_path, ["python3", "script.py"], tiny)
    assert result.truncated and len(result.stdout) <= 100
