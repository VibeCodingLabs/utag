"""Typed inter-agent contracts. Every boundary artifact is a Pydantic v2 model."""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ---- Task intake ------------------------------------------------------------
class Complexity(str, Enum):
    trivial = "trivial"; standard = "standard"; complex = "complex"


class TaskProfile(BaseModel):
    """Facets reuse master_mapped_taxonomy.md vocabulary."""
    domain: str = "software-engineering"
    stack_layer: list[str] = Field(default_factory=lambda: ["backend"])
    artifact_type: str = "code"
    complexity: Complexity = Complexity.standard
    determinism: bool = True                      # temperature=0 pipelines by default
    budget_usd: float = 1.0                       # per-task cost guardrail


class TaskSpec(BaseModel):
    goal: str
    context_files: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    profile: TaskProfile = Field(default_factory=TaskProfile)


# ---- Ambiguity gate ----------------------------------------------------------
class AmbiguityDimension(str, Enum):
    scope = "scope"; io_contract = "io_contract"; constraints = "constraints"
    environment = "environment"; success_criteria = "success_criteria"; priority = "priority"


class ClarifyingQuestion(BaseModel):
    dimension: AmbiguityDimension
    question: str
    options: list[str] = Field(default_factory=list, max_length=4)


class AmbiguityReport(BaseModel):
    scores: dict[AmbiguityDimension, float]       # each in [0,1]
    open_questions: list[ClarifyingQuestion] = Field(default_factory=list)

    @field_validator("scores")
    @classmethod
    def _bounded(cls, v):
        assert all(0.0 <= s <= 1.0 for s in v.values()), "scores must be in [0,1]"
        return v

    @property
    def overall(self) -> float:                   # weakest-link, not average
        return min(self.scores.values()) if self.scores else 0.0


class ClarifiedTask(BaseModel):
    task: TaskSpec
    answers: dict[str, str] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)   # residual gaps, explicit — never silent
    final_ambiguity: float = 0.0


# ---- Prompt enhancement ------------------------------------------------------
class EnhancedPrompt(BaseModel):
    system: str
    user: str
    techniques_applied: list[str]
    provenance: dict[str, str] = Field(default_factory=dict)  # constraint -> source (task|answer|assumption)
    cove_verified: bool = False
    verification_log: list[str] = Field(default_factory=list)


# ---- Planning / patching -----------------------------------------------------
class AgentRole(str, Enum):
    orchestrator = "orchestrator"; planner = "planner"; coder = "coder"
    tester = "tester"; debugger = "debugger"; critic = "critic"


class PlanStep(BaseModel):
    agent_role: AgentRole
    description: str
    target_files: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    rationale: str
    steps: list[PlanStep] = Field(min_length=1)


class Patch(BaseModel):
    """Unified diff only — AgentForge Prop.3: O(k) tokens, smaller error surface."""
    unified_diff: str
    files_touched: list[str] = Field(min_length=1)
    rationale: str = ""

    @field_validator("unified_diff")
    @classmethod
    def _looks_like_diff(cls, v: str) -> str:
        markers = ("--- ", "+++ ", "diff --git", "@@")
        assert any(m in v for m in markers), "not a unified diff"
        return v


class TestSuite(BaseModel):
    framework: str = "pytest"
    code: str
    fail_to_pass: list[str] = Field(min_length=1)   # tests that must flip red->green
    pass_to_pass: list[str] = Field(default_factory=list)  # regression guard


# ---- Execution / verdicts ----------------------------------------------------
class ExecutionResult(BaseModel):
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_s: float = 0.0

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and "FAILED" not in self.stdout and "ERROR" not in self.stdout


class Verdict(BaseModel):
    passed: bool
    failures: list[str] = Field(default_factory=list)
    regression: bool = False
    notes: str = ""


# ---- Error taxonomy (verbatim classes from 20_error_taxonomy_routing.md) ------
class ErrorClass(str, Enum):
    syntax_type = "syntax_type"; logic = "logic"; design = "design"
    performance = "performance"; security = "security"
    environment = "environment"; flaky_test = "flaky_test"


class RoutedError(BaseModel):
    model_config = ConfigDict(frozen=True)
    error_class: ErrorClass
    context_strategy: str
    handler: str
    escalation: str
