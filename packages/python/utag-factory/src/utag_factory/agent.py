"""NL → structured job spec via the policy router (v2.16.0 F4).

A natural-language request becomes a validated `JobRequest` (which kind, what
payload, what resources) through the router + a StructuredPort — offline via the
FakeStructuredPort, live only when a provider credential is present. No NL ever
reaches a worker unstructured.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field

from utag_core.ai import ModelRouter, load_policies, load_providers
from utag_core.ai.adapters import RoutedStructuredAdapter
from utag_core.observe import Recorder
from utag_core.schemas import StrictSchema
from utag_core.schemas.factory import JobKind, ResourceContract


class JobRequest(StrictSchema):
    """Structured intent an agent extracts from a natural-language ask."""
    kind: JobKind
    script: str = Field(default="", description="python source for run-python jobs")
    target: str = Field(default="", description="generator target for generate-artifact jobs")
    prompt_yaml: str = Field(default="", description="prompt YAML for generate-artifact jobs")
    rationale: str = Field(default="")

    def to_payload(self) -> dict:
        if self.kind == JobKind.run_python:
            return {"script": self.script}
        if self.kind == JobKind.generate_artifact:
            return {"target": self.target, "prompt_yaml": self.prompt_yaml}
        raise ValueError(f"agent cannot build a payload for kind {self.kind.value}")


_SYSTEM = (
    "You translate a natural-language automation request into a JobRequest. "
    "Pick kind='run-python' for scripts/computation, 'generate-artifact' for "
    "producing typed artifacts from a generator target. Fill only the fields the "
    "chosen kind needs. Never invent credentials or network calls."
)


def plan_job(nl_request: str, *, task_kind: str = "offline-smoke",
             policies_path: Path | None = None, providers_path: Path | None = None,
             recorder: Recorder | None = None, port=None) -> JobRequest:
    root = Path.cwd()
    providers = load_providers(providers_path or root / "policies/ai-providers.yaml")
    policies = load_policies(policies_path or root / "policies/ai-router.yaml")
    policy = next(p for p in policies if p.task_kind == task_kind)
    rec = recorder or Recorder()
    decision = ModelRouter(providers).route(policy, recorder=rec)

    if port is None:
        from utag_generators.ai_bridge import port_for
        port = port_for(decision, providers)
    adapter = RoutedStructuredAdapter(decision, policy, port, recorder=rec)
    result = adapter.generate(prompt=nl_request, response_model=JobRequest, system=_SYSTEM)
    return result.output
