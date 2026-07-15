from utag_core.editor import (
    OpenAPIEditorModel,
    ArazzoEditorModel,
    OverlayEditorModel,
    DiffReviewModel,
    ValidationPanelModel
)

def test_openapi_editor_model():
    m = OpenAPIEditorModel(source_uri="file.yaml", positions={"/paths/x": "line 10"})
    assert m.source_uri == "file.yaml"
    assert "/paths/x" in m.positions

def test_arazzo_editor_model():
    m = ArazzoEditorModel(workflow_id="wf1", nodes=[{"id": "n1"}], edges=[])
    assert m.workflow_id == "wf1"
    assert len(m.nodes) == 1

def test_overlay_editor_model():
    m = OverlayEditorModel(base_uri="base.yaml", actions=[{"target": "$.info"}])
    assert m.base_uri == "base.yaml"
    assert len(m.actions) == 1

def test_diff_review_model():
    m = DiffReviewModel(changes_by_pointer={"$.info.title": "changed"})
    assert "$.info.title" in m.changes_by_pointer

def test_validation_panel_model():
    m = ValidationPanelModel(findings_by_severity={"error": ["missing field"]}, findings_by_source={"file.yaml": ["missing field"]})
    assert "error" in m.findings_by_severity
    assert "file.yaml" in m.findings_by_source
