"""Full autonomous-DevOps loop against a FAKE GitHub API — no real GitHub needed:
signed webhook comment -> control-plane fetches source file (installation token)
-> job queued -> Python worker generates+validates -> control-plane pushes
blobs/tree/commit/ref and opens a PR whose body embeds the ValidationReports
-> comments the PR link back on the triggering issue."""
import base64
import hashlib
import hmac as hmac_mod
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from utag_worker.worker import ControlPlane, loop

BIN = Path(__file__).parents[2] / "control-plane" / "utag-control-plane"
FIXTURE = Path(__file__).parents[2] / "fixtures" / "prompts" / "categorize-file.prompt.yaml"
SECRET, TOKEN = "hook-secret", "api-token"
RECORDED = {"pulls": [], "comments": [], "refs": [], "blobs": 0}


class FakeGitHub(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if "/contents/" in self.path:
            content = base64.b64encode(FIXTURE.read_bytes()).decode()
            return self._json(200, {"content": content, "encoding": "base64"})
        if "/git/ref/heads/" in self.path:
            return self._json(200, {"object": {"sha": "basesha"}})
        if "/git/commits/basesha" in self.path:
            return self._json(200, {"tree": {"sha": "basetree"}})
        self._json(404, {"error": self.path})

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if "/access_tokens" in self.path:
            return self._json(201, {"token": "installation-token"})
        if "/git/blobs" in self.path:
            RECORDED["blobs"] += 1
            return self._json(201, {"sha": f"blob{RECORDED['blobs']}"})
        if "/git/trees" in self.path:
            return self._json(201, {"sha": "newtree"})
        if "/git/commits" in self.path:
            return self._json(201, {"sha": "newcommit"})
        if "/git/refs" in self.path:
            RECORDED["refs"].append(json.loads(body))
            return self._json(201, {})
        if "/pulls" in self.path:
            RECORDED["pulls"].append(json.loads(body))
            return self._json(201, {"html_url": "http://fake/pr/1", "number": 1})
        if "/comments" in self.path:
            RECORDED["comments"].append(json.loads(body))
            return self._json(201, {})
        self._json(404, {"error": self.path})


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    if not BIN.exists():
        pytest.skip("control-plane binary not built")
    td = tmp_path_factory.mktemp("gh")
    key = td / "app.pem"
    subprocess.run(["openssl", "genrsa", "-out", str(key), "2048"],
                   check=True, capture_output=True)
    gh_port, cp_port = _free_port(), _free_port()
    gh = ThreadingHTTPServer(("127.0.0.1", gh_port), FakeGitHub)
    threading.Thread(target=gh.serve_forever, daemon=True).start()
    env = {**os.environ, "UTAG_PORT": str(cp_port), "UTAG_API_TOKEN": TOKEN,
           "UTAG_GITHUB_WEBHOOK_SECRET": SECRET, "UTAG_GITHUB_APP_ID": "777",
           "UTAG_GITHUB_PRIVATE_KEY_FILE": str(key),
           "UTAG_GITHUB_API_BASE": f"http://127.0.0.1:{gh_port}"}
    proc = subprocess.Popen([str(BIN), "serve"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{cp_port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("control-plane not healthy")
    yield base
    proc.terminate()
    gh.shutdown()


def _signed_webhook(base, event: dict, sig_secret=SECRET):
    body = json.dumps(event).encode()
    sig = "sha256=" + hmac_mod.new(sig_secret.encode(), body, hashlib.sha256).hexdigest()
    req = urllib.request.Request(base + "/v1/integrations/github/webhook", data=body,
                                 headers={"Content-Type": "application/json",
                                          "X-GitHub-Event": "issue_comment",
                                          "X-Hub-Signature-256": sig})
    return urllib.request.urlopen(req, timeout=10)


EVENT = {"action": "created",
         "comment": {"body": "/utag generate pydantic-models prompts/categorize.prompt.yaml"},
         "issue": {"number": 5},
         "repository": {"full_name": "acme/devops", "default_branch": "main"},
         "installation": {"id": 42}}


def test_bad_signature_rejected(stack):
    import urllib.error
    with pytest.raises(urllib.error.HTTPError) as ei:
        _signed_webhook(stack, EVENT, sig_secret="wrong-secret")
    assert ei.value.code == 401


def test_webhook_to_pull_request_full_loop(stack):
    with _signed_webhook(stack, EVENT) as r:
        assert r.status == 202
        job = json.loads(r.read())
    assert job["status"] == "queued" and job["target"] == "pydantic-models"
    assert "class CategorizeFileInput" not in job["input"]  # raw yaml, not generated yet
    # worker does the actual generation + validation
    cp = ControlPlane(stack, token=TOKEN)
    loop(cp, poll_seconds=0.05, max_jobs=1)
    # delivery is async on complete — poll fake GitHub for the PR
    for _ in range(100):
        if RECORDED["pulls"]:
            break
        time.sleep(0.1)
    assert RECORDED["pulls"], "PR was never opened on fake GitHub"
    pr = RECORDED["pulls"][0]
    assert pr["base"] == "main" and pr["head"].startswith("utag/job-")
    assert "utag generation report" in pr["body"]
    assert '"valid": true' in pr["body"]          # ValidationReport embedded = review evidence
    assert "categorize_file.py" in pr["body"]
    assert RECORDED["refs"][0]["ref"].startswith("refs/heads/utag/job-")
    assert RECORDED["blobs"] >= 1
    # PR link commented back on the triggering issue
    for _ in range(50):
        if RECORDED["comments"]:
            break
        time.sleep(0.1)
    assert "http://fake/pr/1" in RECORDED["comments"][0]["body"]
    # job event trail includes pr_opened
    events_req = urllib.request.Request(f"{stack}/v1/jobs/{job['id']}/events",
                                        headers={"Authorization": f"Bearer {TOKEN}"})
    types = []
    with urllib.request.urlopen(events_req, timeout=15) as r:
        for raw in r:
            line = raw.decode().strip()
            if line.startswith("event: "):
                types.append(line.removeprefix("event: "))
            if "pr_opened" in types:
                break
    assert "pr_opened" in types
