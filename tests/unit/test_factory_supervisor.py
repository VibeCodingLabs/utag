"""F3: desired_workers formula + guardrails + step limits + scale-to-zero."""
from __future__ import annotations

from pathlib import Path

import fakeredis
import pytest

from utag_factory.config import load_config
from utag_factory.queue import StreamQueue
from utag_factory.supervisor import Signals, Supervisor, eval_formula

ROOT = Path(__file__).resolve().parents[2]


def _supervisor(monkeypatch, profile="cloud_burst"):
    monkeypatch.setenv("UTAG_AUTOSCALING_PROFILE", profile)
    cfg = load_config(ROOT)
    q = StreamQueue(fakeredis.FakeRedis(), cfg.profile.queue, "sup")
    q.ensure_groups()
    return Supervisor(cfg=cfg, queue=q)


def test_eval_formula_is_safe_and_correct():
    v = {"min_workers": 0, "max_workers": 20, "queue_depth": 50,
         "target_jobs_per_worker": 5, "oldest_job_age_seconds": 90,
         "target_oldest_job_age_seconds": 30}
    expr = ("clamp(min_workers, max_workers, max(ceil(queue_depth / target_jobs_per_worker),"
            " ceil(oldest_job_age_seconds / target_oldest_job_age_seconds)))")
    assert eval_formula(expr, v) == 10  # max(ceil(50/5)=10, ceil(90/30)=3)
    with pytest.raises(ValueError, match="not allowed"):
        eval_formula("__import__('os').system('x')", v)
    with pytest.raises(ValueError, match="unknown variable"):
        eval_formula("mystery + 1", v)


def test_scale_up_is_step_limited(monkeypatch):
    sup = _supervisor(monkeypatch)
    # deep backlog wants many workers, but max_add_per_interval caps the step
    s = Signals(queue_depth=100, pending_entries=0, oldest_job_age_seconds=0,
                available_memory=64 * 1024**3)
    d = sup.decide(s, current=0)
    assert d.desired == sup.cfg.profile.scaling.step_limits.maximum_add_per_interval
    assert "step-limited" in d.reason


def test_memory_reserve_blocks_scale_up(monkeypatch):
    sup = _supervisor(monkeypatch)
    s = Signals(queue_depth=100, pending_entries=0, oldest_job_age_seconds=0,
                available_memory=1024)  # essentially no memory
    d = sup.decide(s, current=0)
    assert d.desired == 0 and "memory below reserve" in d.reason


def test_failure_rate_cap_blocks_scale_up(monkeypatch):
    sup = _supervisor(monkeypatch)
    s = Signals(queue_depth=100, pending_entries=0, oldest_job_age_seconds=0,
                available_memory=64 * 1024**3, recent_failure_rate=0.9)
    d = sup.decide(s, current=1)
    assert d.desired == 1 and "failure rate" in d.reason


def test_scale_to_zero_when_idle(monkeypatch):
    sup = _supervisor(monkeypatch)  # cloud_burst has min_workers 0, scale_to_zero true
    s = Signals(queue_depth=0, pending_entries=0, oldest_job_age_seconds=0,
                available_memory=64 * 1024**3)
    d = sup.decide(s, current=1)
    assert d.desired == 0


def test_scale_down_is_step_limited(monkeypatch):
    sup = _supervisor(monkeypatch)
    s = Signals(queue_depth=0, pending_entries=0, oldest_job_age_seconds=0,
                available_memory=64 * 1024**3)
    d = sup.decide(s, current=10)
    assert d.desired == 10 - sup.cfg.profile.scaling.step_limits.maximum_remove_per_interval


def test_reconcile_spawns_and_drains_with_fake_spawn(monkeypatch):
    sup = _supervisor(monkeypatch)
    for _ in range(3):
        sup.queue.enqueue(sup.cfg.streams.jobs, {"job_id": f"j{_}"})
    spawned = []
    d = sup.reconcile(spawn=lambda i: spawned.append(i) or f"fake-{i}")
    assert len(sup.workers) == d.desired and spawned
    events = sup.queue.r.xrange(sup.cfg.streams.events)
    assert any(b"utag.supervisor.scaled" in f.get(b"name", b"") for _i, f in events)
