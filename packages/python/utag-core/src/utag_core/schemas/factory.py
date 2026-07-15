"""Factory contracts (v2.16.0): autoscaling profile, jobs, resource contracts, DLQ.

`AutoscalingProfile` is the typed form of `policies/autoscaling.yaml` — the
operator's template is canonical only because it validates against this schema
(the template's own stated requirement).
"""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from utag_core.schemas import SHA256, SLUG, StrictSchema

DURATION = r"^\d+(ms|s|m|h)$"
BYTESIZE = r"^\d+(B|KiB|MiB|GiB)$"


class Isolation(str, Enum):
    process = "process"
    bwrap = "bwrap"
    firecracker = "firecracker"
    remote_flash = "remote-flash"


class FailureClass(str, Enum):
    provider_rate_limit = "provider_rate_limit"
    provider_timeout = "provider_timeout"
    worker_lost = "worker_lost"
    transient_network = "transient_network"
    resource_temporarily_unavailable = "resource_temporarily_unavailable"
    schema_invalid = "schema_invalid"
    permission_denied = "permission_denied"
    unsupported_capability = "unsupported_capability"
    deterministic_failure_repeated = "deterministic_failure_repeated"


class ScalingSignal(str, Enum):
    queue_depth = "queue_depth"
    pending_entries = "pending_entries"
    oldest_job_age = "oldest_job_age"
    worker_utilization = "worker_utilization"
    available_memory = "available_memory"
    available_vram = "available_vram"
    recent_failure_rate = "recent_failure_rate"


class JobKind(str, Enum):
    run_python = "run-python"
    generate_artifact = "generate-artifact"
    agent_task = "agent-task"
    embed = "embed"


class JobStatus(str, Enum):
    queued = "queued"
    claimed = "claimed"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    dead_letter = "dead-letter"
    cancelled = "cancelled"


class TemplateMeta(StrictSchema):
    id: str = Field(pattern=SLUG)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    status: str = Field(pattern=r"^(draft|canonical)$")
    strict: bool
    unknown_fields: str = Field(pattern=r"^reject$")
    description: str = ""


class SelectionConfig(StrictSchema):
    active_profile_env: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    default_profile: str = Field(pattern=r"^[a-z0-9_]+$")


class QueueStreams(StrictSchema):
    jobs: str
    ingest: str
    validate_stream: str = Field(alias="validate")  # `validate` shadows a BaseModel attr
    evals: str
    events: str
    dead_letters: str


class QueueRead(StrictSchema):
    batch_size: int = Field(ge=1)
    block_timeout: str = Field(pattern=DURATION)


class QueueRecovery(StrictSchema):
    claim_command: str = Field(pattern=r"^XAUTOCLAIM$")
    claim_idle_after: str = Field(pattern=DURATION)
    reclaim_interval: str = Field(pattern=DURATION)


class QueueRetention(StrictSchema):
    approximate_max_entries: int = Field(ge=1)


class QueueConfig(StrictSchema):
    provider: str = Field(pattern=r"^redis_streams$")
    connection_env: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    streams: QueueStreams
    consumer_group: str
    consumer_name_template: str
    delivery: str = Field(pattern=r"^at_least_once$")
    pointers_only: bool
    read: QueueRead
    recovery: QueueRecovery
    retention: QueueRetention


class Stabilization(StrictSchema):
    scale_up: str = Field(pattern=DURATION)
    scale_down: str = Field(pattern=DURATION)


class StepLimits(StrictSchema):
    maximum_add_per_interval: int = Field(ge=1)
    maximum_remove_per_interval: int = Field(ge=1)


class ScalingGuardrails(StrictSchema):
    refuse_scale_up_when_memory_below_reserve: bool
    refuse_scale_up_when_vram_below_reserve: bool
    stop_claiming_before_oom: bool
    drain_before_scale_down: bool
    terminate_only_idle_workers: bool
    preserve_inflight_checkpoints: bool
    maximum_failure_rate: float = Field(ge=0, le=1)


class ScalingConfig(StrictSchema):
    enabled: bool
    scale_to_zero: bool
    poll_interval: str = Field(pattern=DURATION)
    target_jobs_per_worker: int = Field(ge=1)
    target_oldest_job_age: str = Field(pattern=DURATION)
    stabilization: Stabilization
    step_limits: StepLimits
    signals: list[ScalingSignal]
    desired_workers: str = Field(min_length=1)
    guardrails: ScalingGuardrails


class ExecutionConfig(StrictSchema):
    supervisor: str = Field(pattern=r"^(python|go)$")
    default_isolation: Isolation
    allowed_isolation: list[Isolation]
    worker_shutdown_grace: str = Field(pattern=DURATION)
    hard_kill_after: str = Field(pattern=DURATION)
    job_timeout: str = Field(pattern=DURATION)
    resource_contract_required: bool


class WorkerProfile(StrictSchema):
    min_workers: int = Field(ge=0)
    max_workers: int = Field(ge=1)
    max_llm_workers: int = Field(ge=0)
    max_embedding_workers: int = Field(ge=0)
    max_wolfram_kernels: int = Field(ge=0)
    max_firecracker_vms: int = Field(ge=0)
    memory_reserve: str = Field(pattern=BYTESIZE)
    vram_reserve: str = Field(pattern=BYTESIZE)
    worker_memory_limit: str = Field(pattern=BYTESIZE)
    worker_cpu_limit: int = Field(ge=1)
    prefer_remote_over_local_when_oom_risk: bool


class StatePort(StrictSchema):
    port: str = Field(pattern=r"^[A-Za-z]+Port$")
    provider_env: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    default_provider: str
    supported_providers: list[str] = Field(min_length=1)


class StateConfig(StrictSchema):
    job_store: StatePort
    vector_store: StatePort
    artifact_store: StatePort


class ExactCache(StrictSchema):
    provider: str = Field(pattern=r"^redis$")
    ttl: str = Field(pattern=DURATION)


class SemanticCache(StrictSchema):
    provider_ref: str
    similarity_threshold: float = Field(ge=0, le=1)
    ttl: str = Field(pattern=DURATION)
    key_material: list[str] = Field(min_length=1)


class CacheConfig(StrictSchema):
    exact: ExactCache
    semantic: SemanticCache


class Backoff(StrictSchema):
    strategy: str = Field(pattern=r"^exponential_jitter$")
    initial: str = Field(pattern=DURATION)
    maximum: str = Field(pattern=DURATION)


class RetryPolicy(StrictSchema):
    maximum_attempts: int = Field(ge=1)
    backoff: Backoff
    retryable: list[FailureClass] = Field(min_length=1)
    terminal: list[FailureClass] = Field(min_length=1)


class DlqPolicy(StrictSchema):
    enabled: bool
    stream_ref: str
    include: list[str] = Field(min_length=1)
    evaluator_requeue_requires: list[str] = Field(min_length=1)


class ObservabilityConfig(StrictSchema):
    metrics: list[str] = Field(min_length=1)
    structured_logs: bool
    trace_propagation: bool
    event_stream_ref: str


class AdapterTarget(StrictSchema):
    enabled: bool
    generate_from_policy: bool | None = None


class ValidationRequirements(StrictSchema):
    require_schema_validation: bool
    require_unknown_field_rejection: bool
    require_profile_resource_limits: bool
    require_dlq_for_at_least_once_delivery: bool
    require_scale_down_drain: bool
    require_determinism_test: bool


class AutoscalingProfile(StrictSchema):
    template: TemplateMeta
    selection: SelectionConfig
    queue: QueueConfig
    scaling: ScalingConfig
    execution: ExecutionConfig
    profiles: dict[str, WorkerProfile] = Field(min_length=1)
    state: StateConfig
    cache: CacheConfig
    retries: RetryPolicy
    dead_letter_queue: DlqPolicy
    observability: ObservabilityConfig
    adapter_targets: dict[str, AdapterTarget]
    validation: ValidationRequirements


class ResourceContract(StrictSchema):
    """Per-job resource limits (wolfram-kb principle: every expensive job carries one)."""
    max_memory_bytes: int = Field(ge=1)
    max_wall_time_s: int = Field(ge=1)
    max_output_bytes: int = Field(ge=1)
    max_vram_bytes: int = Field(default=0, ge=0)
    concurrency_class: str = Field(default="default", pattern=SLUG)
    allow_remote: bool = False
    degradation_policy: str = Field(default="fail", pattern=r"^(fail|queue|degrade)$")


class FactoryJob(StrictSchema):
    id: str = Field(pattern=SLUG)
    kind: JobKind
    status: JobStatus
    payload_ref: str = Field(min_length=1)  # pointers-only queue: payload lives in the store
    payload_sha256: str = Field(pattern=SHA256)
    resources: ResourceContract
    isolation: Isolation
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    failure_class: FailureClass | None = None
    failure_fingerprint: str | None = None
    worker: str | None = None
    run_id: str | None = None
    created_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    updated_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class DeadLetterEntry(StrictSchema):
    original_job_pointer: str = Field(min_length=1)
    attempts: int = Field(ge=1)
    failure_class: FailureClass
    failure_fingerprint: str = Field(min_length=1)
    schema_digest: str | None = Field(default=None, pattern=SHA256)
    workflow_ref: str | None = None
    validation_reports: list[str] = []
    execution_trace_ref: str | None = None
    provider_history: list[str] = []
    resource_usage: dict[str, float] = {}


TOP_LEVEL = [AutoscalingProfile, ResourceContract, FactoryJob, DeadLetterEntry]

_PROFILE_EXAMPLE = {
    "min_workers": 0, "max_workers": 2, "max_llm_workers": 1,
    "max_embedding_workers": 1, "max_wolfram_kernels": 0, "max_firecracker_vms": 0,
    "memory_reserve": "2GiB", "vram_reserve": "0GiB",
    "worker_memory_limit": "2GiB", "worker_cpu_limit": 2,
    "prefer_remote_over_local_when_oom_risk": True,
}
_RESOURCES_EXAMPLE = {"max_memory_bytes": 1073741824, "max_wall_time_s": 900,
                      "max_output_bytes": 1048576, "allow_remote": True}
EXAMPLES = {
    "AutoscalingProfile": {
        "template": {"id": "autoscaling/default", "version": "1.0.0", "status": "canonical",
                     "strict": True, "unknown_fields": "reject", "description": "example"},
        "selection": {"active_profile_env": "UTAG_AUTOSCALING_PROFILE",
                      "default_profile": "local_small"},
        "queue": {"provider": "redis_streams", "connection_env": "UTAG_REDIS_URL",
                  "streams": {"jobs": "utag:jobs", "ingest": "utag:ingest",
                              "validate": "utag:validate", "evals": "utag:evals",
                              "events": "utag:events", "dead_letters": "utag:dlq"},
                  "consumer_group": "utag-workers",
                  "consumer_name_template": "{hostname}-{pid}-{worker_index}",
                  "delivery": "at_least_once", "pointers_only": True,
                  "read": {"batch_size": 1, "block_timeout": "5s"},
                  "recovery": {"claim_command": "XAUTOCLAIM", "claim_idle_after": "60s",
                               "reclaim_interval": "30s"},
                  "retention": {"approximate_max_entries": 100000}},
        "scaling": {"enabled": True, "scale_to_zero": True, "poll_interval": "5s",
                    "target_jobs_per_worker": 5, "target_oldest_job_age": "30s",
                    "stabilization": {"scale_up": "15s", "scale_down": "120s"},
                    "step_limits": {"maximum_add_per_interval": 2, "maximum_remove_per_interval": 1},
                    "signals": ["queue_depth", "oldest_job_age"],
                    "desired_workers": "clamp(min_workers, max_workers, ceil(queue_depth / target_jobs_per_worker))",
                    "guardrails": {"refuse_scale_up_when_memory_below_reserve": True,
                                   "refuse_scale_up_when_vram_below_reserve": True,
                                   "stop_claiming_before_oom": True,
                                   "drain_before_scale_down": True,
                                   "terminate_only_idle_workers": True,
                                   "preserve_inflight_checkpoints": True,
                                   "maximum_failure_rate": 0.25}},
        "execution": {"supervisor": "python", "default_isolation": "bwrap",
                      "allowed_isolation": ["process", "bwrap"],
                      "worker_shutdown_grace": "30s", "hard_kill_after": "45s",
                      "job_timeout": "15m", "resource_contract_required": True},
        "profiles": {"local_small": _PROFILE_EXAMPLE},
        "state": {"job_store": {"port": "JobStorePort", "provider_env": "UTAG_JOB_STORE_PROVIDER",
                                "default_provider": "sqlite", "supported_providers": ["sqlite"]},
                  "vector_store": {"port": "VectorStorePort", "provider_env": "UTAG_VECTOR_STORE_PROVIDER",
                                   "default_provider": "sqlite_vec", "supported_providers": ["sqlite_vec"]},
                  "artifact_store": {"port": "ArtifactStorePort", "provider_env": "UTAG_ARTIFACT_STORE_PROVIDER",
                                     "default_provider": "filesystem", "supported_providers": ["filesystem"]}},
        "cache": {"exact": {"provider": "redis", "ttl": "15m"},
                  "semantic": {"provider_ref": "state.vector_store", "similarity_threshold": 0.94,
                               "ttl": "24h", "key_material": ["normalized_input_digest", "model_id"]}},
        "retries": {"maximum_attempts": 3,
                    "backoff": {"strategy": "exponential_jitter", "initial": "2s", "maximum": "2m"},
                    "retryable": ["provider_timeout", "worker_lost"],
                    "terminal": ["schema_invalid", "permission_denied"]},
        "dead_letter_queue": {"enabled": True, "stream_ref": "queue.streams.dead_letters",
                              "include": ["original_job_pointer", "attempts", "failure_fingerprint"],
                              "evaluator_requeue_requires": ["validated_overlay", "new_attempt_budget"]},
        "observability": {"metrics": ["stream_queue_depth", "active_workers"],
                          "structured_logs": True, "trace_propagation": True,
                          "event_stream_ref": "queue.streams.events"},
        "adapter_targets": {"local_python_supervisor": {"enabled": True},
                            "systemd_transient_units": {"enabled": True},
                            "keda_scaled_object": {"enabled": False, "generate_from_policy": True}},
        "validation": {"require_schema_validation": True, "require_unknown_field_rejection": True,
                       "require_profile_resource_limits": True,
                       "require_dlq_for_at_least_once_delivery": True,
                       "require_scale_down_drain": True, "require_determinism_test": True},
    },
    "ResourceContract": _RESOURCES_EXAMPLE,
    "FactoryJob": {"id": "job-0001", "kind": "run-python", "status": "queued",
                   "payload_ref": "jobs/job-0001.json", "payload_sha256": "a" * 64,
                   "resources": _RESOURCES_EXAMPLE, "isolation": "bwrap",
                   "attempts": 0, "max_attempts": 3,
                   "created_at": "2026-07-15T00:00:00Z", "updated_at": "2026-07-15T00:00:00Z"},
    "DeadLetterEntry": {"original_job_pointer": "jobs/job-0001.json", "attempts": 3,
                        "failure_class": "provider_timeout",
                        "failure_fingerprint": "timeout:run-python:step-2",
                        "provider_history": ["fake-local"],
                        "resource_usage": {"memory_bytes": 1024.0}},
}
