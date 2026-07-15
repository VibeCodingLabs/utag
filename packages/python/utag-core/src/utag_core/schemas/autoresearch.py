"""Autoresearch task-execution schemas: tasks, plans, evidence, receipts."""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from utag_core.schemas import SHA256, SLUG, StrictSchema


class TaskMode(str, Enum):
    research = "research"
    implement = "implement"
    dry_run = "dry-run"


class StepKind(str, Enum):
    research = "research"
    plan = "plan"
    schema = "schema"
    tests = "tests"
    implementation = "implementation"
    validation = "validation"
    docs = "docs"
    receipt = "receipt"


class StepStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class TaskStatus(str, Enum):
    completed = "completed"
    failed = "failed"
    partial = "partial"


class EvidenceKind(str, Enum):
    command = "command"
    file = "file"
    metric = "metric"
    log = "log"


class TaskGate(StrictSchema):
    name: str = Field(pattern=SLUG)
    command: str = Field(min_length=1)


class AutoresearchTask(StrictSchema):
    id: str = Field(pattern=SLUG)
    goal: str = Field(min_length=1)
    mode: TaskMode
    inputs: list[str] = []
    required_outputs: list[str] = []
    gates: list[TaskGate] = []
    done_when: list[str] = []


class AutoresearchStep(StrictSchema):
    id: str = Field(pattern=SLUG)
    kind: StepKind
    description: str
    status: StepStatus = StepStatus.pending


class AutoresearchPlan(StrictSchema):
    task_id: str = Field(pattern=SLUG)
    steps: list[AutoresearchStep]


class AutoresearchEvidence(StrictSchema):
    step_id: str = Field(pattern=SLUG)
    kind: EvidenceKind
    ref: str = Field(min_length=1)
    sha256: str | None = Field(default=None, pattern=SHA256)


class AutoresearchResult(StrictSchema):
    task_id: str = Field(pattern=SLUG)
    status: TaskStatus
    evidence: list[AutoresearchEvidence] = []


class AutoresearchMetric(StrictSchema):
    name: str = Field(pattern=SLUG)
    value: float
    unit: str | None = None


class AutoresearchDecision(StrictSchema):
    id: str = Field(pattern=SLUG)
    decision: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class GateResult(StrictSchema):
    name: str = Field(pattern=SLUG)
    passed: bool


class TaskCompletionReceipt(StrictSchema):
    task_id: str = Field(pattern=SLUG)
    commands_run: list[str] = []
    files_changed: list[str] = []
    gates: list[GateResult] = []
    next_tasks: list[str] = []


TOP_LEVEL = [
    AutoresearchTask, AutoresearchPlan, AutoresearchStep, AutoresearchEvidence,
    AutoresearchResult, AutoresearchMetric, AutoresearchDecision, TaskCompletionReceipt,
]

EXAMPLES = {
    "AutoresearchTask": {"id": "ar-ui-observability-dashboard",
                         "goal": "Generate the observability dashboard from design.yaml and validate it.",
                         "mode": "implement", "inputs": ["design.yaml"],
                         "required_outputs": ["packages/ui/src/generated/components/RunTimeline.tsx"],
                         "gates": [{"name": "schema", "command": "python scripts/validate_schemas.py --root ."}],
                         "done_when": ["all_gates_pass"]},
    "AutoresearchPlan": {"task_id": "ar-ui-observability-dashboard",
                         "steps": [{"id": "s1", "kind": "schema", "description": "emit schemas", "status": "pending"}]},
    "AutoresearchStep": {"id": "s1", "kind": "tests", "description": "write failing tests first", "status": "pending"},
    "AutoresearchEvidence": {"step_id": "s1", "kind": "command", "ref": "uv run pytest -q"},
    "AutoresearchResult": {"task_id": "ar-ui-observability-dashboard", "status": "completed",
                           "evidence": [{"step_id": "s1", "kind": "metric", "ref": "passed_tests=380"}]},
    "AutoresearchMetric": {"name": "passed-tests", "value": 380, "unit": "tests"},
    "AutoresearchDecision": {"id": "d1", "decision": "use pydantic emission",
                             "rationale": "already a core dependency; deterministic"},
    "TaskCompletionReceipt": {"task_id": "ar-ui-observability-dashboard",
                              "commands_run": ["uv run pytest -q"], "files_changed": ["design.yaml"],
                              "gates": [{"name": "schema", "passed": True}], "next_tasks": []},
}
