"""AI integration schemas: provider manifests, prompt contracts, router policy, evals."""
from __future__ import annotations

from pydantic import Field

from utag_core.schemas import SHA256, SLUG, StrictSchema


class ModelCapability(StrictSchema):
    id: str = Field(min_length=1)
    context_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    structured_output: bool = False
    tool_call: bool = False
    reasoning: bool = False


class AIProviderManifest(StrictSchema):
    id: str = Field(pattern=SLUG)
    name: str
    models: list[ModelCapability] = []
    env_credentials: list[str] = []


class PromptContract(StrictSchema):
    id: str = Field(pattern=SLUG)
    input_schema: str = Field(pattern=SLUG)
    output_schema: str = Field(pattern=SLUG)
    template_sha256: str = Field(pattern=SHA256)


class PromptRun(StrictSchema):
    contract_id: str = Field(pattern=SLUG)
    provider: str = Field(pattern=SLUG)
    model: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=SHA256)
    output_sha256: str = Field(pattern=SHA256)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)


class StructuredOutputContract(StrictSchema):
    id: str = Field(pattern=SLUG)
    schema_kind: str = Field(pattern=SLUG)
    max_repair_attempts: int = Field(ge=0, le=10)


class EvalCase(StrictSchema):
    id: str = Field(pattern=SLUG)
    input: str = Field(min_length=1)
    expected: str = Field(min_length=1)


class EvalResult(StrictSchema):
    case_id: str = Field(pattern=SLUG)
    passed: bool
    score: float | None = Field(default=None, ge=0, le=1)


class ModelRouterPolicy(StrictSchema):
    task_kind: str = Field(pattern=SLUG)
    max_cost_usd: float | None = Field(default=None, ge=0)
    max_latency_ms: float | None = Field(default=None, ge=0)
    require_structured_output: bool = False
    local_only: bool = False
    no_network: bool = False
    allow_fallback: bool = False
    prefer_cached: bool = True


TOP_LEVEL = [
    AIProviderManifest, ModelCapability, PromptContract, PromptRun,
    StructuredOutputContract, EvalCase, EvalResult, ModelRouterPolicy,
]

_SHA = "c" * 64
EXAMPLES = {
    "AIProviderManifest": {"id": "anthropic", "name": "Anthropic",
                           "models": [{"id": "claude-sonnet-4-6", "context_tokens": 200000, "output_tokens": 64000,
                                       "structured_output": True, "tool_call": True, "reasoning": True}],
                           "env_credentials": ["ANTHROPIC_API_KEY"]},
    "ModelCapability": {"id": "claude-sonnet-4-6", "context_tokens": 200000, "output_tokens": 64000,
                        "structured_output": True, "tool_call": True},
    "PromptContract": {"id": "generate-openapi", "input_schema": "module-spec",
                       "output_schema": "artifact-manifest", "template_sha256": _SHA},
    "PromptRun": {"contract_id": "generate-openapi", "provider": "anthropic", "model": "claude-sonnet-4-6",
                  "prompt_sha256": _SHA, "output_sha256": _SHA, "input_tokens": 900, "output_tokens": 210},
    "StructuredOutputContract": {"id": "module-spec-out", "schema_kind": "artifact-manifest", "max_repair_attempts": 3},
    "EvalCase": {"id": "case-1", "input": "generate a pet-store client", "expected": "compiles"},
    "EvalResult": {"case_id": "case-1", "passed": True, "score": 1.0},
    "ModelRouterPolicy": {"task_kind": "generate-openapi", "max_cost_usd": 0.05,
                          "require_structured_output": True, "allow_fallback": False},
}
