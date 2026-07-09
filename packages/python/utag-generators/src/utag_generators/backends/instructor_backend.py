"""Instructor backend — native structured output + validation-feedback retries.

instructor 1.15.x: from_provider("anthropic/...", "openai/...") etc.
Import is lazy so the package works without instructor installed (capability-gated).
"""
from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class InstructorPort:
    def __init__(self, provider: str, **client_kwargs):
        import instructor  # lazy: optional heavy dep

        self.name = f"instructor[{provider}]"
        self._client = instructor.from_provider(provider, **client_kwargs)

    def generate(self, *, prompt: str, response_model: type[M],
                 max_attempts: int = 3, system: str | None = None) -> M:
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        # instructor feeds ValidationError back to the model internally per retry
        return self._client.chat.completions.create(
            response_model=response_model, max_retries=max_attempts, messages=messages,
        )
