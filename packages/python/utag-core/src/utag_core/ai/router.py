"""Model router: pick a provider/model under explicit policy; log every decision.

Providers come from a checked-in manifest (`policies/ai-providers.yaml`) validated
against `AIProviderManifest` — no network, no live keys. A provider is "local"
when its manifest carries `extensions: {local: true}`. Fallback never happens
implicitly: it must be allowed by the policy, and the decision rationale says so.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from utag_core.schemas.ai import AIProviderManifest, EvalCase, EvalResult, ModelRouterPolicy


class RoutingError(Exception):
    pass


@dataclass
class RoutingDecision:
    task_kind: str
    provider: str
    model: str
    rationale: str
    candidates_considered: int
    fallback_used: bool = False

    def to_json(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True)


def _is_local(p: AIProviderManifest) -> bool:
    return bool((p.extensions or {}).get("local"))


class ModelRouter:
    def __init__(self, providers: list[AIProviderManifest]):
        self.providers = providers

    def route(self, policy: ModelRouterPolicy, recorder=None) -> RoutingDecision:
        candidates = sorted(
            ((p, m) for p in self.providers for m in p.models),
            key=lambda pm: (pm[0].id, pm[1].id))
        if policy.local_only or policy.no_network:
            candidates = [(p, m) for p, m in candidates if _is_local(p)]
        considered = len(candidates)
        strict = [(p, m) for p, m in candidates
                  if m.structured_output or not policy.require_structured_output]
        fallback_used = False
        if strict:
            provider, model = strict[0]
            rationale = "first candidate satisfying policy (deterministic provider/model order)"
        elif candidates and policy.allow_fallback:
            provider, model = candidates[0]
            fallback_used = True
            rationale = ("policy-sanctioned fallback: no structured-output model available; "
                         "adapter must run the bounded text-repair loop")
        else:
            raise RoutingError(
                f"no candidate for task {policy.task_kind!r} "
                f"(considered {considered}, fallback allowed: {policy.allow_fallback})")
        decision = RoutingDecision(task_kind=policy.task_kind, provider=provider.id,
                                   model=model.id, rationale=rationale,
                                   candidates_considered=considered,
                                   fallback_used=fallback_used)
        if recorder is not None:
            recorder.event("utag.ai.route", task_kind=policy.task_kind,
                           provider=provider.id, model=model.id,
                           fallback=str(fallback_used).lower())
        return decision


class FakeProviderAdapter:
    """Deterministic offline adapter: proves routing/eval plumbing in tests and
    `utag ai eval`. Output is a pure function of the input — clearly not a model."""

    provider_id = "fake-local"

    def complete(self, prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        return f"fake-completion({digest}): {prompt}"


def load_providers(path: Path) -> list[AIProviderManifest]:
    payload = yaml.safe_load(path.read_text())
    return [AIProviderManifest.model_validate(p) for p in payload["providers"]]


def load_policies(path: Path) -> list[ModelRouterPolicy]:
    payload = yaml.safe_load(path.read_text())
    return [ModelRouterPolicy.model_validate(p) for p in payload["policies"]]


def run_eval_suite(path: Path, adapter: FakeProviderAdapter | None = None) -> list[EvalResult]:
    """Substring-match eval harness over an adapter (fake by default — offline)."""
    adapter = adapter or FakeProviderAdapter()
    payload = yaml.safe_load(path.read_text())
    results = []
    for raw in payload["cases"]:
        case = EvalCase.model_validate(raw)
        output = adapter.complete(case.input)
        passed = case.expected in output
        results.append(EvalResult(case_id=case.id, passed=passed,
                                  score=1.0 if passed else 0.0))
    return results
