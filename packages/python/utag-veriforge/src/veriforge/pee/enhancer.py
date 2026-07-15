"""Prompt Enhancement Engine: select -> compose -> CoVe-gate -> EnhancedPrompt."""
from __future__ import annotations
from ..core.schemas import ClarifiedTask, EnhancedPrompt, TaskProfile
from .techniques import PHASE_ORDER, TechniqueRegistry, TechniqueSpec


def _matches(t: TechniqueSpec, profile: TaskProfile, facets: dict) -> bool:
    trig = t.trigger
    if trig.get("always"):
        return True
    for key, want in trig.items():
        have = facets.get(key, getattr(profile, key, None))
        if isinstance(want, list):
            hv = have.value if hasattr(have, "value") else have
            if hv not in want:
                return False
        elif isinstance(want, bool):
            if bool(have) is not want:
                return False
    return bool(trig)                                  # empty trigger != auto-select


def select(profile: TaskProfile, registry: TechniqueRegistry,
           facets: dict | None = None, budget_multiplier: float = 6.0) -> list[TechniqueSpec]:
    """Rank matches by inverse cost; max ONE technique per phase (composition slots);
    respect cumulative cost budget; CoVe forced if within budget (design principle #4)."""
    facets = facets or {}
    chosen: dict[str, TechniqueSpec] = {}
    spend = 0.0
    # CoVe is non-negotiable (design principle #4): reserve its budget FIRST.
    cove = next((t for t in registry.techniques if t.id == "chain_of_verification"), None)
    if cove:
        chosen["self_criticism"] = cove
        spend += cove.cost
    matched = [t for t in registry.techniques if _matches(t, profile, facets)]
    matched.sort(key=lambda t: t.cost)                 # cheapest competent technique wins slot
    for t in matched:
        if t.phase in chosen or spend + t.cost > budget_multiplier:
            continue
        chosen[t.phase] = t
        spend += t.cost
    return [chosen[p] for p in PHASE_ORDER if p in chosen]


_RENDER = {   # composition fragments — data-driven, extend per technique as needed
    "framing":        lambda t: f"[{t.id}] You are a senior software engineer; be precise and terse.",
    "context":        lambda t: f"[{t.id}] Relevant exemplars/context are injected below when available.",
    "reasoning":      lambda t: f"[{t.id}] Reason step by step before producing the final artifact.",
    "decomposition":  lambda t: f"[{t.id}] Decompose into ordered sub-tasks; solve sequentially.",
    "ensembling":     lambda t: f"[{t.id}] Sample multiple candidates; return the consistent answer.",
    "self_criticism": lambda t: f"[{t.id}] Draft, plan verification questions, answer them WITHOUT the draft in context, revise.",
}


def compose(clarified: ClarifiedTask, techniques: list[TechniqueSpec]) -> EnhancedPrompt:
    system = "\n".join(_RENDER[t.phase](t) for t in techniques)
    provenance = {c: "task" for c in clarified.task.constraints}
    provenance.update({q: "answer" for q in clarified.answers})
    provenance.update({a: "assumption" for a in clarified.assumptions})
    user_parts = [f"GOAL: {clarified.task.goal}"]
    if clarified.task.constraints:
        user_parts.append("CONSTRAINTS: " + "; ".join(clarified.task.constraints))
    if clarified.answers:
        user_parts.append("CLARIFICATIONS: " + "; ".join(f"{k} -> {v}" for k, v in clarified.answers.items()))
    if clarified.assumptions:
        user_parts.append("ASSUMPTIONS (explicit): " + "; ".join(clarified.assumptions))
    if clarified.task.acceptance_criteria:
        user_parts.append("ACCEPTANCE: " + "; ".join(clarified.task.acceptance_criteria))
    return EnhancedPrompt(system=system, user="\n".join(user_parts),
                          techniques_applied=[t.id for t in techniques], provenance=provenance)


def cove_gate(prompt: EnhancedPrompt, clarified: ClarifiedTask) -> EnhancedPrompt:
    """Anti-fabrication: every constraint in the prompt must trace to task | answer | assumption.
    Structural (offline) check; LLM-backed factored CoVe runs on top in prod (verification/cove.py)."""
    log = []
    for constraint, source in prompt.provenance.items():
        traceable = (constraint in clarified.task.constraints
                     or constraint in clarified.answers
                     or constraint in clarified.assumptions)
        log.append(f"{'OK' if traceable else 'STRIPPED'}: [{source}] {constraint[:80]}")
        if not traceable:
            prompt.user = prompt.user.replace(constraint, "")
    prompt.cove_verified = all(line.startswith("OK") for line in log) if log else True
    prompt.verification_log = log
    return prompt
