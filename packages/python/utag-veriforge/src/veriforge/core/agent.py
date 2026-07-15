"""Agent = (Spec, Binding). Structured output + automatic schema-retry via Instructor."""
from __future__ import annotations
from typing import Any, Protocol, Type, TypeVar
from pydantic import BaseModel, Field
from .binding import ModelBinding, client_for

TOut = TypeVar("TOut", bound=BaseModel)


class LLMClient(Protocol):
    """Minimal protocol so tests inject fakes; instructor clients satisfy it."""
    def create(self, *, messages: list[dict], response_model: Type[BaseModel],
               max_retries: int, **kw: Any) -> BaseModel: ...


class AgentSpec(BaseModel):
    name: str
    role: str
    system_prompt: str
    binding: ModelBinding
    max_retries: int = 3                            # Instructor feeds ValidationError back automatically


class Agent:
    def __init__(self, spec: AgentSpec, client: LLMClient | None = None) -> None:
        self.spec = spec
        self._client = client                       # None => lazy-build from binding

    # -- hot-swap ---------------------------------------------------------
    def rebind(self, binding: ModelBinding) -> None:
        self.spec = self.spec.model_copy(update={"binding": binding})
        self._client = None                         # force rebuild with new provider

    # -- execution --------------------------------------------------------
    def _client_or_build(self) -> Any:
        if self._client is None:
            self._client = client_for(self.spec.binding).chat.completions
        return self._client

    def run(self, user_content: str, response_model: Type[TOut]) -> TOut:
        client = self._client_or_build()
        return client.create(
            messages=[{"role": "system", "content": self.spec.system_prompt},
                      {"role": "user", "content": user_content}],
            response_model=response_model,
            max_retries=self.spec.max_retries,
            temperature=self.spec.binding.temperature,
            max_tokens=self.spec.binding.max_tokens,
        )
