"""Bridge routed AI decisions to live StructuredPorts (v2.15.0 phase D).

Local-flagged providers get the deterministic `FakeStructuredPort`; everything
else constructs a `PydanticAIPort` for the routed provider/model. Construction
is offline — no network until `.generate()`.
"""
from __future__ import annotations

import os

from utag_core.ai.adapters import FakeStructuredPort
from utag_core.ai.router import RoutingDecision
from utag_core.schemas.ai import AIProviderManifest

#: provider id -> pydantic-ai model prefix
PYDANTIC_AI_PREFIX = {"anthropic": "anthropic", "openai": "openai", "google": "google-gla"}


def manifest_for(decision: RoutingDecision, providers: list[AIProviderManifest]) -> AIProviderManifest:
    try:
        return next(p for p in providers if p.id == decision.provider)
    except StopIteration:
        raise ValueError(f"routed provider {decision.provider!r} has no manifest") from None


def credentials_present(manifest: AIProviderManifest) -> bool:
    return not manifest.env_credentials or any(os.environ.get(v) for v in manifest.env_credentials)


def port_for(decision: RoutingDecision, providers: list[AIProviderManifest]):
    manifest = manifest_for(decision, providers)
    if (manifest.extensions or {}).get("local"):
        return FakeStructuredPort()
    from utag_generators.backends import PydanticAIPort  # lazy: pydantic-ai import
    prefix = PYDANTIC_AI_PREFIX.get(decision.provider, decision.provider)
    return PydanticAIPort(f"{prefix}:{decision.model}")
