"""`utag schema` CLI: list/emit/validate/validate-all/doctor + manifest wiring."""
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


def test_schema_list():
    rc, out = run_cli("schema", "list")
    assert rc == 0
    kinds = out.split()
    assert "artifact-manifest" in kinds and "design-yaml" in kinds
    assert len(kinds) >= 54


def test_schema_emit_roundtrip(tmp_path):
    rc, out = run_cli("schema", "emit", "--out", str(tmp_path))
    assert rc == 0
    emitted = list(tmp_path.glob("*.schema.json"))
    assert len(emitted) >= 54
    payload = json.loads((tmp_path / "artifact-manifest.schema.json").read_text())
    assert payload["additionalProperties"] is False


def test_schema_validate_design_yaml():
    rc, out = run_cli("schema", "validate", "--kind", "design-yaml", "--path", str(ROOT / "design.yaml"))
    assert rc == 0
    assert json.loads(out.strip().splitlines()[-1])["valid"] is True


def test_schema_validate_rejects_bad_payload(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"__nope__": 1}')
    rc, _ = run_cli("schema", "validate", "--kind", "artifact-manifest", "--path", str(bad))
    assert rc == 1


def test_schema_validate_all_repo():
    rc, out = run_cli("schema", "validate-all", "--root", str(ROOT))
    assert rc == 0, out


def test_schema_doctor(tmp_path):
    report = tmp_path / "doctor.md"
    rc, out = run_cli("schema", "doctor", "--root", str(ROOT), "--out", str(report))
    assert rc == 0
    assert "All schema contracts healthy" in report.read_text()


def test_generate_emits_valid_artifact_manifest(tmp_path):
    from utag_core.schemas.core import ArtifactManifest

    rc, _ = run_cli("generate", "--input", str(ROOT / "fixtures/prompts/categorize-file.prompt.yaml"),
                    "--target", "pydantic-models", "--out", str(tmp_path))
    assert rc == 0
    manifest_path = tmp_path / "artifact.manifest.json"
    manifest = ArtifactManifest.model_validate_json(manifest_path.read_text())
    assert manifest.target == "pydantic-models"
    assert manifest.files, "manifest lists no files"
    for f in manifest.files:
        assert (tmp_path / f.path).is_file()
