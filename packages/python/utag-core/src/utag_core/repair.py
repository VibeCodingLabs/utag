"""Bounded validation-feedback repair loop (spec: repair-engine, retry_policy).

Identical semantics across every backend: raw text in, validated model out.
Repairable = pydantic ValidationError / JSON decode. Terminal = everything else.
Hard stops: attempt budget, identical consecutive failure (hash + errors).
"""
from __future__ import annotations

import hashlib
import json
from typing import Callable, TypeVar

from pydantic import BaseModel, ValidationError

M = TypeVar("M", bound=BaseModel)

DEFAULT_MAX_ATTEMPTS = 3
HARD_MAX_ATTEMPTS = 10


class RepairExhausted(RuntimeError):
    def __init__(self, attempts: int, last_errors: list[dict]):
        self.attempts = attempts
        self.last_errors = last_errors
        super().__init__(f"repair exhausted after {attempts} attempts: {last_errors}")


class TerminalGenerationError(RuntimeError):
    """Non-repairable failure (auth, network, policy). Never retried."""


def format_validation_errors(errors: list[dict]) -> str:
    """pydantic ValidationError.errors() -> concise model-facing feedback."""
    lines = []
    for e in errors:
        loc = ".".join(str(p) for p in e.get("loc", ())) or "<root>"
        lines.append(f"- {loc}: {e.get('msg', 'invalid')} (type={e.get('type', '?')})")
    return "Your previous output failed validation:\n" + "\n".join(lines) + "\nReturn corrected JSON only."


def repair_loop(
    call: Callable[[str | None], str],
    response_model: type[M],
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> tuple[M, int]:
    """call(feedback|None) -> raw JSON text. Returns (validated, attempts_used)."""
    if not 1 <= max_attempts <= HARD_MAX_ATTEMPTS:
        raise ValueError(f"max_attempts must be in [1, {HARD_MAX_ATTEMPTS}]")
    feedback: str | None = None
    prev_sig: str | None = None
    last_errors: list[dict] = []
    for attempt in range(1, max_attempts + 1):
        raw = call(feedback)
        try:
            return response_model.model_validate_json(raw), attempt
        except ValidationError as exc:
            last_errors = [dict(e) for e in exc.errors(include_url=False)]
        except json.JSONDecodeError as exc:  # some ports pre-decode
            last_errors = [{"loc": (), "msg": str(exc), "type": "json_invalid"}]
        sig = hashlib.sha256(raw.encode()).hexdigest() + json.dumps(last_errors, default=str, sort_keys=True)
        if sig == prev_sig:  # identical artifact + identical errors -> stop early (spec rule)
            raise RepairExhausted(attempt, last_errors)
        prev_sig = sig
        feedback = format_validation_errors(last_errors)
    raise RepairExhausted(max_attempts, last_errors)
