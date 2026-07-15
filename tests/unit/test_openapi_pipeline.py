"""Real OpenAPI pipeline: normalize/bundle/diff/overlay/lint/readiness content checks."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from utag_core import openapi as oa

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "openapi"
PETSTORE = oa.load_spec(FIX / "petstore.yaml")


def test_load_spec_rejects_non_openapi(tmp_path):
    bad = tmp_path / "x.yaml"
    bad.write_text("just: yaml\n")
    with pytest.raises(ValueError, match="openapi"):
        oa.load_spec(bad)


def test_normalize_resolves_refs_and_is_canonical():
    resolved = oa.resolve_local_refs(PETSTORE)
    listing = resolved["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert listing["items"]["properties"]["name"] == {"type": "string"}  # $ref inlined
    assert oa.canonical(resolved) == oa.canonical(oa.resolve_local_refs(PETSTORE))


def test_bundle_inlines_external_file_refs():
    doc = oa.load_spec(FIX / "petstore-split.yaml")
    bundled, resolved = oa.bundle(doc, FIX)
    schema = bundled["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["required"] == ["id", "name"]
    assert resolved == ["petstore-shared.yaml#/Pet"]


def test_diff_reports_added_removed_changed():
    report = oa.diff(PETSTORE, oa.load_spec(FIX / "petstore-v2.yaml"), "v1", "v2")
    by_kind = {}
    for e in report.entries:
        by_kind.setdefault(e.kind, []).append(e.pointer)
    assert any("photos" in p for p in by_kind["added"])
    assert any(p.endswith("/post") for p in by_kind["removed"])          # POST /pets dropped
    assert any(p.endswith("~1pets/get") for p in by_kind["changed"])     # paging added
    assert "/components/schemas/Pet" in by_kind["changed"]               # photoUrls added


def test_overlay_updates_and_removes():
    overlay = yaml.safe_load((FIX / "overlay-title.yaml").read_text())
    out = oa.apply_overlay(PETSTORE, overlay)
    assert out["info"]["title"] == "Petstore (Partner Edition)"
    assert out["info"]["x-audience"] == "partners"
    assert out["info"]["version"] == "1.0.0"          # merge, not replace
    assert "post" not in out["paths"]["/pets"]
    assert "post" in PETSTORE["paths"]["/pets"]       # input untouched
    with pytest.raises(ValueError, match="Overlay"):
        oa.apply_overlay(PETSTORE, {"nope": True})


def test_lint_clean_spec_has_no_errors():
    findings = oa.lint(PETSTORE, "petstore.yaml")
    assert not [f for f in findings if f.severity.value == "error"]


def test_lint_flags_real_defects():
    findings = oa.lint(oa.load_spec(FIX / "petstore-flawed.yaml"), "flawed")
    codes = {f.code for f in findings}
    assert {"missing-operation-id", "no-success-response", "missing-summary",
            "untagged-operation", "orphan-schema"} <= codes


def test_readiness_scores_and_findings():
    good = oa.readiness(PETSTORE, "petstore.yaml")
    assert good.operations == 3 and good.score == 1.0 and good.findings == []
    bad = oa.readiness(oa.load_spec(FIX / "petstore-flawed.yaml"), "flawed")
    assert bad.score < 0.5
    assert any("operationId" in f for f in bad.findings)


def test_operations_extraction():
    ops = {o.operation_id: o for o in oa.operations(PETSTORE)}
    assert ops["createPet"].has_request_schema and ops["createPet"].has_response_schema
    assert ops["listPets"].method.value == "get" and ops["listPets"].tags == ["pets"]
    payload = json.loads(ops["getPet"].model_dump_json(exclude_none=True))
    assert payload["path"] == "/pets/{petId}"
