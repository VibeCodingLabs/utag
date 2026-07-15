"""Supervisor: evaluate the template's desired_workers formula from live queue
signals, apply guardrails (memory reserve, failure-rate cap, step limits,
scale-to-zero), and spawn/drain worker daemons — systemd-run transient units
when available, plain subprocesses otherwise.
"""
from __future__ import annotations

import ast
import math
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field

from utag_factory.config import FactoryConfig, parse_bytes, parse_duration_s
from utag_factory.queue import StreamQueue

# whitelisted names for the desired_workers expression — no builtins, no calls
# to anything else. Evaluated over an AST, not eval().
_FUNCS = {
    "clamp": lambda lo, hi, x: max(lo, min(hi, x)),
    "max": max, "min": min,
    "ceil": lambda x: math.ceil(x), "floor": lambda x: math.floor(x),
}


def eval_formula(expr: str, variables: dict[str, float]) -> float:
    """Safe arithmetic over whitelisted funcs + given variables."""
    tree = ast.parse(expr, mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            raise ValueError(f"unknown variable {node.id!r} in desired_workers")
        if isinstance(node, ast.BinOp):
            l, r = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return l + r
            if isinstance(node.op, ast.Sub):
                return l - r
            if isinstance(node.op, ast.Mult):
                return l * r
            if isinstance(node.op, ast.Div):
                return l / r
            raise ValueError(f"operator {type(node.op).__name__} not allowed")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
                raise ValueError(f"call {ast.dump(node.func)} not allowed")
            return _FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise ValueError(f"node {type(node).__name__} not allowed in desired_workers")

    return ev(tree)


@dataclass
class Signals:
    queue_depth: int
    pending_entries: int
    oldest_job_age_seconds: float
    available_memory: int
    recent_failure_rate: float = 0.0
    available_vram: int = 0


@dataclass
class ScalingDecision:
    current: int
    desired: int
    reason: str


@dataclass
class Supervisor:
    cfg: FactoryConfig
    queue: StreamQueue
    workers: list = field(default_factory=list)  # handles (systemd unit name or Popen)

    # -- signal gathering -------------------------------------------------------
    def gather(self) -> Signals:
        try:
            import psutil  # optional; falls back to /proc
            avail_mem = psutil.virtual_memory().available
        except Exception:  # noqa: BLE001
            avail_mem = _proc_mem_available()
        return Signals(
            queue_depth=self.queue.depth(),
            pending_entries=self.queue.pending(),
            oldest_job_age_seconds=self.queue.oldest_job_age_s(),
            available_memory=avail_mem)

    # -- decision ---------------------------------------------------------------
    def decide(self, signals: Signals, current: int) -> ScalingDecision:
        prof = self.cfg.worker_profile
        scaling = self.cfg.profile.scaling
        variables = {
            "min_workers": prof.min_workers, "max_workers": prof.max_workers,
            "queue_depth": signals.queue_depth,
            "pending_entries": signals.pending_entries,
            "oldest_job_age_seconds": signals.oldest_job_age_seconds,
            "target_jobs_per_worker": scaling.target_jobs_per_worker,
            "target_oldest_job_age_seconds": parse_duration_s(scaling.target_oldest_job_age),
        }
        raw = eval_formula(scaling.desired_workers, variables)
        desired = int(_FUNCS["clamp"](prof.min_workers, prof.max_workers, math.ceil(raw)))

        g = scaling.guardrails
        reason = "formula"
        if not scaling.scale_to_zero:
            desired = max(desired, prof.min_workers, 1)
        if signals.recent_failure_rate > g.maximum_failure_rate and desired > current:
            desired, reason = current, f"failure rate {signals.recent_failure_rate:.0%} over cap"
        elif desired > current and g.refuse_scale_up_when_memory_below_reserve \
                and signals.available_memory < parse_bytes(prof.memory_reserve):
            desired, reason = current, "memory below reserve"
        elif desired > current:
            desired = min(desired, current + scaling.step_limits.maximum_add_per_interval)
            reason = "scale up (step-limited)"
        elif desired < current:
            desired = max(desired, current - scaling.step_limits.maximum_remove_per_interval)
            reason = "scale down (step-limited, drain idle)"
        return ScalingDecision(current=current, desired=desired, reason=reason)

    # -- actuation --------------------------------------------------------------
    def reconcile(self, spawn=None) -> ScalingDecision:
        decision = self.decide(self.gather(), current=len(self.workers))
        spawn = spawn or self._spawn_worker
        while len(self.workers) < decision.desired:
            self.workers.append(spawn(len(self.workers)))
        while len(self.workers) > decision.desired:
            self._drain_worker(self.workers.pop())
        self.queue.publish_event({"name": "utag.supervisor.scaled",
                                  "current": str(decision.current),
                                  "desired": str(decision.desired),
                                  "reason": decision.reason})
        return decision

    def _spawn_worker(self, index: int):
        name = f"utag-worker-{os.getpid()}-{index}"
        cmd = ["utag-factory", "work", "--name", name]
        if use_systemd_run():
            unit = f"{name}.service"
            subprocess.run(["systemd-run", "--user", "--unit", unit,
                            f"--property=MemoryMax={self.cfg.worker_profile.worker_memory_limit}",
                            *cmd], check=False)
            return unit
        return subprocess.Popen(cmd)

    def _drain_worker(self, handle) -> None:
        grace = parse_duration_s(self.cfg.profile.execution.worker_shutdown_grace)
        if isinstance(handle, str):  # systemd unit
            subprocess.run(["systemctl", "--user", "stop", handle], check=False)
            return
        handle.terminate()
        try:
            handle.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            handle.kill()


def use_systemd_run() -> bool:
    return shutil.which("systemd-run") is not None and os.environ.get("XDG_RUNTIME_DIR") is not None


def _proc_mem_available() -> int:
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except OSError:
        pass
    return 1 << 30
