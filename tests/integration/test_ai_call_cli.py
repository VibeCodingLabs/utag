"""`utag ai call`: offline routed path, refusal without credentials, evidence."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path

import pytest

from utag_cli.main import main as cli_main

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _offline(monkeypatch, tmp_path):
    for var in list(os.environ):
        if var.endswith("_API_KEY") or var.endswith("_TOKEN"):
            monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("UTAG_OBSERVE_DIR", str(tmp_path / "runs"))


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


def test_offline_task_routes_to_fake_local_and_records_evidence(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("emit one metric point")
    rc, out = run_cli("ai", "call", "--task", "offline-smoke",
                      "--prompt-file", str(prompt), "--schema", "metric-point")
    assert rc == 0
    payload = json.loads(out)
    assert payload["name"].startswith("utag_")
    store = Path(os.environ["UTAG_OBSERVE_DIR"])
    (evidence,) = store.glob("*.jsonl")
    text = evidence.read_text()
    assert '"utag.ai.route"' in text
    assert '"model-call-trace"' in text and '"prompt-run"' in text


def test_live_task_refused_without_credentials(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("x")
    rc, _ = run_cli("ai", "call", "--task", "generate-openapi",
                    "--prompt-file", str(prompt), "--schema", "metric-point")
    assert rc == 1  # anthropic routed, no key in env -> refuse, never a fake success


def test_cache_roundtrip_via_cli(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("same prompt")
    cache = tmp_path / "cache"
    for _ in range(2):
        rc, _ = run_cli("ai", "call", "--task", "offline-smoke",
                        "--prompt-file", str(prompt), "--schema", "metric-point",
                        "--cache-dir", str(cache))
        assert rc == 0
    assert len(list(cache.glob("*.json"))) == 1
