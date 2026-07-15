"""`utag automation` CLI: list/validate/run/doctor with run evidence."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from utag_cli.main import main as cli_main

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


@pytest.fixture(autouse=True)
def _in_repo(monkeypatch):
    monkeypatch.chdir(ROOT)


def test_list_and_validate():
    rc, out = run_cli("automation", "list")
    assert rc == 0 and "schema-drift" in out and "release-gate" in out
    rc, out = run_cli("automation", "validate")
    assert rc == 0 and "8 manifest(s) valid" in out


def test_doctor_clean():
    rc, out = run_cli("automation", "doctor")
    assert rc == 0 and "0 problem(s)" in out


def test_run_records_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("UTAG_OBSERVE_DIR", str(tmp_path))
    rc, out = run_cli("automation", "run", "autoresearch-weekly")
    assert rc == 0 and "ok" in out
    (evidence,) = tmp_path.glob("*.jsonl")
    assert "utag.automation.step" in evidence.read_text()


def test_run_unknown_id_fails():
    rc, _ = run_cli("automation", "run", "nope")
    assert rc == 1
