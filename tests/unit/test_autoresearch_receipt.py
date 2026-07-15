"""Task engine: plans, gate execution, completion rules, follow-up specs."""
from __future__ import annotations

import yaml

from utag_core import autoresearch as ar
from utag_core.schemas.autoresearch import (
    AutoresearchTask, GateResult, StepKind, TaskStatus,
)


def _task(**over) -> AutoresearchTask:
    base = {"id": "ar-demo", "goal": "demo", "mode": "implement",
            "gates": [{"name": "ok", "command": "true"},
                      {"name": "boom", "command": "false"}],
            "required_outputs": []}
    base.update(over)
    return AutoresearchTask.model_validate(base)


def test_plan_follows_lifecycle():
    plan = ar.make_plan(_task())
    kinds = [s.kind for s in plan.steps]
    assert kinds[0] == StepKind.research and kinds[-1] == StepKind.receipt
    assert StepKind.implementation in kinds
    research_kinds = [s.kind for s in ar.make_plan(_task(mode="research")).steps]
    assert StepKind.implementation not in research_kinds


def test_gates_run_for_real(tmp_path):
    gates, commands = ar.run_gates(_task(), tmp_path)
    assert [g.passed for g in gates] == [True, False]
    assert commands == ["true", "false"]


def test_cannot_complete_with_failed_gate():
    gates = [GateResult(name="ok", passed=True), GateResult(name="boom", passed=False)]
    assert ar.result_status(gates, []) == TaskStatus.partial
    assert ar.result_status([GateResult(name="boom", passed=False)], []) == TaskStatus.failed
    assert ar.result_status([GateResult(name="ok", passed=True)], []) == TaskStatus.completed
    assert ar.result_status([GateResult(name="ok", passed=True)], ["missing.txt"]) != TaskStatus.completed


def test_receipt_lists_followup_only_on_failure():
    ok = [GateResult(name="ok", passed=True)]
    bad = [GateResult(name="boom", passed=False)]
    assert ar.build_receipt(_task(), ok, ["true"], []).next_tasks == []
    assert ar.build_receipt(_task(), bad, ["false"], []).next_tasks == ["ar-demo-followup"]


def test_failed_task_writes_valid_followup_spec(tmp_path):
    gates = [GateResult(name="boom", passed=False)]
    path = ar.write_followup(_task(), gates, ["out.txt"], tmp_path)
    assert path is not None and path.is_file()
    followup = AutoresearchTask.model_validate(yaml.safe_load(path.read_text()))
    assert followup.id == "ar-demo-followup" and "boom" in followup.goal
    assert ar.write_followup(_task(), [GateResult(name="ok", passed=True)], [], tmp_path) is None


def test_dry_run_marks_gates():
    gates, _ = ar.run_gates(_task(), None, dry_run=True)
    assert all(g.passed and (g.extensions or {}).get("dry_run") for g in gates)
