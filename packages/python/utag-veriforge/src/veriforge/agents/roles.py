"""Five role specs (AgentForge decomposition) + default bindings. Bindings are DATA —
override per deployment; model names churn, do not hardcode in logic."""
from __future__ import annotations
from ..core.agent import Agent, AgentSpec
from ..core.binding import BindingRegistry, ModelBinding

SYSTEM = {
    "orchestrator": "Route tasks through the pipeline. Enforce budget, retries, escalation. JSON only.",
    "planner": ("Produce a minimal ordered plan. Each step: agent_role, description, target_files. "
                "Ground every file reference in the provided repo index. No speculative steps (YAGNI)."),
    "coder": ("Produce a MINIMAL unified diff for the given step. No drive-by edits, no TODOs, "
              "no placeholder code. Diff-based editing only."),
    "tester": ("Produce deterministic pytest tests: no sleeps, no network, no time coupling. "
               "Declare fail_to_pass (must flip red->green) and pass_to_pass (regression guard)."),
    "debugger": ("Repair the patch using ONLY the routed context provided. Change the minimum. "
                 "If the error locus is outside the patch, say so rather than thrash."),
    "critic": ("Binary verdict on the full trace: PASS iff all fail_to_pass pass and zero "
               "pass_to_pass regressions and consistency edges hold. FAIL with concrete reasons otherwise."),
}


def default_bindings() -> BindingRegistry:
    reg = BindingRegistry()
    # Placeholders — set real model names in deployment config. Critic on a DIFFERENT
    # provider than coder (decorrelated errors — AgentForge Eq.19).
    reg.bind("orchestrator", ModelBinding(provider="anthropic", model="SET_IN_CONFIG"))
    reg.bind("planner",      ModelBinding(provider="anthropic", model="SET_IN_CONFIG"))
    reg.bind("coder",        ModelBinding(provider="anthropic", model="SET_IN_CONFIG"))
    reg.bind("tester",       ModelBinding(provider="openai",    model="SET_IN_CONFIG"))
    reg.bind("debugger",     ModelBinding(provider="openai",    model="SET_IN_CONFIG"))
    reg.bind("critic",       ModelBinding(provider="openai",    model="SET_IN_CONFIG"))
    return reg


def build_agents(bindings: BindingRegistry, client_factory=None) -> dict[str, Agent]:
    return {name: Agent(AgentSpec(name=name, role=name, system_prompt=SYSTEM[name],
                                  binding=bindings.get(name)),
                        client=client_factory(name) if client_factory else None)
            for name in SYSTEM}
