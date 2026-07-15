"""autoresearch.sh: --strict must propagate pytest failure; --compare must not."""
from __future__ import annotations

import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "autoresearch.sh"


def _stub(tmp_path: Path, summary: str, rc: int) -> str:
    stub = tmp_path / "fake_pytest.sh"
    stub.write_text(f"#!/usr/bin/env bash\necho '{summary}'\nexit {rc}\n")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    return str(stub)


def _run(mode: str, pytest_cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(HARNESS), mode],
        env={"PATH": "/usr/bin:/bin", "PYTEST_CMD": pytest_cmd},
        capture_output=True,
        text=True,
    )


def test_strict_fails_on_failed_tests(tmp_path):
    proc = _run("--strict", _stub(tmp_path, "2 failed, 3 passed in 0.1s", 1))
    assert proc.returncode != 0
    assert "METRIC passed_tests=3" in proc.stdout
    assert "METRIC failed_tests=2" in proc.stdout


def test_strict_passes_on_green_suite(tmp_path):
    proc = _run("--strict", _stub(tmp_path, "5 passed in 0.1s", 0))
    assert proc.returncode == 0
    assert "METRIC passed_tests=5" in proc.stdout
    assert "METRIC failed_tests=0" in proc.stdout


def test_compare_collects_metrics_without_failing(tmp_path):
    proc = _run("--compare", _stub(tmp_path, "2 failed, 3 passed in 0.1s", 1))
    assert proc.returncode == 0
    assert "METRIC passed_tests=3" in proc.stdout
    assert "WARN" in proc.stdout


def test_unknown_mode_rejected(tmp_path):
    proc = _run("--bogus", _stub(tmp_path, "1 passed", 0))
    assert proc.returncode == 2
