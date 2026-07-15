"""RoutedStructuredAdapter: telemetry, budgets, cache — all offline."""
from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from utag_core.ai.adapters import BudgetExceeded, FakeStructuredPort, RoutedStructuredAdapter
from utag_core.ai.router import RoutingDecision
from utag_core.observe import Recorder, validate_jsonl
from utag_core.schemas.ai import ModelRouterPolicy
from utag_core.schemas.observability import MetricPoint


class ScriptedPort:
    """Test port: returns a fixed instance, counts calls, exposes usage."""

    name = "scripted"

    def __init__(self, usage: dict | None = None):
        self.calls = 0
        self.last_usage = usage or {}

    def generate(self, *, prompt, response_model, max_attempts=3, system=None):
        self.calls += 1
        return MetricPoint(name="utag_runs_total", value=1)


def _adapter(port, recorder=None, cache_dir=None, **policy_over):
    policy = ModelRouterPolicy(task_kind="offline-smoke", **policy_over)
    decision = RoutingDecision(task_kind="offline-smoke", provider="fake-local",
                               model="fake-echo", rationale="test", candidates_considered=1)
    return RoutedStructuredAdapter(decision, policy, port, recorder=recorder, cache_dir=cache_dir)


def test_call_records_prompt_run_and_trace_evidence():
    rec = Recorder(run_id="run-adapter")
    port = ScriptedPort(usage={"input_tokens": 10, "output_tokens": 2, "cost_usd": 0.001})
    result = _adapter(port, recorder=rec).generate(prompt="p", response_model=MetricPoint)
    assert result.prompt_run.provider == "fake-local"
    assert result.prompt_run.prompt_sha256 == result.call_trace.prompt_sha256
    assert result.call_trace.input_tokens == 10 and result.call_trace.cost_usd == 0.001
    assert result.call_trace.run_id == "run-adapter"
    kinds = [k for k, _ in rec.records]
    assert kinds == ["prompt-run", "model-call-trace"]
    assert any(s.name == "utag.ai.call" for s in rec.spans)
    assert validate_jsonl(rec.to_jsonl()) == []  # evidence is schema-valid end to end


def test_cache_hit_skips_port_and_records_metric(tmp_path):
    rec = Recorder(run_id="run-cache")
    port = ScriptedPort()
    adapter = _adapter(port, recorder=rec, cache_dir=tmp_path, prefer_cached=True)
    first = adapter.generate(prompt="p", response_model=MetricPoint)
    second = adapter.generate(prompt="p", response_model=MetricPoint)
    assert port.calls == 1
    assert not first.cached and second.cached
    assert second.output == first.output
    assert any(m.name == "utag_cache_hits_total" for m in rec.metrics)


def test_latency_budget_breach_raises_and_records_event():
    rec = Recorder(run_id="run-budget")
    with pytest.raises(BudgetExceeded) as exc:
        _adapter(ScriptedPort(), recorder=rec, max_latency_ms=0.000001).generate(
            prompt="p", response_model=MetricPoint)
    assert exc.value.finding.code == "latency-budget-exceeded"
    assert any(e.name == "utag.ai.budget_exceeded" for e in rec.events)


def test_cost_budget_breach_and_unverifiable_warning():
    pricey = ScriptedPort(usage={"cost_usd": 1.0})
    with pytest.raises(BudgetExceeded) as exc:
        _adapter(pricey, max_cost_usd=0.01).generate(prompt="p", response_model=MetricPoint)
    assert exc.value.finding.code == "cost-budget-exceeded"
    # no cost reported + cost cap -> explicit warning finding, not silence
    result = _adapter(ScriptedPort(), max_cost_usd=0.01).generate(prompt="p", response_model=MetricPoint)
    assert [f.code for f in result.findings] == ["cost-unverifiable"]


def test_fake_structured_port_returns_valid_example():
    out = FakeStructuredPort().generate(prompt="p", response_model=MetricPoint)
    assert isinstance(out, MetricPoint) and out.name.startswith("utag_")


def test_pydantic_ai_function_model_through_adapter():
    """Full path with pydantic-ai's offline FunctionModel behind the real port."""
    pytest.importorskip("pydantic_ai")
    from pydantic_ai.models.function import AgentInfo, FunctionModel
    from pydantic_ai.messages import ModelResponse, ToolCallPart

    from utag_generators.backends import PydanticAIPort

    def respond(messages, info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0]
        payload = json.dumps({"name": "utag_ai_tokens_input_total", "value": 42})
        return ModelResponse(parts=[ToolCallPart(tool.name, payload)])

    rec = Recorder(run_id="run-fn")
    port = PydanticAIPort(FunctionModel(respond))
    result = _adapter(port, recorder=rec).generate(prompt="emit a metric", response_model=MetricPoint)
    assert result.output.value == 42
    assert result.call_trace.output_sha256 != result.call_trace.prompt_sha256
