import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec

def _get_module():
    return ModuleSpec(
        name="test_monitor",
        operations=[OperationSpec(name="op1", method="GET", path="/monitor-path")]
    )

def test_bump_sh_generator():
    gen = get_generator("bump-sh-manifest")
    out = gen.generate(_get_module())
    content = out["test_monitor-bump.yaml"]
    assert "api: test_monitor-api" in content
    assert "file: test_monitor.openapi.json" in content
    assert "auto_create: true" in content

def test_specway_generator():
    gen = get_generator("specway-monitor")
    out = gen.generate(_get_module())
    
    import yaml
    data = yaml.safe_load(out["test_monitor-specway.yaml"])
    
    assert data["monitor"] == "test_monitor"
    assert data["schema"] == "./test_monitor.openapi.json"
    assert "/monitor-path" in data["endpoints"]
