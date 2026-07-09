"""Same e2e against the Postgres store (SKIP LOCKED queue) + parallel-claim safety.
Capability-gated on a reachable Postgres."""
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from utag_worker.worker import ControlPlane, loop

BIN = Path(__file__).parents[2] / "control-plane" / "utag-control-plane"
FIXTURE = Path(__file__).parents[2] / "fixtures" / "prompts" / "ingest-docs.prompt.yaml"
PG_URL = os.environ.get("UTAG_TEST_PG", "postgres://utag:utag@127.0.0.1:5432/utag")
TOKEN = "pg-token"


def _pg_up() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture(scope="module")
def server():
    if not BIN.exists() or not _pg_up():
        pytest.skip("binary or postgres unavailable")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    env = {**os.environ, "UTAG_PORT": str(port), "UTAG_API_TOKEN": TOKEN,
           "UTAG_DATABASE_URL": PG_URL}
    proc = subprocess.Popen([str(BIN), "serve"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1); break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill(); pytest.fail("pg-backed control-plane not healthy")
    yield base
    proc.terminate()


def test_lifecycle_on_postgres(server):
    cp = ControlPlane(server, token=TOKEN)
    job = cp._req("POST", "/v1/jobs", {"target": "openapi-3.1",
                  "input_kind": "prompt-yaml", "input": FIXTURE.read_text()})
    loop(cp, poll_seconds=0.05, max_jobs=1)
    assert cp._req("GET", f"/v1/jobs/{job['id']}")["status"] == "succeeded"


def test_skip_locked_no_double_claim(server):
    cp = ControlPlane(server, token=TOKEN)
    n = 6
    ids = [cp._req("POST", "/v1/jobs", {"target": "prompt-yaml",
           "input_kind": "prompt-yaml", "input": FIXTURE.read_text()})["id"] for _ in range(n)]
    counts = []
    def w():
        counts.append(loop(cp, poll_seconds=0.02, max_jobs=None) if False else 0)
    # bounded workers racing on the same queue
    threads = [threading.Thread(target=lambda: counts.append(
        loop(cp, poll_seconds=0.02, max_jobs=2))) for _ in range(3)]
    [t.start() for t in threads]; [t.join(timeout=60) for t in threads]
    assert sum(counts) == n  # every job claimed exactly once across racing workers
    for jid in ids:
        assert cp._req("GET", f"/v1/jobs/{jid}")["status"] == "succeeded"
