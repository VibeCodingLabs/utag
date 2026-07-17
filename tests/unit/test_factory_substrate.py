"""F1: stores, queue semantics, caches, retry taxonomy — offline (fakeredis + tmp sqlite)."""
from __future__ import annotations

import random
from pathlib import Path

import fakeredis
import pytest

from utag_core.schemas.factory import (
    DeadLetterEntry, FactoryJob, FailureClass, JobStatus,
)
from utag_factory.cache import ExactCache, FeatureHashEmbedder, SemanticCache, material_digest
from utag_factory.config import load_config
from utag_factory.queue import StreamQueue, backoff_s, classify_exception, is_retryable
from utag_factory.store import JobStore, VectorStore

ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT)


@pytest.fixture()
def redis():
    return fakeredis.FakeRedis()


@pytest.fixture()
def queue(redis):
    q = StreamQueue(redis, CFG.profile.queue, consumer_name="test-1")
    q.ensure_groups()
    return q


def _job(job_id="job-0001", **over) -> FactoryJob:
    from utag_core.schemas import EXAMPLES
    payload = dict(EXAMPLES["factory-job"])
    payload["id"] = job_id
    payload.update(over)
    return FactoryJob.model_validate(payload)


def test_job_store_roundtrip_and_transitions(tmp_path):
    store = JobStore(tmp_path / "jobs.db")
    ref, sha = store.put_payload("job-0001", {"script": "print(1)"})
    job = _job(payload_ref=ref, payload_sha256=sha)
    store.put(job)
    assert store.get("job-0001").status == JobStatus.queued
    store.transition("job-0001", JobStatus.running, worker="w-1")
    assert store.get("job-0001").worker == "w-1"
    assert store.counts_by_status() == {"running": 1}
    assert store.get_payload(ref) == {"script": "print(1)"}


def test_payload_digest_mismatch_detected(tmp_path):
    store = JobStore(tmp_path / "jobs.db")
    ref, _ = store.put_payload("job-x", {"a": 1})
    store.db.execute("UPDATE payloads SET body = ? WHERE ref = ?", ('{"a": 2}', ref))
    with pytest.raises(ValueError, match="digest mismatch"):
        store.get_payload(ref)


def test_queue_claim_ack_and_pending(queue):
    queue.enqueue(CFG.streams.jobs, {"job_id": "job-0001", "payload_ref": "payload:job-0001"})
    assert queue.depth() == 1
    (msg,) = queue.claim(block_ms=1)
    assert msg.fields["job_id"] == "job-0001"
    assert queue.pending() == 1
    queue.ack(msg)
    assert queue.pending() == 0
    assert queue.claim(block_ms=1) == []          # at-least-once: no redelivery after ack


def test_reclaim_takes_over_stale_messages(redis):
    q1 = StreamQueue(redis, CFG.profile.queue, consumer_name="dead-worker")
    q1.ensure_groups()
    q1.enqueue(CFG.streams.jobs, {"job_id": "job-stale"})
    q1.claim(block_ms=1)                           # dead-worker claims, then vanishes
    q2 = StreamQueue(redis, CFG.profile.queue, consumer_name="rescuer")
    redis.xautoclaim  # ensure command exists on fakeredis
    # template says claim after 60s idle; fake time by claiming with min idle 0 via monkey cfg
    q2.cfg = q2.cfg.model_copy(update={
        "recovery": q2.cfg.recovery.model_copy(update={"claim_idle_after": "0s"})})
    rescued = q2.reclaim()
    assert [m.fields["job_id"] for m in rescued] == ["job-stale"]


def test_dead_letter_carries_contract_entry(queue):
    queue.enqueue(CFG.streams.jobs, {"job_id": "job-dl"})
    (msg,) = queue.claim(block_ms=1)
    entry = DeadLetterEntry(original_job_pointer="payload:job-dl", attempts=3,
                            failure_class=FailureClass.provider_timeout,
                            failure_fingerprint="timeout:run-python")
    queue.dead_letter(msg, entry)
    (stored,) = queue.dead_letters()
    assert stored.failure_class == FailureClass.provider_timeout
    assert queue.pending() == 0                    # original acked


def test_retry_taxonomy_from_template():
    policy = CFG.profile.retries
    assert is_retryable(FailureClass.provider_timeout, policy)
    assert is_retryable(FailureClass.worker_lost, policy)
    assert not is_retryable(FailureClass.schema_invalid, policy)
    assert not is_retryable(FailureClass.permission_denied, policy)


def test_backoff_exponential_jitter_capped():
    policy = CFG.profile.retries  # initial 2s, max 2m
    rng = random.Random(42)
    b1, b2, b9 = (backoff_s(n, policy, rng) for n in (1, 2, 9))
    assert 1.0 <= b1 <= 3.0            # 2s ± jitter
    assert 2.0 <= b2 <= 6.0            # 4s ± jitter
    assert b9 <= 180.0                 # capped at 2m * 1.5 jitter


def test_classify_exception():
    assert classify_exception(TimeoutError("x")) == FailureClass.provider_timeout
    assert classify_exception(PermissionError("x")) == FailureClass.permission_denied
    assert classify_exception(ValueError("schema validation failed")) == FailureClass.schema_invalid
    assert classify_exception(ConnectionError("refused")) == FailureClass.transient_network


def test_vector_store_cosine_search(tmp_path):
    store = VectorStore(tmp_path / "vec.db", dim=8)
    store.add("a", [1, 0, 0, 0, 0, 0, 0, 0], {"value": "A"})
    store.add("b", [0, 1, 0, 0, 0, 0, 0, 0], {"value": "B"})
    (key, sim, meta), *_ = store.search([1, 0, 0, 0, 0, 0, 0, 0], k=2)
    assert key == "a" and sim == pytest.approx(1.0) and meta["value"] == "A"


def test_exact_cache_ttl(redis):
    cache = ExactCache(redis, CFG.profile.cache)
    cache.put("d" * 64, "cached-value")
    assert cache.get("d" * 64) == "cached-value"
    assert 899 <= redis.ttl("utag:cache:" + "d" * 64) <= 900    # template: 15m


MATERIAL = {"normalized_input_digest": "x", "schema_digest": "y",
            "generator_version": "1", "provider_id": "fake", "model_id": "m"}


def test_semantic_cache_hits_near_duplicates(tmp_path):
    cache = SemanticCache(VectorStore(tmp_path / "vec.db"), FeatureHashEmbedder(),
                          CFG.profile.cache)
    cache.put("generate a pydantic model for a petstore api", MATERIAL, "artifact-ref-1")
    assert cache.get("generate a pydantic model for a petstore api", MATERIAL) == "artifact-ref-1"
    # case/whitespace variants normalize to the same embedding -> hit
    assert cache.get("Generate a Pydantic model for a petstore API", MATERIAL) == "artifact-ref-1"
    # honest ceiling of the lexical placeholder embedder: reworded text scores
    # below the template's 0.94 threshold -> miss (a model embedder would hit)
    assert cache.get("generate a pydantic model for the petstore api", MATERIAL) is None
    # different material never hits, regardless of similarity (template key material)
    other = dict(MATERIAL, model_id="different")
    assert cache.get("generate a pydantic model for a petstore api", other) is None
    # unrelated text misses
    assert cache.get("write a haiku about redis streams", MATERIAL) is None


def test_semantic_cache_requires_all_key_material(tmp_path):
    cache = SemanticCache(VectorStore(tmp_path / "vec.db"), FeatureHashEmbedder(),
                          CFG.profile.cache)
    with pytest.raises(ValueError, match="missing"):
        cache.get("text", {"model_id": "only"})
