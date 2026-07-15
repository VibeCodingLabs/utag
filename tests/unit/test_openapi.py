import pytest
from utag_core.openapi import (
    OpenAPISource,
    OpenAPIDocument,
    OpenAPIBundle,
    OpenAPIDiff,
    OverlayPatch,
    ValidationFinding,
    BreakingChangeReport,
    AgentReadinessReport,
)

def test_openapi_source():
    source = OpenAPISource(uri="https://example.com/openapi.yaml", content="openapi: 3.1.0")
    assert source.uri == "https://example.com/openapi.yaml"
    assert source.content == "openapi: 3.1.0"

def test_openapi_document():
    doc = OpenAPIDocument(version="3.1.0", paths={"/test": {}}, components={"schemas": {}})
    assert doc.version == "3.1.0"
    assert "/test" in doc.paths
    assert "schemas" in doc.components

def test_openapi_bundle():
    doc = OpenAPIDocument(version="3.1.0")
    bundle = OpenAPIBundle(document=doc, resolved_refs=["file:///schema.json"])
    assert bundle.document.version == "3.1.0"
    assert "file:///schema.json" in bundle.resolved_refs

def test_openapi_diff():
    diff = OpenAPIDiff(added=["/new-path"], removed=["/old-path"], changed=["/changed-path"])
    assert "/new-path" in diff.added
    assert "/old-path" in diff.removed
    assert "/changed-path" in diff.changed

def test_overlay_patch():
    patch = OverlayPatch(actions=[{"target": "$.info.title", "update": "New Title"}])
    assert patch.actions[0]["target"] == "$.info.title"

def test_validation_finding():
    finding = ValidationFinding(path="$.paths./test", message="Missing description", severity="warn")
    assert finding.path == "$.paths./test"
    assert finding.severity == "warn"

def test_breaking_change_report():
    report = BreakingChangeReport(breaking_changes=["Removed path /old"])
    assert "Removed path /old" in report.breaking_changes

def test_agent_readiness_report():
    report = AgentReadinessReport(is_ready=False, warnings=["Missing operationId on GET /test"])
    assert not report.is_ready
    assert "Missing operationId on GET /test" in report.warnings
