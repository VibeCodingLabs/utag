"""`utag openapi`: real outputs, honest exit codes, run evidence."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from utag_cli.main import main as cli_main

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures" / "openapi"


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


def test_normalize_writes_canonical_json(tmp_path):
    out = tmp_path / "norm.json"
    rc, _ = run_cli("openapi", "normalize", "--path", str(FIX / "petstore.yaml"), "--out", str(out))
    assert rc == 0
    doc = json.loads(out.read_text())
    schema = doc["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["items"]["type"] == "object"  # ref resolved to the actual Pet schema


def test_bundle_reports_resolved_refs(tmp_path):
    out = tmp_path / "bundled.json"
    rc, stdout = run_cli("openapi", "bundle", "--path", str(FIX / "petstore-split.yaml"), "--out", str(out))
    assert rc == 0
    assert json.loads(stdout.strip().splitlines()[-1])["resolved_refs"] == ["petstore-shared.yaml#/Pet"]
    assert "required" in out.read_text()


def test_diff_cli(tmp_path):
    out = tmp_path / "diff.json"
    rc, _ = run_cli("openapi", "diff", "--old", str(FIX / "petstore.yaml"),
                    "--new", str(FIX / "petstore-v2.yaml"), "--out", str(out))
    assert rc == 0
    report = json.loads(out.read_text())
    kinds = {e["kind"] for e in report["entries"]}
    assert kinds == {"added", "removed", "changed"}


def test_overlay_apply_cli(tmp_path):
    out = tmp_path / "overlaid.json"
    rc, _ = run_cli("openapi", "overlay", "apply", "--path", str(FIX / "petstore.yaml"),
                    "--overlay", str(FIX / "overlay-title.yaml"), "--out", str(out))
    assert rc == 0
    doc = json.loads(out.read_text())
    assert doc["info"]["title"] == "Petstore (Partner Edition)"
    assert "post" not in doc["paths"]["/pets"]


def test_lint_exit_codes():
    rc, stdout = run_cli("openapi", "lint", "--path", str(FIX / "petstore.yaml"))
    assert rc == 0 and "0 error(s)" in stdout
    rc, stdout = run_cli("openapi", "lint", "--path", str(FIX / "petstore-flawed.yaml"))
    assert rc == 1 and "missing-operation-id" in stdout


def test_agent_readiness_cli(tmp_path, monkeypatch):
    store = tmp_path / "runs"
    monkeypatch.setenv("UTAG_OBSERVE_DIR", str(store))
    rc, stdout = run_cli("openapi", "agent-readiness", "--path", str(FIX / "petstore.yaml"))
    assert rc == 0
    assert json.loads(stdout)["score"] == 1.0
    (evidence,) = store.glob("*.jsonl")  # every subcommand records run evidence
    assert "utag.openapi.agent_readiness" in evidence.read_text()
