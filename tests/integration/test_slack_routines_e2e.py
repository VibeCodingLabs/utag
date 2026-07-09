"""Slack slash-command + Routines against the real binary.
Slack: signed command -> job (file fetched from fake GitHub) -> worker ->
async result posted to response_url (captured). Routines: config file with a
fast interval -> jobs appear on the queue without any trigger."""
import base64
import hashlib
import hmac as hmac_mod
import json
import os
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from utag_worker.worker import ControlPlane, loop

BIN = Path(__file__).parents[2] / "control-plane" / "utag-control-plane"
FIXTURE = Path(__file__).parents[2] / "fixtures" / "prompts" / "normalize-tool.prompt.yaml"
SLACK_SECRET, TOKEN = "slack-sign", "tok"
CAPTURED = {"slack": [], "pulls": []}


class FakeExternal(BaseHTTPRequestHandler):
    """One fake server plays GitHub API + Slack response_url."""
    def log_message(self, *a): pass
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if "/contents/" in self.path:
            return self._json(200, {"content": base64.b64encode(FIXTURE.read_bytes()).decode(),
                                    "encoding": "base64"})
        if "/git/ref/heads/" in self.path:
            return self._json(200, {"object": {"sha": "b"}})
        if "/git/commits/" in self.path:
            return self._json(200, {"tree": {"sha": "t"}})
        self._json(404, {})
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/slack-response":
            CAPTURED["slack"].append(json.loads(body)); return self._json(200, {})
        if "/access_tokens" in self.path: return self._json(201, {"token": "itok"})
        if "/git/blobs" in self.path: return self._json(201, {"sha": "bl"})
        if "/git/trees" in self.path: return self._json(201, {"sha": "tr"})
        if "/git/commits" in self.path: return self._json(201, {"sha": "c"})
        if "/git/refs" in self.path: return self._json(201, {})
        if "/pulls" in self.path:
            CAPTURED["pulls"].append(json.loads(body))
            return self._json(201, {"html_url": "http://fake/pr/9", "number": 9})
        if "/comments" in self.path: return self._json(201, {})
        self._json(404, {})


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    if not BIN.exists():
        pytest.skip("binary not built")
    td = tmp_path_factory.mktemp("slk")
    key = td / "app.pem"
    subprocess.run(["openssl", "genrsa", "-out", str(key), "2048"], check=True, capture_output=True)
    ext_port, cp_port = _free_port(), _free_port()
    ext = ThreadingHTTPServer(("127.0.0.1", ext_port), FakeExternal)
    threading.Thread(target=ext.serve_forever, daemon=True).start()
    # routines config file (viper yaml) with a fast interval
    routine_input = td / "routine.prompt.yaml"
    routine_input.write_text(FIXTURE.read_text())
    cfg = td / "utag.yaml"
    cfg.write_text(f"""routines:
  - name: fast-loop
    every: 300ms
    target: openapi-3.1
    input-file: {routine_input}
""")
    env = {**os.environ, "UTAG_PORT": str(cp_port), "UTAG_API_TOKEN": TOKEN,
           "UTAG_GITHUB_WEBHOOK_SECRET": "gh-hook", "UTAG_GITHUB_APP_ID": "7",
           "UTAG_GITHUB_PRIVATE_KEY_FILE": str(key),
           "UTAG_GITHUB_API_BASE": f"http://127.0.0.1:{ext_port}",
           "UTAG_GITHUB_INSTALLATION_ID": "42",
           "UTAG_SLACK_SIGNING_SECRET": SLACK_SECRET}
    proc = subprocess.Popen([str(BIN), "serve", "--config", str(cfg)], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{cp_port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1); break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill(); pytest.fail("not healthy")
    yield base, ext_port
    proc.terminate(); ext.shutdown()


def _slash(base, text, ext_port, secret=SLACK_SECRET):
    form = urllib.parse.urlencode({"command": "/utag", "text": text,
                                   "response_url": f"http://127.0.0.1:{ext_port}/slack-response"})
    ts = str(int(time.time()))
    sig = "v0=" + hmac_mod.new(secret.encode(), f"v0:{ts}:{form}".encode(),
                               hashlib.sha256).hexdigest()
    req = urllib.request.Request(base + "/v1/integrations/slack/command", data=form.encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded",
                                          "X-Slack-Request-Timestamp": ts,
                                          "X-Slack-Signature": sig})
    return urllib.request.urlopen(req, timeout=10)


def test_slack_bad_signature_rejected(stack):
    import urllib.error
    base, ext_port = stack
    with pytest.raises(urllib.error.HTTPError) as ei:
        _slash(base, "status x", ext_port, secret="wrong")
    assert ei.value.code == 401


def test_slack_generate_to_pr_and_notify(stack):
    base, ext_port = stack
    with _slash(base, "generate pydantic-models acme/devops prompts/n.prompt.yaml", ext_port) as r:
        ack = json.loads(r.read())
    assert ack["response_type"] == "in_channel" and "queued job" in ack["text"]
    job_id = ack["text"].split("`")[1]
    cp = ControlPlane(base, token=TOKEN)
    # routines may race us for claims; process until our job leaves the queue
    for _ in range(20):
        loop(cp, poll_seconds=0.02, max_jobs=1)
        if cp._req("GET", f"/v1/jobs/{job_id}")["status"] in ("succeeded", "failed"):
            break
    assert cp._req("GET", f"/v1/jobs/{job_id}")["status"] == "succeeded"
    for _ in range(100):
        if CAPTURED["slack"]:
            break
        time.sleep(0.1)
    assert CAPTURED["slack"], "response_url never notified"
    note = CAPTURED["slack"][0]["text"]
    assert job_id in note and "succeeded" in note and "http://fake/pr/9" in note
    assert CAPTURED["pulls"] and CAPTURED["pulls"][0]["head"].startswith("utag/job-")


def test_slack_status_command(stack):
    base, ext_port = stack
    with _slash(base, "status does-not-exist", ext_port) as r:
        out = json.loads(r.read())
    assert out["response_type"] == "ephemeral" and "not found" in out["text"]


def test_routines_enqueue_without_any_trigger(stack):
    base, _ = stack
    cp = ControlPlane(base, token=TOKEN)
    # claim from the queue; routine ticks every 300ms so a job must appear
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            job = cp.claim()
        except Exception:
            job = None
        if job and job.get("backend") == "routine":
            assert job["target"] == "openapi-3.1"
            cp.complete(job["id"], "succeeded")
            return
        if job:  # someone else's job; finish it politely
            cp.complete(job["id"], "succeeded")
        time.sleep(0.1)
    pytest.fail("routine never enqueued")
