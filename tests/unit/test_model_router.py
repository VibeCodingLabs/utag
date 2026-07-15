"""ModelRouter: policy enforcement, deterministic choice, explicit fallback, evidence."""
from __future__ import annotations

from pathlib import Path

import pytest

from utag_core.ai import FakeProviderAdapter, ModelRouter, RoutingError, load_policies, load_providers
from utag_core.ai.router import run_eval_suite
from utag_core.observe import Recorder
from utag_core.schemas.ai import ModelRouterPolicy

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = load_providers(ROOT / "policies/ai-providers.yaml")


def test_provider_manifests_validate_and_flag_local():
    ids = {p.id for p in PROVIDERS}
    assert {"anthropic", "fake-local"} <= ids
    fake = next(p for p in PROVIDERS if p.id == "fake-local")
    assert (fake.extensions or {}).get("local") is True


def test_structured_output_required_picks_capable_model():
    decision = ModelRouter(PROVIDERS).route(
        ModelRouterPolicy(task_kind="generate-openapi", require_structured_output=True))
    assert (decision.provider, decision.model) == ("anthropic", "claude-sonnet-4-6")
    assert not decision.fallback_used


def test_local_only_restricts_candidates():
    decision = ModelRouter(PROVIDERS).route(
        ModelRouterPolicy(task_kind="offline-smoke", local_only=True, allow_fallback=True))
    assert decision.provider == "fake-local"


def test_fallback_requires_explicit_policy():
    strict = ModelRouterPolicy(task_kind="offline-structured", local_only=True,
                               require_structured_output=True, allow_fallback=False)
    with pytest.raises(RoutingError):
        ModelRouter(PROVIDERS).route(strict)
    allowed = strict.model_copy(update={"allow_fallback": True})
    decision = ModelRouter(PROVIDERS).route(allowed)
    assert decision.fallback_used and "fallback" in decision.rationale


def test_routing_decision_logged_as_evidence():
    rec = Recorder(run_id="run-route")
    ModelRouter(PROVIDERS).route(
        ModelRouterPolicy(task_kind="generate-openapi"), recorder=rec)
    (event,) = rec.events
    assert event.name == "utag.ai.route"
    assert event.attributes["provider"] == "anthropic"


def test_repo_policies_all_routable():
    router = ModelRouter(PROVIDERS)
    for policy in load_policies(ROOT / "policies/ai-router.yaml"):
        router.route(policy)


def test_fake_adapter_deterministic_and_eval_suite_passes():
    adapter = FakeProviderAdapter()
    assert adapter.complete("x") == adapter.complete("x")
    results = run_eval_suite(ROOT / "evals/openapi-generation.yaml", adapter)
    assert results and all(r.passed for r in results)
