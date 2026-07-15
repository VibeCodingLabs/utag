"""Routed structured calls with telemetry, budgets, and caching (v2.15.0 phase D).

The adapter wraps any `StructuredPort` chosen by the router. Every call records
a `utag.ai.call` span plus `prompt-run` and `model-call-trace` evidence
(prompt/output sha256; tokens/cost/latency when the port exposes `last_usage`).
Budgets come from the routing policy: a breach raises `BudgetExceeded` and is
recorded — never a silent overage. `prefer_cached` uses a sha-keyed JSON cache;
hits are recorded as `utag_cache_hits_total` and skip the port entirely.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from utag_core.ai.router import RoutingDecision
from utag_core.schemas.ai import ModelRouterPolicy, PromptRun
from utag_core.schemas.core import Severity, ValidationFinding
from utag_core.schemas.observability import ModelCallTrace


class BudgetExceeded(Exception):
    def __init__(self, finding: ValidationFinding):
        super().__init__(finding.message)
        self.finding = finding


@dataclass
class CallResult:
    output: BaseModel
    prompt_run: PromptRun
    call_trace: ModelCallTrace
    cached: bool
    findings: list[ValidationFinding]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class RoutedStructuredAdapter:
    def __init__(self, decision: RoutingDecision, policy: ModelRouterPolicy, port,
                 recorder=None, cache_dir: Path | None = None):
        self.decision = decision
        self.policy = policy
        self.port = port
        self.recorder = recorder
        self.cache_dir = cache_dir

    def _cache_path(self, prompt_sha: str) -> Path | None:
        if self.cache_dir is None or not self.policy.prefer_cached:
            return None
        return Path(self.cache_dir) / f"{prompt_sha}.json"

    def generate(self, *, prompt: str, response_model: type[BaseModel],
                 system: str | None = None, max_attempts: int = 3) -> CallResult:
        contract_id = f"{self.policy.task_kind}-{response_model.__name__.lower()}"
        prompt_sha = _sha(f"{self.decision.provider}/{self.decision.model}\n{system or ''}\n{prompt}")
        findings: list[ValidationFinding] = []

        cache_path = self._cache_path(prompt_sha)
        if cache_path is not None and cache_path.is_file():
            output = response_model.model_validate_json(cache_path.read_text())
            if self.recorder is not None:
                self.recorder.metric("utag_cache_hits_total", 1, provider=self.decision.provider)
            return self._result(output, prompt_sha, latency_ms=0.0, usage={}, cached=True,
                                contract_id=contract_id, findings=findings)

        t0 = time.monotonic()
        if self.recorder is not None:
            with self.recorder.span("utag.ai.call", provider=self.decision.provider,
                                    model=self.decision.model, task_kind=self.policy.task_kind):
                output = self.port.generate(prompt=prompt, response_model=response_model,
                                            max_attempts=max_attempts, system=system)
        else:
            output = self.port.generate(prompt=prompt, response_model=response_model,
                                        max_attempts=max_attempts, system=system)
        latency_ms = round((time.monotonic() - t0) * 1000, 3)
        usage = dict(getattr(self.port, "last_usage", None) or {})

        self._enforce_budgets(latency_ms, usage, findings)

        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(output.model_dump_json())
        return self._result(output, prompt_sha, latency_ms, usage, cached=False,
                            contract_id=contract_id, findings=findings)

    def _enforce_budgets(self, latency_ms: float, usage: dict,
                         findings: list[ValidationFinding]) -> None:
        cost = usage.get("cost_usd")
        if self.policy.max_cost_usd is not None:
            if cost is None:
                findings.append(ValidationFinding(
                    severity=Severity.warn, code="cost-unverifiable",
                    message=f"policy caps cost at ${self.policy.max_cost_usd} but the "
                            f"provider returned no cost — budget unverifiable"))
            elif cost > self.policy.max_cost_usd:
                self._breach("cost-budget-exceeded",
                             f"call cost ${cost} > policy max ${self.policy.max_cost_usd}")
        if self.policy.max_latency_ms is not None and latency_ms > self.policy.max_latency_ms:
            self._breach("latency-budget-exceeded",
                         f"call took {latency_ms}ms > policy max {self.policy.max_latency_ms}ms")

    def _breach(self, code: str, message: str) -> None:
        finding = ValidationFinding(severity=Severity.error, code=code, message=message)
        if self.recorder is not None:
            self.recorder.event("utag.ai.budget_exceeded", code=code,
                                provider=self.decision.provider, model=self.decision.model)
        raise BudgetExceeded(finding)

    def _result(self, output: BaseModel, prompt_sha: str, latency_ms: float,
                usage: dict, cached: bool, contract_id: str,
                findings: list[ValidationFinding]) -> CallResult:
        output_sha = _sha(output.model_dump_json())
        common = dict(prompt_sha256=prompt_sha, output_sha256=output_sha,
                      input_tokens=usage.get("input_tokens"),
                      output_tokens=usage.get("output_tokens"),
                      cost_usd=usage.get("cost_usd"), latency_ms=latency_ms)
        prompt_run = PromptRun(contract_id=contract_id, provider=self.decision.provider,
                               model=self.decision.model, **common)
        run_id = self.recorder.run_id if self.recorder is not None else "run-detached"
        call_trace = ModelCallTrace(run_id=run_id, provider=self.decision.provider,
                                    model=self.decision.model, **common)
        if self.recorder is not None:
            self.recorder.record("prompt-run", prompt_run)
            self.recorder.record("model-call-trace", call_trace)
        return CallResult(output=output, prompt_run=prompt_run, call_trace=call_trace,
                          cached=cached, findings=findings)


class FakeStructuredPort:
    """Deterministic offline StructuredPort: returns the schema's canonical
    example for the requested model. Proves the routed-call plumbing without a
    provider — clearly not a model."""

    name = "fake-local[structured]"
    last_usage = {"input_tokens": 1, "output_tokens": 1, "cost_usd": 0.0}

    def generate(self, *, prompt: str, response_model: type[BaseModel],
                 max_attempts: int = 3, system: str | None = None) -> BaseModel:
        from utag_core.schemas import EXAMPLES, SCHEMAS, kind_of
        kind = kind_of(response_model)
        if kind in SCHEMAS and SCHEMAS[kind] is response_model:
            return response_model.model_validate(EXAMPLES[kind])
        return response_model.model_construct()
