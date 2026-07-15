"""`utag autoresearch`: init -> plan -> execute -> receipt, honest failure paths."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import pytest
import yaml

from utag_cli.main import main as cli_main
from utag_core.schemas.autoresearch import TaskCompletionReceipt


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


@pytest.fixture()
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write_task(tmp_path: Path, *, command: str, outputs: list[str]) -> Path:
    spec = {"id": "ar-it", "goal": "integration demo", "mode": "implement",
            "inputs": [], "required_outputs": outputs,
            "gates": [{"name": "gate", "command": command}],
            "done_when": ["all_gates_pass"]}
    p = tmp_path / "task.yaml"
    p.write_text(yaml.safe_dump(spec, sort_keys=False))
    return p


def test_init_writes_valid_task(workdir):
    rc, out = run_cli("autoresearch", "init", "--goal", "Ship the demo", "--out", "t.yaml")
    assert rc == 0
    spec = yaml.safe_load((workdir / "t.yaml").read_text())
    assert spec["id"].startswith("ar-") and spec["gates"]


def test_plan_and_successful_execute_with_receipt(workdir):
    task = _write_task(workdir, command="touch out.txt", outputs=["out.txt"])
    rc, out = run_cli("autoresearch", "plan", "--task", str(task))
    assert rc == 0 and '"kind": "implementation"' in out
    rc, out = run_cli("autoresearch", "execute", "--task", str(task), "--mode", "local")
    assert rc == 0 and "status: completed" in out
    receipt = TaskCompletionReceipt.model_validate_json(
        (workdir / "reports/autoresearch/ar-it.receipt.json").read_text())
    assert receipt.gates[0].passed and receipt.next_tasks == []
    assert (workdir / "reports/autoresearch/ar-it.md").read_text().count("PASS") == 1


def test_failed_gate_blocks_completion_and_creates_followup(workdir):
    task = _write_task(workdir, command="false", outputs=[])
    rc, out = run_cli("autoresearch", "execute", "--task", str(task), "--mode", "local")
    assert rc == 1 and "status: failed" in out
    followup = workdir / "TODO/autoresearch/ar-it-followup.yaml"
    assert followup.is_file()
    receipt = json.loads((workdir / "reports/autoresearch/ar-it.receipt.json").read_text())
    assert receipt["next_tasks"] == ["ar-it-followup"]


def test_missing_required_output_blocks_completion(workdir):
    task = _write_task(workdir, command="true", outputs=["never-created.txt"])
    rc, out = run_cli("autoresearch", "execute", "--task", str(task), "--mode", "local")
    assert rc == 1 and "status: partial" in out


def test_dry_run_never_executes(workdir):
    task = _write_task(workdir, command="touch should-not-exist.txt", outputs=[])
    rc, out = run_cli("autoresearch", "execute", "--task", str(task), "--mode", "dry-run")
    assert rc == 0 and "dry-run preview" in out
    assert not (workdir / "should-not-exist.txt").exists()


def test_validate_reports_gate_status(workdir):
    task = _write_task(workdir, command="true", outputs=[])
    rc, out = run_cli("autoresearch", "validate", "--task", str(task))
    assert rc == 0 and "PASS gate" in out
