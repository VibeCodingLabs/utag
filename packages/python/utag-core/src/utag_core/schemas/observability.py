"""Observability schemas: traces, spans, metrics, logs, cost, model calls."""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from utag_core.schemas import SHA256, SLUG, StrictSchema

SPAN_NAME = r"^utag\.[a-z][a-z0-9._-]*$"
METRIC_NAME = r"^utag_[a-z0-9_]+$"


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    dead_letter = "dead-letter"


class RunSpan(StrictSchema):
    span_id: str = Field(pattern=SLUG)
    name: str = Field(pattern=SPAN_NAME)
    start_ms: float = Field(ge=0)
    end_ms: float = Field(ge=0)
    parent_span_id: str | None = None
    attributes: dict[str, str] = {}


class RunTrace(StrictSchema):
    run_id: str = Field(pattern=SLUG)
    spans: list[RunSpan] = []


class RunEvent(StrictSchema):
    run_id: str = Field(pattern=SLUG)
    name: str = Field(pattern=SPAN_NAME)
    attributes: dict[str, str] = {}


class MetricPoint(StrictSchema):
    name: str = Field(pattern=METRIC_NAME)
    value: float
    labels: dict[str, str] = {}


class LogRecord(StrictSchema):
    level: LogLevel
    message: str = Field(min_length=1)
    run_id: str | None = None
    span_id: str | None = None


class CostMetric(StrictSchema):
    run_id: str = Field(pattern=SLUG)
    usd: float = Field(ge=0)
    source: str = Field(pattern=SLUG)


class ModelCallTrace(StrictSchema):
    run_id: str = Field(pattern=SLUG)
    provider: str = Field(pattern=SLUG)
    model: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=SHA256)
    output_sha256: str = Field(pattern=SHA256)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)


class WorkerJobTrace(StrictSchema):
    job_id: str = Field(pattern=SLUG)
    status: JobStatus
    run_id: str | None = None


class ValidationTrace(StrictSchema):
    run_id: str = Field(pattern=SLUG)
    span_id: str = Field(pattern=SLUG)
    report_ref: str = Field(min_length=1)


TOP_LEVEL = [
    RunTrace, RunSpan, RunEvent, MetricPoint, LogRecord, CostMetric,
    ModelCallTrace, WorkerJobTrace, ValidationTrace,
]

_SHA = "b" * 64
EXAMPLES = {
    "RunTrace": {"run_id": "run-001", "spans": [
        {"span_id": "sp-1", "name": "utag.run", "start_ms": 0, "end_ms": 120.5, "attributes": {"target": "pydantic-models"}}]},
    "RunSpan": {"span_id": "sp-2", "name": "utag.generate", "start_ms": 1, "end_ms": 90, "parent_span_id": "sp-1"},
    "RunEvent": {"run_id": "run-001", "name": "utag.validate", "attributes": {"valid": "true"}},
    "MetricPoint": {"name": "utag_runs_total", "value": 1, "labels": {"target": "pydantic-models"}},
    "LogRecord": {"level": "info", "message": "generation complete", "run_id": "run-001"},
    "CostMetric": {"run_id": "run-001", "usd": 0.0042, "source": "anthropic"},
    "ModelCallTrace": {"run_id": "run-001", "provider": "anthropic", "model": "claude-sonnet-4-6",
                       "prompt_sha256": _SHA, "output_sha256": _SHA,
                       "input_tokens": 1200, "output_tokens": 300, "cost_usd": 0.0042, "latency_ms": 850},
    "WorkerJobTrace": {"job_id": "job-9", "status": "completed", "run_id": "run-001"},
    "ValidationTrace": {"run_id": "run-001", "span_id": "sp-3", "report_ref": "reports/run-001/validation.json"},
}
