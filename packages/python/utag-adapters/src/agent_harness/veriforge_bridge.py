"""VeriForge <-> utag bridge: run the 5-role verifiable pipeline, PEE, CoVe, and the
ambiguity gate on utag's provider stack (pydantic-ai models, catalog, credentials).

- PydanticAIClient satisfies veriforge's LLMClient protocol -> veriforge Agents run on any
  utag model (including TestModel/FunctionModel offline). Instructor stays an optional
  native path inside utag-veriforge; this bridge needs neither.
- HeuristicScorer is a deterministic, documented, structure-based ambiguity scorer
  (offline default). LLMScorer wraps a model for production scoring.
- veriforge_tools() mounts session tools: clarify_task / enhance_prompt (structural,
  instant) and run_pipeline (model-backed, LocalSandbox, bounded).
"""
from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel
from pydantic_ai import Agent as PAIAgent
from pydantic_ai import Tool

from veriforge.core.agent import Agent as VFAgent
from veriforge.core.agent import AgentSpec
from veriforge.core.binding import ModelBinding
from veriforge.core.schemas import (AmbiguityDimension, AmbiguityReport, ClarifiedTask,
                                    ClarifyingQuestion, TaskProfile, TaskSpec)
from veriforge.pee.enhancer import compose, cove_gate, select
from veriforge.pee.techniques import TechniqueRegistry, load_registry


# ---------------------------------------------------------------- client adapter
class PydanticAIClient:
    """veriforge LLMClient protocol over a pydantic-ai model. One agent per
    (system, response_model) pair, cached — veriforge roles are stable pairs."""

    def __init__(self, model: Any):
        self.model = model
        self._agents: dict[tuple[str, type], PAIAgent] = {}

    def create(self, *, messages: list[dict], response_model: Type[BaseModel],
               max_retries: int = 3, **kw: Any) -> BaseModel:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user = "\n".join(m["content"] for m in messages if m["role"] == "user")
        key = (system, response_model)
        if key not in self._agents:
            self._agents[key] = PAIAgent(self.model, output_type=response_model,
                                         instructions=system, retries=max_retries)
        return self._agents[key].run_sync(user).output


def vf_agent(name: str, system_prompt: str, model: Any) -> VFAgent:
    """A veriforge role agent backed by a pydantic-ai model. Binding recorded as data
    (provider 'pydantic-ai') — hot-swap happens at the utag model layer."""
    spec = AgentSpec(name=name, role=name, system_prompt=system_prompt,
                     binding=ModelBinding(provider="pydantic-ai", model=str(model)))
    return VFAgent(spec, client=PydanticAIClient(model))


def build_agents(model: Any, per_role_models: dict[str, Any] | None = None) -> dict[str, VFAgent]:
    """All five roles + orchestrator on one model, or per-role overrides
    (per_role_models={'critic': other_model} — decorrelate critic per AgentForge Eq.19)."""
    from veriforge.agents.roles import SYSTEM
    per_role_models = per_role_models or {}
    return {name: vf_agent(name, sys_prompt, per_role_models.get(name, model))
            for name, sys_prompt in SYSTEM.items()}


# ---------------------------------------------------------------- ambiguity scorers
_DIM_HINT = {
    AmbiguityDimension.scope: ("What is in and out of scope?", ["single module", "whole package", "one function", "unsure"]),
    AmbiguityDimension.io_contract: ("What are the exact inputs and outputs?", ["typed models", "plain dicts", "files", "unsure"]),
    AmbiguityDimension.constraints: ("Any hard constraints (versions, style, deps)?", ["yes, will list", "none", "unsure"]),
    AmbiguityDimension.environment: ("Where must this run?", ["python 3.12", "docker", "browser", "unsure"]),
    AmbiguityDimension.success_criteria: ("How is success verified?", ["tests pass", "manual review", "benchmark", "unsure"]),
    AmbiguityDimension.priority: ("What matters most?", ["correctness", "speed", "readability", "cost"]),
}


class HeuristicScorer:
    """Deterministic structural scorer — no LLM. Scores presence of information, not
    quality: a goal >= 8 words scopes at 0.9; declared constraints/acceptance lift their
    dimensions; user answers lift the weakest dimensions round by round. Documented
    heuristic, not intelligence — swap in LLMScorer for semantic scoring."""

    def score(self, task: TaskSpec, answers: dict[str, str]) -> AmbiguityReport:
        s: dict[AmbiguityDimension, float] = {
            AmbiguityDimension.scope: 0.9 if len(task.goal.split()) >= 8 else 0.5,
            AmbiguityDimension.io_contract: 0.9 if task.acceptance_criteria else 0.5,
            AmbiguityDimension.constraints: 0.9 if task.constraints else 0.6,
            AmbiguityDimension.environment: 0.9 if task.context_files else 0.6,
            AmbiguityDimension.success_criteria: 0.9 if task.acceptance_criteria else 0.5,
            AmbiguityDimension.priority: 0.9,
        }
        answered = {q for q in answers}
        for dim in s:
            q, _ = _DIM_HINT[dim]
            if q in answered and answers[q].strip():
                s[dim] = max(s[dim], 0.9)
        open_qs = [ClarifyingQuestion(dimension=d, question=_DIM_HINT[d][0], options=_DIM_HINT[d][1])
                   for d, v in sorted(s.items(), key=lambda kv: kv[1]) if v < 0.85]
        return AmbiguityReport(scores=s, open_questions=open_qs[:3])


class LLMScorer:
    """Model-backed scorer (production path): a veriforge agent emits AmbiguityReport."""

    def __init__(self, model: Any):
        self._agent = vf_agent(
            "ambiguity-scorer",
            "Score task ambiguity on six dimensions in [0,1] (1 = fully specified): scope, "
            "io_contract, constraints, environment, success_criteria, priority. Weakest link "
            "gates. Emit <=3 clarifying questions (2-4 tap-able options each) for dims < 0.85.",
            model)

    def score(self, task: TaskSpec, answers: dict[str, str]) -> AmbiguityReport:
        qa = "\n".join(f"Q: {q}\nA: {a}" for q, a in answers.items())
        return self._agent.run(f"TASK: {task.model_dump_json()}\nANSWERS:\n{qa or '(none)'}",
                               AmbiguityReport)


class NullAsker:
    """Non-interactive contexts (tools, CI): asks nothing; unresolved dims become
    explicit logged assumptions via clarify_loop — never silent."""

    def ask(self, questions: list[ClarifyingQuestion]) -> dict[str, str]:
        return {}


# ---------------------------------------------------------------- structural helpers
def profile_from_facets(complexity: str = "standard", artifact_type: str = "code",
                        domain: str = "software-engineering") -> TaskProfile:
    return TaskProfile(complexity=complexity, artifact_type=artifact_type, domain=domain)


def enhance(goal: str, constraints: list[str] | None = None,
            acceptance_criteria: list[str] | None = None,
            answers: dict[str, str] | None = None, assumptions: list[str] | None = None,
            complexity: str = "standard", artifact_type: str = "code",
            registry: TechniqueRegistry | None = None):
    """select -> compose -> CoVe-gate (structural anti-fabrication). Pure, offline."""
    task = TaskSpec(goal=goal, constraints=constraints or [],
                    acceptance_criteria=acceptance_criteria or [],
                    profile=profile_from_facets(complexity, artifact_type))
    clarified = ClarifiedTask(task=task, answers=answers or {}, assumptions=assumptions or [])
    reg = registry or load_registry()
    chosen = select(task.profile, reg)
    return cove_gate(compose(clarified, chosen), clarified)


# ---------------------------------------------------------------- session tools
def veriforge_tools(model: Any = None, sandbox: Any = None) -> list[Tool]:
    """Structural tools always; run_pipeline only when a model is supplied."""

    def clarify_task(goal: str, constraints: list[str] = [],
                     acceptance_criteria: list[str] = []) -> dict:
        """Score task ambiguity (6 dims, weakest link gates at 0.85) and return the
        open clarifying questions. Deterministic heuristic; instant."""
        task = TaskSpec(goal=goal, constraints=constraints,
                        acceptance_criteria=acceptance_criteria)
        r = HeuristicScorer().score(task, {})
        return {"overall": r.overall,
                "scores": {d.value: v for d, v in r.scores.items()},
                "open_questions": [{"dimension": q.dimension.value, "question": q.question,
                                    "options": q.options} for q in r.open_questions]}

    def enhance_prompt(goal: str, constraints: list[str] = [],
                       acceptance_criteria: list[str] = [],
                       complexity: str = "standard", artifact_type: str = "code") -> dict:
        """PEE: select techniques from the 49/58 taxonomy (CoVe always composed last),
        compose system+user, run the structural CoVe anti-fabrication gate."""
        p = enhance(goal, constraints, acceptance_criteria,
                    complexity=complexity, artifact_type=artifact_type)
        return {"system": p.system, "user": p.user,
                "techniques_applied": p.techniques_applied,
                "cove_verified": p.cove_verified, "verification_log": p.verification_log}

    tools = [Tool(clarify_task, name="clarify_task", takes_ctx=False,
                  description="Score a task's ambiguity across 6 dimensions and get "
                              "clarifying questions (with tap-able options) for weak ones."),
             Tool(enhance_prompt, name="enhance_prompt", takes_ctx=False,
                  description="Enhance a raw goal into a technique-composed prompt "
                              "(Prompt Report taxonomy) with a CoVe anti-fabrication gate.")]

    if model is not None:
        from veriforge.agents.orchestrator import Orchestrator
        from veriforge.verification.sandbox import LocalSandbox

        async def run_pipeline(goal: str, constraints: list[str] = [],
                               acceptance_criteria: list[str] = []) -> dict:
            """Full VeriForge run: clarify (heuristic, non-interactive — residual gaps
            logged as assumptions) -> PEE+CoVe -> plan -> per-step sandboxed closed
            loop -> critic verdict. Many model calls; use for real engineering tasks."""
            import asyncio

            def _run() -> dict:
                orch = Orchestrator(agents=build_agents(model),
                                    sandbox=sandbox or LocalSandbox(),
                                    techniques=load_registry(), scorer=HeuristicScorer(),
                                    asker=NullAsker())
                res = orch.run(TaskSpec(goal=goal, constraints=constraints,
                                        acceptance_criteria=acceptance_criteria))
                return {"techniques": res.techniques,
                        "assumptions": res.clarified.assumptions,
                        "plan_rationale": res.plan_rationale,
                        "steps": [{"passed": o.result.passed, "attempts": o.attempts,
                                   "quarantined": o.quarantined, "escalated": o.escalated}
                                  for o in res.outcomes],
                        "verdict": res.verdict.model_dump() if res.verdict else None}

            try:  # sync pipeline in a thread: run_sync needs its own loop; tool errors
                return await asyncio.to_thread(_run)  # return structured, never kill a turn
            except Exception as exc:
                return {"error": f"pipeline failed: {type(exc).__name__}: {str(exc)[:400]}"}

        tools.append(Tool(run_pipeline, name="run_pipeline", takes_ctx=False,
                          description="Run the 5-role verifiable engineering pipeline "
                                      "(plan -> code -> test -> sandbox -> debug -> critic) "
                                      "on a goal. Expensive: many model calls."))
    return tools
