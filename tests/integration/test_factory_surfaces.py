"""F4/F5: NL→job agent + Typer/FastAPI/FastMCP surfaces, offline (fakeredis)."""
from __future__ import annotations

import json
from pathlib import Path

import fakeredis
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from utag_core.schemas.factory import JobKind
from utag_factory.agent import JobRequest, plan_job
from utag_factory.config import load_config
from utag_factory.queue import StreamQueue
from utag_factory.runtime import Runtime
from utag_factory.store import JobStore

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("UTAG_FACTORY_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("UTAG_OBSERVE_DIR", str(tmp_path / "obs"))
    monkeypatch.chdir(ROOT)
    cfg = load_config(ROOT)
    q = StreamQueue(fakeredis.FakeRedis(), cfg.profile.queue, "test")
    q.ensure_groups()
    return Runtime(cfg=cfg, queue=q, store=JobStore(tmp_path / "jobs.db"))


class ScriptedPort:
    """Returns a fixed JobRequest — stands in for a real planner model."""
    name = "scripted"
    last_usage = {}

    def generate(self, *, prompt, response_model, max_attempts=3, system=None):
        return JobRequest(kind=JobKind.run_python, script="print('planned')",
                          rationale="user asked to run a script")


def test_plan_job_offline_returns_valid_request(monkeypatch):
    monkeypatch.chdir(ROOT)
    req = plan_job("run a python script that prints hello", port=ScriptedPort())
    assert req.kind == JobKind.run_python
    assert req.to_payload() == {"script": "print('planned')"}


def test_plan_job_fake_port_is_valid_but_stub(monkeypatch):
    monkeypatch.chdir(ROOT)
    # default offline path routes to fake-local; the stub is a *valid* JobRequest
    req = plan_job("anything")
    assert isinstance(req, JobRequest) and req.kind in set(JobKind)


def test_fastapi_submit_inspect_and_dlq(runtime):
    from utag_factory.api import create_app
    client = TestClient(create_app(runtime))
    assert client.get("/health").json()["profile"] == "local_jetson_8gb"
    r = client.post("/jobs", json={"kind": "run-python", "payload": {"script": "print(1)"}})
    job_id = r.json()["job_id"]
    # drain it with a worker, then inspect
    runtime.worker("api").run_once(block_ms=1)
    body = client.get(f"/jobs/{job_id}").json()
    assert body["status"] == "succeeded"
    assert body["result"]["stdout"].strip() == "1"
    assert client.get("/jobs/nope").status_code == 404


def test_fastapi_sse_events_stream(runtime):
    from utag_factory.api import create_app
    client = TestClient(create_app(runtime))
    runtime.worker("api").submit(JobKind.run_python, {"script": "print(1)"})
    # follow=false drains buffered events and closes — bounded for tests
    resp = client.get("/events?last_id=0&follow=false")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "utag.job.queued" in resp.text
    payloads = [json.loads(line[len("data: "):])
                for line in resp.text.splitlines() if line.startswith("data: ")]
    assert any(p["name"] == "utag.job.queued" for p in payloads)


def test_typer_cli_submit_and_work(runtime, monkeypatch):
    from utag_factory import cli, runtime as rtmod
    monkeypatch.setattr(rtmod, "connect", lambda **kw: runtime)
    result = CliRunner().invoke(cli.app, ["submit", "--script", "print(42)"])
    assert result.exit_code == 0
    job_id = result.stdout.strip()
    work = CliRunner().invoke(cli.app, ["work", "--once"])
    assert work.exit_code == 0 and "succeeded" in work.stdout
    status = CliRunner().invoke(cli.app, ["status", job_id])
    assert '"status": "succeeded"' in status.stdout


def test_typer_doctor(runtime, monkeypatch):
    from utag_factory import cli
    monkeypatch.setattr("utag_factory.config.load_config", lambda *a, **k: runtime.cfg)
    result = CliRunner().invoke(cli.app, ["doctor"])
    assert result.exit_code == 0
    assert "supervisor: python" in result.stdout


def test_mcp_server_builds_with_tools(runtime, monkeypatch):
    from utag_factory import mcp_server, runtime as rtmod
    monkeypatch.setattr(rtmod, "connect", lambda **kw: runtime)
    server = mcp_server.build_server()
    assert server is not None  # tools registered without error
