"""True e2e: real Go control-plane binary + real Python worker + HTTP round-trip.
Proves: auth enforced, job lifecycle queued->running->succeeded, artifacts +
ValidationReports retrievable, SSE terminal event emitted."""
import json
import os
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from utag_worker.worker import ControlPlane, loop

BIN = Path(__file__).parents[2] / "control-plane" / "utag-control-plane"
FIXTURE = Path(__file__).parents[2] / "fixtures" / "prompts" / "normalize-tool.prompt.yaml"
TOKEN = "test-token-123"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    if not BIN.exists():
        pytest.skip("control-plane binary not built")
    port = _free_port()
    env = {**os.environ, "UTAG_PORT": str(port), "UTAG_API_TOKEN": TOKEN}
    proc = subprocess.Popen([str(BIN), "serve"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("control-plane did not become healthy")
    yield base
    proc.terminate()


def test_auth_required(server):
    with pytest.raises(urllib.error.HTTPError) as ei:
        ControlPlane(server, token="wrong").claim()
    assert ei.value.code == 401


def test_full_job_lifecycle_with_worker(server):
    cp = ControlPlane(server, token=TOKEN)
    job = cp._req("POST", "/v1/jobs", {
        "target": "pydantic-models", "backend": "none",
        "input_kind": "prompt-yaml", "input": FIXTURE.read_text()})
    assert job["status"] == "queued"
    t = threading.Thread(target=loop, args=(cp,), kwargs={"poll_seconds": 0.1, "max_jobs": 1})
    t.start(); t.join(timeout=30)
    assert not t.is_alive()
    final = cp._req("GET", f"/v1/jobs/{job['id']}")
    assert final["status"] == "succeeded", final
    arts = cp._req("GET", f"/v1/jobs/{job['id']}/artifacts")
    assert arts and arts[0]["path"].endswith(".py")
    report = json.loads(arts[0]["report"])
    assert report["valid"] is True
    one = cp._req("GET", f"/v1/artifacts/{arts[0]['id']}")
    assert "class NormalizeToolInput" in one["content"]


def test_failed_job_surfaces_error(server):
    cp = ControlPlane(server, token=TOKEN)
    job = cp._req("POST", "/v1/jobs", {"target": "no-such-target",
                  "input_kind": "prompt-yaml", "input": FIXTURE.read_text()})
    loop(cp, poll_seconds=0.05, max_jobs=1)
    final = cp._req("GET", f"/v1/jobs/{job['id']}")
    assert final["status"] == "failed" and "no generator registered" in final["error"]


def test_sse_stream_reaches_terminal_event(server):
    cp = ControlPlane(server, token=TOKEN)
    job = cp._req("POST", "/v1/jobs", {"target": "agent-skill",
                  "input_kind": "prompt-yaml", "input": FIXTURE.read_text()})
    threading.Thread(target=loop, args=(cp,), kwargs={"poll_seconds": 0.05, "max_jobs": 1}).start()
    req = urllib.request.Request(f"{server}/v1/jobs/{job['id']}/events",
                                 headers={"Authorization": f"Bearer {TOKEN}"})
    events = []
    with urllib.request.urlopen(req, timeout=20) as r:
        for raw in r:
            line = raw.decode().strip()
            if line.startswith("event: "):
                events.append(line.removeprefix("event: "))
    assert events[0] == "queued" and events[-1] == "succeeded", events
