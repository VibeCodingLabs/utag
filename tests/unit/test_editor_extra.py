import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec

def _get_module():
    return ModuleSpec(
        name="test_editor",
        operations=[OperationSpec(name="op1", method="GET", path="/test-path")]
    )

def test_stoplight_generator():
    gen = get_generator("stoplight-studio-project")
    out = gen.generate(_get_module())
    assert '{"version": "1.0.0"}' in out["test_editor-stoplight/stoplight.json"]
    assert "name: test_editor\n" in out["test_editor-stoplight/project.yaml"]

def test_swaggerhub_generator():
    gen = get_generator("swaggerhub-sync-manifest")
    out = gen.generate(_get_module())
    content = out["test_editor-swaggerhub.yaml"]
    assert "api: test_editor" in content
    assert "file: test_editor.openapi.json" in content

def test_api_fiddle_generator():
    gen = get_generator("api-fiddle-workspace")
    out = gen.generate(_get_module())
    import json
    data = json.loads(out["test_editor-fiddle.json"])
    assert data["workspace"] == "test_editor"
    assert "/test-path" in data["endpoints"]
