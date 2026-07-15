"""Execution grounding. Caps mirror AgentForge §III.E: 512MB / 0.5 CPU / no net / 64 PIDs / 30s.
Sandbox is a protocol — swap Docker for Firecracker/gVisor without touching the loop."""
from __future__ import annotations
import subprocess, time
from typing import Protocol
from ..core.schemas import ExecutionResult


class Sandbox(Protocol):
    def run(self, workdir: str, command: list[str]) -> ExecutionResult: ...


class DockerSandbox:
    def __init__(self, image: str = "python:3.12-slim", mem: str = "512m",
                 cpus: str = "0.5", pids: int = 64, timeout_s: int = 30) -> None:
        self.image, self.mem, self.cpus, self.pids, self.timeout_s = image, mem, cpus, pids, timeout_s

    def run(self, workdir: str, command: list[str]) -> ExecutionResult:
        argv = ["docker", "run", "--rm",
                "--memory", self.mem, "--cpus", self.cpus,
                "--pids-limit", str(self.pids), "--network", "none",
                "-v", f"{workdir}:/work:ro", "-w", "/work", self.image, *command]
        t0 = time.monotonic()
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=self.timeout_s)
            return ExecutionResult(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr,
                                   duration_s=time.monotonic() - t0)
        except subprocess.TimeoutExpired as e:
            return ExecutionResult(exit_code=124, stdout=str(e.stdout or ""),
                                   stderr="TIMEOUT", duration_s=self.timeout_s)


class LocalSandbox:
    """NO ISOLATION — tests/dev only. Never wire into prod loop."""
    def __init__(self, timeout_s: int = 30) -> None:
        self.timeout_s = timeout_s

    def run(self, workdir: str, command: list[str]) -> ExecutionResult:
        t0 = time.monotonic()
        p = subprocess.run(command, cwd=workdir, capture_output=True, text=True, timeout=self.timeout_s)
        return ExecutionResult(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr,
                               duration_s=time.monotonic() - t0)
