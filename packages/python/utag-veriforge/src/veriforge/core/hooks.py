"""Lifecycle hooks — the observability + extension seam."""
from __future__ import annotations
from enum import Enum
from typing import Any, Callable


class HookEvent(str, Enum):
    pre_clarify = "pre_clarify"; post_enhance = "post_enhance"
    pre_plan = "pre_plan"; post_patch = "post_patch"
    pre_execute = "pre_execute"; post_verify = "post_verify"
    on_error = "on_error"; on_verdict = "on_verdict"


class HookRegistry:
    def __init__(self) -> None:
        self._subs: dict[HookEvent, list[Callable[[dict], None]]] = {e: [] for e in HookEvent}

    def on(self, event: HookEvent, fn: Callable[[dict], None]) -> None:
        self._subs[event].append(fn)

    def fire(self, event: HookEvent, payload: dict[str, Any]) -> None:
        for fn in self._subs[event]:
            fn(payload)                              # subscriber errors must not kill pipeline
