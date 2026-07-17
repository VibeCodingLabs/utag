"""Redis Streams queue per the canonical template: consumer groups,
at-least-once delivery, pointers-only payloads, XAUTOCLAIM crash recovery,
dead-letter stream, retry taxonomy with exponential-jitter backoff.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass

from utag_core.schemas.factory import DeadLetterEntry, FailureClass, QueueConfig, RetryPolicy

from utag_factory.config import parse_duration_s


@dataclass
class Message:
    stream: str
    id: str
    fields: dict[str, str]


class StreamQueue:
    def __init__(self, redis, cfg: QueueConfig, consumer_name: str):
        self.r = redis
        self.cfg = cfg
        self.consumer = consumer_name

    # -- lifecycle -----------------------------------------------------------
    def ensure_groups(self) -> None:
        for stream in self._streams():
            try:
                self.r.xgroup_create(stream, self.cfg.consumer_group, id="0", mkstream=True)
            except Exception as e:  # noqa: BLE001
                if "BUSYGROUP" not in str(e):
                    raise

    def _streams(self) -> list[str]:
        s = self.cfg.streams
        return [s.jobs, s.ingest, s.validate_stream, s.evals, s.events, s.dead_letters]

    # -- produce -------------------------------------------------------------
    def enqueue(self, stream: str, fields: dict[str, str]) -> str:
        maxlen = self.cfg.retention.approximate_max_entries
        return self.r.xadd(stream, fields, maxlen=maxlen, approximate=True)

    def publish_event(self, fields: dict[str, str]) -> str:
        return self.enqueue(self.cfg.streams.events, fields)

    # -- consume -------------------------------------------------------------
    def claim(self, stream: str | None = None, block_ms: int | None = None) -> list[Message]:
        stream = stream or self.cfg.streams.jobs
        if block_ms is None:
            block_ms = int(parse_duration_s(self.cfg.read.block_timeout) * 1000)
        resp = self.r.xreadgroup(self.cfg.consumer_group, self.consumer,
                                 {stream: ">"}, count=self.cfg.read.batch_size,
                                 block=block_ms)
        return [Message(stream=_s(sname), id=_s(mid), fields=_fields(f))
                for sname, messages in (resp or []) for mid, f in messages]

    def ack(self, message: Message) -> None:
        self.r.xack(message.stream, self.cfg.consumer_group, message.id)

    def reclaim(self, stream: str | None = None) -> list[Message]:
        """XAUTOCLAIM messages whose consumer died (idle past the template limit)."""
        stream = stream or self.cfg.streams.jobs
        min_idle_ms = int(parse_duration_s(self.cfg.recovery.claim_idle_after) * 1000)
        _cursor, messages, *_ = self.r.xautoclaim(
            stream, self.cfg.consumer_group, self.consumer,
            min_idle_time=min_idle_ms, start_id="0")
        return [Message(stream=stream, id=_s(mid), fields=_fields(f)) for mid, f in messages]

    # -- signals (scaling inputs) ---------------------------------------------
    def depth(self, stream: str | None = None) -> int:
        return self.r.xlen(stream or self.cfg.streams.jobs)

    def pending(self, stream: str | None = None) -> int:
        info = self.r.xpending(stream or self.cfg.streams.jobs, self.cfg.consumer_group)
        return int(info["pending"] if isinstance(info, dict) else info[0])

    def oldest_job_age_s(self, stream: str | None = None) -> float:
        stream = stream or self.cfg.streams.jobs
        first = self.r.xrange(stream, count=1)
        if not first:
            return 0.0
        ms = int(_s(first[0][0]).split("-")[0])
        return max(0.0, time.time() - ms / 1000)

    # -- dead letters ----------------------------------------------------------
    def dead_letter(self, message: Message, entry: DeadLetterEntry) -> str:
        dlq_id = self.enqueue(self.cfg.streams.dead_letters,
                              {"entry": entry.model_dump_json(exclude_none=True)})
        self.ack(message)
        return dlq_id

    def dead_letters(self, count: int = 100) -> list[DeadLetterEntry]:
        rows = self.r.xrange(self.cfg.streams.dead_letters, count=count)
        return [DeadLetterEntry.model_validate_json(_fields(f)["entry"]) for _mid, f in rows]


# -- retry taxonomy ------------------------------------------------------------

def is_retryable(failure: FailureClass, policy: RetryPolicy) -> bool:
    if failure in policy.terminal:
        return False
    return failure in policy.retryable


def backoff_s(attempt: int, policy: RetryPolicy, rng: random.Random | None = None) -> float:
    """Exponential backoff with jitter in [0.5x, 1.5x], capped at the policy max."""
    rng = rng or random.Random()
    base = parse_duration_s(policy.backoff.initial) * (2 ** max(0, attempt - 1))
    capped = min(base, parse_duration_s(policy.backoff.maximum))
    return capped * rng.uniform(0.5, 1.5)


def classify_exception(exc: BaseException) -> FailureClass:
    """Map runtime failures onto the template taxonomy (conservative defaults)."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if isinstance(exc, TimeoutError) or "timeout" in text:
        return FailureClass.provider_timeout
    if isinstance(exc, PermissionError):  # before OSError — it's a subclass
        return FailureClass.permission_denied
    if isinstance(exc, MemoryError) or "resource temporarily unavailable" in text:
        return FailureClass.resource_temporarily_unavailable
    if isinstance(exc, (ConnectionError, OSError)):
        return FailureClass.transient_network
    if "validation" in text or "schema" in text:
        return FailureClass.schema_invalid
    return FailureClass.deterministic_failure_repeated


def _s(v) -> str:
    return v.decode() if isinstance(v, bytes) else str(v)


def _fields(f: dict) -> dict[str, str]:
    return {_s(k): _s(v) for k, v in f.items()}
