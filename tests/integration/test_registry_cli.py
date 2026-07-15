"""`utag registry` CLI: list/doctor/manifest/coverage; coverage is deterministic."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from utag_cli.main import main as cli_main

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


def test_registry_list():
    rc, out = run_cli("registry", "list")
    assert rc == 0
    assert "pydantic-models" in out and "fastapi-importer" in out
    assert len(out.strip().splitlines()) >= 90  # 79 generators + 9 validators + 8 importers


def test_registry_doctor():
    rc, out = run_cli("registry", "doctor", "--root", str(ROOT))
    assert rc == 0, out
    assert "0 problem(s)" in out


def test_registry_manifest_by_id():
    rc, out = run_cli("registry", "manifest", "--id", "pydantic-models")
    assert rc == 0
    m = json.loads(out)
    assert m["kind"] == "generator"
    assert m["entrypoints"] == ["utag generate --target pydantic-models"]


def test_registry_manifest_unknown_id_fails():
    rc, _ = run_cli("registry", "manifest", "--id", "nope-not-registered")
    assert rc == 1


def test_registry_coverage_deterministic(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    assert run_cli("registry", "coverage", "--out", str(a))[0] == 0
    assert run_cli("registry", "coverage", "--out", str(b))[0] == 0
    assert a.read_bytes() == b.read_bytes()
    assert "| generator | pydantic-models |" in a.read_text()
