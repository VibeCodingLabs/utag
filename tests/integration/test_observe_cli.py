"""End-to-end: `utag generate` emits run evidence; `utag observe` reads/validates it."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import pytest

from utag_cli.main import main as cli_main

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/prompts/categorize-file.prompt.yaml"


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


@pytest.fixture()
def observed_run(tmp_path, monkeypatch):
    store = tmp_path / "runs"
    monkeypatch.setenv("UTAG_OBSERVE_DIR", str(store))
    rc, _ = run_cli("generate", "--input", str(FIXTURE), "--target", "pydantic-models",
                    "--out", str(tmp_path / "out"))
    assert rc == 0
    files = list(store.glob("*.jsonl"))
    assert len(files) == 1
    return tmp_path, files[0].stem


def test_generate_emits_linked_evidence(observed_run):
    tmp_path, run_id = observed_run
    report = json.loads((tmp_path / "out/validation.report.json").read_text())
    assert report["run_id"] == run_id
    assert report["span_id"].startswith("sp-")
    assert report["valid"] is True


def test_observe_run_export_summary_doctor(observed_run):
    tmp_path, run_id = observed_run
    rc, out = run_cli("observe", "run", "--run-id", run_id)
    assert rc == 0 and '"utag.generate"' in out
    export = tmp_path / "events.jsonl"
    rc, _ = run_cli("observe", "export", "--out", str(export))
    assert rc == 0
    kinds = {json.loads(l)["kind"] for l in export.read_text().splitlines()}
    assert kinds == {"run-trace", "metric-point"}
    summary = tmp_path / "summary.md"
    rc, out = run_cli("observe", "summary", "--out", str(summary))
    assert rc == 0
    assert "- runs: 1" in summary.read_text()
    assert "`utag_runs_total`: 1" in summary.read_text()
    rc, out = run_cli("observe", "doctor")
    assert rc == 0 and "0 problem(s)" in out


def test_observe_doctor_fails_on_corrupt_evidence(observed_run, monkeypatch):
    tmp_path, run_id = observed_run
    store = Path((tmp_path / "runs"))
    bad = store / "run-corrupt.jsonl"
    bad.write_text('{"kind": "metric-point", "record": {"name": "bad name", "value": 1}}\n')
    rc, out = run_cli("observe", "doctor")
    assert rc == 1
