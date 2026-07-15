"""Provider Abstraction Layer. Agents bind to models via pure data — hot-swap = data change.
Primitive verified in-sandbox: instructor 1.15.4 `from_provider("provider/model")`."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field

try:
    import instructor
except ImportError:                                # keep importable in stripped envs
    instructor = None                              # type: ignore


class ModelBinding(BaseModel):
    provider: str                                  # "anthropic" | "openai" | "google" | "ollama" | ...
    model: str
    mode: Optional[str] = None                     # instructor Mode name override
    temperature: float = 0.0
    max_tokens: int = 4096
    fallbacks: list["ModelBinding"] = Field(default_factory=list)

    @property
    def provider_string(self) -> str:
        return f"{self.provider}/{self.model}"


def client_for(binding: ModelBinding) -> Any:
    """Build a normalized structured-output client. Requires provider API key in env."""
    if instructor is None:
        raise RuntimeError("instructor not installed")
    mode = getattr(instructor.Mode, binding.mode) if binding.mode else None
    return instructor.from_provider(binding.provider_string, mode=mode)


class BindingRegistry:
    """agent name -> binding. rebind() is the runtime hot-swap: next run() builds new client."""
    def __init__(self) -> None:
        self._bindings: dict[str, ModelBinding] = {}

    def bind(self, agent_name: str, binding: ModelBinding) -> None:
        self._bindings[agent_name] = binding

    rebind = bind                                   # alias: intent-revealing at call sites

    def get(self, agent_name: str) -> ModelBinding:
        return self._bindings[agent_name]

    def with_fallbacks(self, agent_name: str) -> list[ModelBinding]:
        b = self.get(agent_name)
        return [b, *b.fallbacks]
