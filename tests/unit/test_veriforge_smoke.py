"""Offline smoke tests — no API keys, no network. Proves: typed contracts, hot-swap,
ambiguity loop convergence, technique selection/gating, error routing, anti-fabrication gate."""
import pytest
from veriforge.core.schemas import (AmbiguityDimension, AmbiguityReport, ClarifyingQuestion,
                                    Complexity, ErrorClass, ExecutionResult, Patch,
                                    TaskProfile, TaskSpec)
from veriforge.core.binding import BindingRegistry, ModelBinding
from veriforge.core.errors import ROUTING, classify
from veriforge.intake.ambiguity import clarify_loop
from veriforge.pee.enhancer import compose, cove_gate, select
from veriforge.pee.techniques import PHASE_ORDER, load_registry


# ---- contracts ---------------------------------------------------------------
def test_patch_rejects_non_diff():
    with pytest.raises(Exception):
        Patch(unified_diff="print('hello')", files_touched=["a.py"])
    Patch(unified_diff="--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b", files_touched=["x.py"])


def test_ambiguity_overall_is_weakest_link():
    r = AmbiguityReport(scores={AmbiguityDimension.scope: 0.9, AmbiguityDimension.io_contract: 0.4})
    assert r.overall == 0.4


# ---- hot-swap ----------------------------------------------------------------
def test_binding_hot_swap():
    reg = BindingRegistry()
    reg.bind("coder", ModelBinding(provider="anthropic", model="model-a"))
    assert reg.get("coder").provider_string == "anthropic/model-a"
    reg.rebind("coder", ModelBinding(provider="ollama", model="local-b",
                                     fallbacks=[ModelBinding(provider="openai", model="c")]))
    assert reg.get("coder").provider_string == "ollama/local-b"
    assert [b.provider_string for b in reg.with_fallbacks("coder")] == ["ollama/local-b", "openai/c"]


# ---- ambiguity gate ----------------------------------------------------------
class ScriptedScorer:
    """Ambiguity resolves as answers arrive: 0 answers -> 0.3, 1 -> 0.6, 2+ -> 0.9."""
    def score(self, task, answers):
        overall = [0.3, 0.6, 0.9][min(len(answers), 2)]
        open_qs = [] if overall >= 0.85 else [
            ClarifyingQuestion(dimension=AmbiguityDimension.scope, question=f"q{len(answers)}",
                               options=["a", "b"])]
        return AmbiguityReport(scores={d: overall for d in AmbiguityDimension},
                               open_questions=open_qs)


class ScriptedAsker:
    def __init__(self): self.calls = 0
    def ask(self, questions):
        self.calls += 1
        return {q.question: "a" for q in questions}


def test_clarify_loop_converges_then_stops():
    asker = ScriptedAsker()
    out = clarify_loop(TaskSpec(goal="build thing"), ScriptedScorer(), asker)
    assert out.final_ambiguity >= 0.85 and asker.calls == 2 and not out.assumptions


def test_clarify_loop_records_assumptions_when_stuck():
    class StuckScorer:
        def score(self, task, answers):
            return AmbiguityReport(scores={d: 0.5 for d in AmbiguityDimension},
                                   open_questions=[ClarifyingQuestion(
                                       dimension=AmbiguityDimension.environment, question="env?")])
    out = clarify_loop(TaskSpec(goal="x"), StuckScorer(), ScriptedAsker(), max_rounds=2)
    assert out.assumptions and "UNRESOLVED[environment]" in out.assumptions[0]


# ---- PEE ---------------------------------------------------------------------
def test_registry_gate_is_honest():
    reg = load_registry()
    assert reg.expected_count == 58 and len(reg.techniques) == 49 and not reg.complete


def test_selection_phase_ordered_and_cove_forced():
    reg = load_registry()
    profile = TaskProfile(complexity=Complexity.complex, artifact_type="code")
    chosen = select(profile, reg)
    phases = [t.phase for t in chosen]
    assert phases == [p for p in PHASE_ORDER if p in phases]        # fixed composition order
    assert len(phases) == len(set(phases))                          # one per phase
    assert "chain_of_verification" in [t.id for t in chosen]        # CoVe always last-phase


def test_cove_gate_strips_untraceable_constraints():
    from veriforge.core.schemas import ClarifiedTask
    task = TaskSpec(goal="g", constraints=["must use python 3.12"])
    clarified = ClarifiedTask(task=task, final_ambiguity=0.9)
    prompt = compose(clarified, select(task.profile, load_registry()))
    prompt.provenance["fabricated constraint never stated"] = "task"   # simulate fabrication
    gated = cove_gate(prompt, clarified)
    assert not gated.cove_verified
    assert any(line.startswith("STRIPPED") for line in gated.verification_log)


# ---- error routing -----------------------------------------------------------
def test_error_routing_table_matches_source_doc():
    assert ROUTING[ErrorClass.flaky_test].handler.startswith("QUARANTINE")
    assert "ALWAYS" in ROUTING[ErrorClass.security].escalation
    assert classify(ExecutionResult(exit_code=1, stderr="SyntaxError: invalid syntax")
                    ).error_class == ErrorClass.syntax_type
    assert classify(ExecutionResult(exit_code=1, stderr="Connection refused"), phase="build"
                    ).error_class == ErrorClass.environment
    assert classify(ExecutionResult(exit_code=1, stdout="1 FAILED"), reruns_inconsistent=True
                    ).error_class == ErrorClass.flaky_test
    assert classify(ExecutionResult(exit_code=1, stdout="assert 2 == 3 FAILED")
                    ).error_class == ErrorClass.logic
