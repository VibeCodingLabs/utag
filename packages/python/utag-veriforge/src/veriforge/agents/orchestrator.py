"""End-to-end wiring: intake -> PEE -> plan -> per-step closed loop -> critic -> memory."""
from __future__ import annotations
from pydantic import BaseModel, Field
from ..core.agent import Agent
from ..core.hooks import HookEvent, HookRegistry
from ..core.schemas import ClarifiedTask, Plan, TaskSpec, Verdict
from ..intake.ambiguity import Asker, Scorer, clarify_loop
from ..pee.enhancer import compose, cove_gate, select
from ..pee.techniques import TechniqueRegistry
from ..verification.loop import LoopOutcome, closed_loop
from ..verification.sandbox import Sandbox


class PipelineResult(BaseModel):
    clarified: ClarifiedTask
    techniques: list[str]
    plan_rationale: str = ""
    outcomes: list[LoopOutcome] = Field(default_factory=list)
    verdict: Verdict | None = None


class Orchestrator:
    def __init__(self, agents: dict[str, Agent], sandbox: Sandbox,
                 techniques: TechniqueRegistry, scorer: Scorer, asker: Asker,
                 hooks: HookRegistry | None = None) -> None:
        self.agents, self.sandbox, self.techniques = agents, sandbox, techniques
        self.scorer, self.asker = scorer, asker
        self.hooks = hooks or HookRegistry()

    def run(self, task: TaskSpec) -> PipelineResult:
        # 1. Ambiguity gate — AskUserQuestions loop until threshold
        self.hooks.fire(HookEvent.pre_clarify, {"goal": task.goal})
        clarified = clarify_loop(task, self.scorer, self.asker)

        # 2. Prompt Enhancement Engine — taxonomy-mapped techniques + CoVe anti-fabrication gate
        chosen = select(task.profile, self.techniques)
        prompt = cove_gate(compose(clarified, chosen), clarified)
        self.hooks.fire(HookEvent.post_enhance, {"techniques": prompt.techniques_applied,
                                                 "cove_verified": prompt.cove_verified})

        # 3. Plan
        self.hooks.fire(HookEvent.pre_plan, {})
        plan = self.agents["planner"].run(prompt.user, Plan)

        # 4. Execute each step through the execution-grounded closed loop
        outcomes = [closed_loop(step, self.agents["coder"], self.agents["tester"],
                                self.agents["debugger"], self.sandbox, self.hooks)
                    for step in plan.steps]

        # 5. Critic — binary verdict over full trace; PASS persists to episodic memory (caller's store)
        trace = "\n".join(f"step={s.description} passed={o.result.passed} attempts={o.attempts}"
                          for s, o in zip(plan.steps, outcomes))
        verdict = self.agents["critic"].run(f"TASK: {task.goal}\nTRACE:\n{trace}", Verdict)
        self.hooks.fire(HookEvent.on_verdict, verdict.model_dump())
        return PipelineResult(clarified=clarified, techniques=prompt.techniques_applied,
                              plan_rationale=plan.rationale, outcomes=outcomes, verdict=verdict)
