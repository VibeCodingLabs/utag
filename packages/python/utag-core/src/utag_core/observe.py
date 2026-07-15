"""Run observability (v2.14.0 Phase 4): spans, events, metrics per run.

Every record validates against the strict observability schemas
(`utag_core.schemas.observability`). Evidence is JSONL, one envelope per line:
`{"kind": "<schema-kind>", "record": {...}}`. Store location: `$UTAG_OBSERVE_DIR`
or `reports/observability/runs/`. Attribute values are caller-supplied strings —
never put credentials in attributes; nothing else is captured.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from utag_core.schemas import SCHEMAS
from utag_core.schemas.observability import MetricPoint, RunEvent, RunSpan, RunTrace

_OBSERVE_KINDS = ("run-trace", "run-span", "run-event", "metric-point", "log-record",
                  "cost-metric", "model-call-trace", "worker-job-trace", "validation-trace")


def store_dir() -> Path:
    return Path(os.environ.get("UTAG_OBSERVE_DIR", "reports/observability/runs"))


class Recorder:
    def __init__(self, run_id: str | None = None):
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self._t0 = time.monotonic()
        self._seq = 0
        self.spans: list[RunSpan] = []
        self.events: list[RunEvent] = []
        self.metrics: list[MetricPoint] = []
        self._stack: list[str] = []

    def _now_ms(self) -> float:
        return round((time.monotonic() - self._t0) * 1000, 3)

    @contextmanager
    def span(self, name: str, **attributes: str):
        self._seq += 1
        span_id = f"sp-{self._seq}"
        parent = self._stack[-1] if self._stack else None
        start = self._now_ms()
        self._stack.append(span_id)
        try:
            yield span_id
        finally:
            self._stack.pop()
            self.spans.append(RunSpan(span_id=span_id, name=name, start_ms=start,
                                      end_ms=self._now_ms(), parent_span_id=parent,
                                      attributes={k: str(v) for k, v in attributes.items()}))

    def event(self, name: str, **attributes: str) -> None:
        self.events.append(RunEvent(run_id=self.run_id, name=name,
                                    attributes={k: str(v) for k, v in attributes.items()}))

    def metric(self, name: str, value: float, **labels: str) -> None:
        self.metrics.append(MetricPoint(name=name, value=value,
                                        labels={k: str(v) for k, v in labels.items()}))

    def trace(self) -> RunTrace:
        return RunTrace(run_id=self.run_id, spans=self.spans)

    def to_jsonl(self) -> str:
        lines = [json.dumps({"kind": "run-trace",
                             "record": self.trace().model_dump(exclude_none=True)}, sort_keys=True)]
        lines += [json.dumps({"kind": "run-event", "record": e.model_dump(exclude_none=True)},
                             sort_keys=True) for e in self.events]
        lines += [json.dumps({"kind": "metric-point", "record": m.model_dump(exclude_none=True)},
                             sort_keys=True) for m in self.metrics]
        return "\n".join(lines) + "\n"

    def flush(self, directory: Path | None = None) -> Path:
        directory = directory or store_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.run_id}.jsonl"
        path.write_text(self.to_jsonl())
        return path


def validate_jsonl(text: str) -> list[str]:
    """Every line must be an envelope whose record validates against its schema kind."""
    problems = []
    for i, line in enumerate(text.splitlines(), 1):
        try:
            envelope = json.loads(line)
            kind = envelope["kind"]
            if kind not in _OBSERVE_KINDS:
                problems.append(f"line {i}: kind {kind!r} is not an observability schema")
                continue
            SCHEMAS[kind].model_validate(envelope["record"])
        except Exception as e:  # noqa: BLE001 — collect every problem, fail at end
            problems.append(f"line {i}: {e}")
    return problems


def load_runs(directory: Path | None = None) -> dict[str, str]:
    """run_id -> raw JSONL for every stored run."""
    directory = directory or store_dir()
    if not directory.is_dir():
        return {}
    return {p.stem: p.read_text() for p in sorted(directory.glob("*.jsonl"))}


def summarize(directory: Path | None = None) -> str:
    runs = load_runs(directory)
    spans = events = 0
    metric_totals: dict[str, float] = {}
    for text in runs.values():
        for line in text.splitlines():
            envelope = json.loads(line)
            if envelope["kind"] == "run-trace":
                spans += len(envelope["record"].get("spans", []))
            elif envelope["kind"] == "run-event":
                events += 1
            elif envelope["kind"] == "metric-point":
                rec = envelope["record"]
                metric_totals[rec["name"]] = metric_totals.get(rec["name"], 0) + rec["value"]
    lines = ["# Observability summary", "", f"- runs: {len(runs)}",
             f"- spans: {spans}", f"- events: {events}", ""]
    lines += [f"- `{name}`: {total:g}" for name, total in sorted(metric_totals.items())]
    return "\n".join(lines) + "\n"
