"""pydantic-ai backend — Agent(output_type=...) with bounded retries.

pydantic-ai v2: Agent('anthropic:claude-...'), FallbackModel for resilience.
Lazy import; capability-gated.
"""
from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class PydanticAIPort:
    def __init__(self, model: Any):
        self.name = f"pydantic-ai[{model}]"
        self._model = model

    def generate(self, *, prompt: str, response_model: type[M],
                 max_attempts: int = 3, system: str | None = None) -> M:
        from pydantic_ai import Agent  # lazy

        agent = Agent(self._model, output_type=response_model,
                      retries=max_attempts, system_prompt=system or ())
        return agent.run_sync(prompt).output
