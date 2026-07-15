"""Closed-loop verifiable code generation (AgentForge Alg.1): patch -> execute -> route -> repair,
N_retry=3 (gains saturate after 2 — Fig.4). Invariant: nothing reaches Critic without surviving
the sandbox. Flaky => quarantine. Security => always human-flag."""
from __future__ import annotations
import tempfile
from pathlib import Path
from pydantic import BaseModel, Field
from ..core.agent import Agent
from ..core.errors import classify
from ..core.hooks import HookEvent, HookRegistry
from ..core.schemas import (ErrorClass, ExecutionResult, Patch, PlanStep, TestSuite)
from .clover import ConsistencyReport, code_tests_edge
from .sandbox import Sandbox

N_RETRY = 3
FLAKY_RERUNS = 3


class LoopOutcome(BaseModel):
    patch: Patch | None = None
    result: ExecutionResult
    consistency: ConsistencyReport | None = None
    quarantined: bool = False
    escalated: str | None = None
    attempts: int = 0
    log: list[str] = Field(default_factory=list)


def _materialize(workdir: Path, patch: Patch, suite: TestSuite) -> None:
    (workdir / "patch.diff").write_text(patch.unified_diff)      # applied by harness `git apply`
    (workdir / "test_generated.py").write_text(suite.code)


def _is_flaky(sandbox: Sandbox, workdir: str, cmd: list[str], first: ExecutionResult) -> bool:
    outcomes = {first.passed}
    for _ in range(FLAKY_RERUNS - 1):
        outcomes.add(sandbox.run(workdir, cmd).passed)
    return len(outcomes) > 1                                     # inconsistent => flaky


def closed_loop(step: PlanStep, coder: Agent, tester: Agent, debugger: Agent,
                sandbox: Sandbox, hooks: HookRegistry, workdir: str | None = None) -> LoopOutcome:
    wd = Path(workdir or tempfile.mkdtemp(prefix="veriforge-"))
    patch = coder.run(step.description, Patch)
    hooks.fire(HookEvent.post_patch, {"step": step.description, "files": patch.files_touched})
    suite = tester.run(f"Write tests for: {step.description}\nPATCH:\n{patch.unified_diff}", TestSuite)
    _materialize(wd, patch, suite)
    cmd = ["python", "-m", "pytest", "-x", "-q", "test_generated.py"]

    log: list[str] = []
    attempts = 0
    hooks.fire(HookEvent.pre_execute, {"workdir": str(wd)})
    result = sandbox.run(str(wd), cmd)

    while not result.passed and attempts < N_RETRY:
        routed = classify(result)
        hooks.fire(HookEvent.on_error, routed.model_dump())
        log.append(f"attempt {attempts + 1}: {routed.error_class.value} -> {routed.handler}")

        if routed.error_class == ErrorClass.flaky_test or _is_flaky(sandbox, str(wd), cmd, result):
            return LoopOutcome(patch=patch, result=result, quarantined=True,
                               attempts=attempts, log=log + ["QUARANTINED: flaky — no fix cycle"])
        if routed.error_class in (ErrorClass.security, ErrorClass.design):
            return LoopOutcome(patch=patch, result=result, escalated=routed.escalation,
                               attempts=attempts, log=log)

        patch = debugger.run(                                     # routed context, not a dump
            f"STEP: {step.description}\nCONTEXT STRATEGY: {routed.context_strategy}\n"
            f"PATCH:\n{patch.unified_diff}\nSTDERR:\n{result.stderr[-2000:]}\nSTDOUT:\n{result.stdout[-2000:]}",
            Patch)
        _materialize(wd, patch, suite)
        result = sandbox.run(str(wd), cmd)
        attempts += 1

    consistency = ConsistencyReport(edges=[code_tests_edge(result)]) if result.passed else None
    hooks.fire(HookEvent.post_verify, {"passed": result.passed, "attempts": attempts})
    return LoopOutcome(patch=patch if result.passed else None,   # invariant: unpassed patch never propagates
                       result=result, consistency=consistency, attempts=attempts, log=log)
