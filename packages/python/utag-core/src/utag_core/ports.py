"""Provider-agnostic model ports (spec: ModelPort; moat: one repair contract, N backends)."""
from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel
import re

from utag_core.repair import repair_loop

M = TypeVar("M", bound=BaseModel)


@runtime_checkable
class ModelPort(Protocol):
    """Lowest common denominator: text in, text out."""
    name: str

    def complete(self, *, prompt: str, system: str | None = None,
                 feedback: str | None = None) -> str: ...


@runtime_checkable
class StructuredPort(Protocol):
    """Backends with native structured output (instructor, pydantic-ai)."""
    name: str

    def generate(self, *, prompt: str, response_model: type[M],
                 max_attempts: int = 3, system: str | None = None) -> M: ...


class TextPortStructuredAdapter:
    """Lift any ModelPort into a StructuredPort via the shared repair loop.

    This is what makes the pi-RPC bridge (text only) behave identically to
    instructor/pydantic-ai native validation retries.
    """

    def __init__(self, port: ModelPort):
        self._port = port
        self.name = f"repair[{port.name}]"

    def generate(self, *, prompt: str, response_model: type[M],
                 max_attempts: int = 3, system: str | None = None) -> M:
        schema = response_model.model_json_schema()
        base = (
            f"{prompt}\n\nRespond with a single JSON object conforming to this JSON Schema "
            f"(2020-12). No prose, no code fences.\nSchema:\n{schema}"
        )

        def call(feedback: str | None) -> str:
            p = base if feedback is None else f"{base}\n\n{feedback}"
            raw = self._port.complete(prompt=p, system=system)
            return _strip_fences(raw)

        validated, _ = repair_loop(call, response_model, max_attempts=max_attempts)
        return validated


def _strip_fences(raw: str) -> str:
    s = raw.strip()
    m = re.search(r"```[a-zA-Z]*\n(.*?)```", s, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return s
