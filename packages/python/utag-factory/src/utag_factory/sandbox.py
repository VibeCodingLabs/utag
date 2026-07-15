"""Sandcastle-tier sandboxes: bwrap by default, plain process fallback.

Same shape as veriforge's Sandbox protocol (`run(workdir, command)`), extended
with the template's resource contract: address-space limit, wall-time kill,
output cap, env scrub. The third tier — remote Flash workers — lives in
flash_tools (an ephemeral cloud machine is its own sandbox).
"""
from __future__ import annotations

import os
import resource
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from utag_core.schemas.factory import ExecutionConfig, Isolation, ResourceContract

_SAFE_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}


@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    truncated: bool = False
    timed_out: bool = False


def _limits_preexec(contract: ResourceContract):
    def apply():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_AS,
                           (contract.max_memory_bytes, contract.max_memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE,
                           (contract.max_output_bytes, contract.max_output_bytes))
    return apply


def _run(argv: list[str], workdir: Path, contract: ResourceContract) -> ExecutionResult:
    t0 = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=workdir, capture_output=True, text=True,
                              timeout=contract.max_wall_time_s, env=dict(_SAFE_ENV),
                              preexec_fn=_limits_preexec(contract))
        out, err, code, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        code, timed_out = -1, True
    duration_ms = round((time.monotonic() - t0) * 1000, 3)
    cap = contract.max_output_bytes
    truncated = len(out) > cap or len(err) > cap
    return ExecutionResult(exit_code=code, stdout=out[:cap], stderr=err[:cap],
                           duration_ms=duration_ms, truncated=truncated,
                           timed_out=timed_out)


class ProcessSandbox:
    """Plain subprocess: env scrubbed, rlimits applied, wall-time kill.
    No filesystem isolation — the fallback tier."""

    isolation = Isolation.process

    def run(self, workdir: Path, command: list[str],
            contract: ResourceContract) -> ExecutionResult:
        return _run(command, workdir, contract)


class BwrapSandbox:
    """bubblewrap: read-only system dirs, private tmp, no network, cleared env,
    only the job workdir writable."""

    isolation = Isolation.bwrap

    def run(self, workdir: Path, command: list[str],
            contract: ResourceContract) -> ExecutionResult:
        argv = ["bwrap", "--die-with-parent", "--unshare-all", "--clearenv"]
        for k, v in _SAFE_ENV.items():
            argv += ["--setenv", k, v]
        for ro in ("/usr", "/lib", "/lib64", "/bin", "/sbin", "/etc/alternatives"):
            if Path(ro).exists():
                argv += ["--ro-bind", ro, ro]
        argv += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                 "--bind", str(workdir), str(workdir), "--chdir", str(workdir)]
        return _run(argv + command, workdir, contract)


def bwrap_available() -> bool:
    return shutil.which("bwrap") is not None


def pick_sandbox(execution: ExecutionConfig):
    """Template default when its toolchain exists; visible fallback otherwise."""
    if (execution.default_isolation == Isolation.bwrap
            and Isolation.bwrap in execution.allowed_isolation and bwrap_available()):
        return BwrapSandbox()
    if Isolation.process not in execution.allowed_isolation:
        raise RuntimeError("no permitted sandbox available "
                           f"(allowed: {[i.value for i in execution.allowed_isolation]})")
    return ProcessSandbox()
