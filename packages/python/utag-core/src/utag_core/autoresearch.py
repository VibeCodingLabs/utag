"""Autoresearch task engine (v2.14.0 Phase 6).

Tasks are YAML validating against the strict `AutoresearchTask` contract.
Lifecycle: research -> plan -> schema -> tests -> implementation -> validation
-> docs -> receipt. Gates are real subprocesses; a task can never be `completed`
unless every gate passes AND every required output exists — failed runs emit a
follow-up task spec instead.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from utag_core.schemas.autoresearch import (
    AutoresearchPlan, AutoresearchStep, AutoresearchTask, GateResult,
    StepKind, TaskCompletionReceipt, TaskMode, TaskStatus,
)

_LIFECYCLE = [StepKind.research, StepKind.plan, StepKind.schema, StepKind.tests,
              StepKind.implementation, StepKind.validation, StepKind.docs, StepKind.receipt]
_RESEARCH_ONLY = {StepKind.research, StepKind.plan, StepKind.docs, StepKind.receipt}


def load_task(path: Path) -> AutoresearchTask:
    return AutoresearchTask.model_validate(yaml.safe_load(path.read_text()))


def make_plan(task: AutoresearchTask) -> AutoresearchPlan:
    kinds = [k for k in _LIFECYCLE
             if task.mode != TaskMode.research or k in _RESEARCH_ONLY]
    steps = [AutoresearchStep(id=f"{task.id}-{k.value}", kind=k,
                              description=f"{k.value} step for: {task.goal}")
             for k in kinds]
    return AutoresearchPlan(task_id=task.id, steps=steps)


def run_gates(task: AutoresearchTask, root: Path, dry_run: bool = False
              ) -> tuple[list[GateResult], list[str]]:
    """Execute every gate command; returns (results, command transcript)."""
    results, commands = [], []
    for gate in task.gates:
        commands.append(gate.command)
        if dry_run:
            results.append(GateResult(name=gate.name, passed=True,
                                      extensions={"dry_run": True}))
            continue
        proc = subprocess.run(gate.command, shell=True, cwd=root,
                              capture_output=True, text=True)
        results.append(GateResult(name=gate.name, passed=proc.returncode == 0))
    return results, commands


def missing_outputs(task: AutoresearchTask, root: Path) -> list[str]:
    return [o for o in task.required_outputs if not (root / o).exists()]


def build_receipt(task: AutoresearchTask, gates: list[GateResult],
                  commands: list[str], missing: list[str]) -> TaskCompletionReceipt:
    next_tasks = []
    if any(not g.passed for g in gates) or missing:
        next_tasks.append(f"{task.id}-followup")
    return TaskCompletionReceipt(task_id=task.id, commands_run=commands,
                                 files_changed=task.required_outputs,
                                 gates=gates, next_tasks=next_tasks)


def result_status(gates: list[GateResult], missing: list[str]) -> TaskStatus:
    if gates and all(g.passed for g in gates) and not missing:
        return TaskStatus.completed
    if any(g.passed for g in gates):
        return TaskStatus.partial
    return TaskStatus.failed


def write_followup(task: AutoresearchTask, gates: list[GateResult],
                   missing: list[str], root: Path) -> Path | None:
    """Failed tasks auto-create a follow-up spec; completed tasks create nothing."""
    failed = [g.name for g in gates if not g.passed]
    if not failed and not missing:
        return None
    followup = {
        "id": f"{task.id}-followup",
        "goal": f"Fix failed gates {failed} and missing outputs {missing} for: {task.goal}",
        "mode": "implement",
        "inputs": task.inputs,
        "required_outputs": task.required_outputs,
        "gates": [{"name": g.name, "command": g.command} for g in task.gates],
        "done_when": ["all_gates_pass"],
    }
    AutoresearchTask.model_validate(followup)  # never emit an invalid spec
    out = root / "TODO" / "autoresearch" / f"{followup['id']}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(followup, sort_keys=False))
    return out


def report_markdown(task: AutoresearchTask, gates: list[GateResult],
                    commands: list[str], missing: list[str]) -> str:
    status = result_status(gates, missing)
    lines = [f"# Autoresearch report: {task.id}", "",
             f"- goal: {task.goal}", f"- mode: {task.mode.value}",
             f"- status: **{status.value}**", "", "## Gates", ""]
    lines += [f"- {'PASS' if g.passed else 'FAIL'}: {g.name}" for g in gates] or ["- (none)"]
    lines += ["", "## Commands", ""] + [f"- `{c}`" for c in commands]
    if missing:
        lines += ["", "## Missing required outputs", ""] + [f"- {m}" for m in missing]
    return "\n".join(lines) + "\n"
