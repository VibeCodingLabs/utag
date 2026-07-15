"""Governed AI adapter layer (v2.14.0 Phase 5). No live keys required anywhere here."""
from utag_core.ai.router import (  # noqa: F401
    FakeProviderAdapter, ModelRouter, RoutingDecision, RoutingError,
    load_policies, load_providers,
)
