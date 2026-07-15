"""`utag ai` works with every provider credential scrubbed from the environment."""
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
def _scrub_keys(monkeypatch):
    for var in list(os.environ):
        if var.endswith("_API_KEY") or var.endswith("_TOKEN"):
            monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(ROOT)


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


def test_ai_providers_and_models():
    rc, out = run_cli("ai", "providers")
    assert rc == 0 and "fake-local" in out and "(local)" in out
    rc, out = run_cli("ai", "models")
    assert rc == 0 and "anthropic/claude-sonnet-4-6" in out


def test_ai_route_policy_file():
    rc, out = run_cli("ai", "route", "--task", "generate-openapi",
                      "--policy", "policies/ai-router.yaml")
    assert rc == 0
    decision = json.loads(out)
    assert decision["provider"] == "anthropic" and decision["fallback_used"] is False


def test_ai_route_unknown_task_fails():
    rc, _ = run_cli("ai", "route", "--task", "does-not-exist",
                    "--policy", "policies/ai-router.yaml")
    assert rc == 1


def test_ai_eval_offline():
    rc, out = run_cli("ai", "eval", "--suite", "evals/openapi-generation.yaml")
    assert rc == 0 and "0 failed" in out and "offline" in out


def test_ai_doctor():
    rc, out = run_cli("ai", "doctor")
    assert rc == 0 and "0 problem(s)" in out
