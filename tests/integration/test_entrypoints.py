"""Every registered generator/importer/validator must be reachable (Phase 0 DoD)."""
from __future__ import annotations

import contextlib
import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_check_entrypoints_passes():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_entrypoints.py")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout


def test_cli_help_lists_command_surface():
    from utag_cli.main import main as cli_main

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.suppress(SystemExit):
        cli_main(["--help"])
    help_text = buf.getvalue()
    for cmd in ("generate", "validate", "targets", "intel", "openapi", "schema", "registry", "design", "observe"):
        assert cmd in help_text, f"`utag {cmd}` missing from --help"
