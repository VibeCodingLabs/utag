import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_redocly_respect_config_generator_content():
    gen = get_generator("redocly-respect-config")
    out = gen.generate(ModuleSpec(name="test_respect"))
    
    import yaml
    data = yaml.safe_load(out["test_respect-respect.yaml"])
    
    assert "recommended" in data["extends"]
    assert "operation-description" in data["rules"]
    assert data["rules"]["operation-description"] == "error"
    assert "test_respect@v1" in data["apis"]
    assert data["apis"]["test_respect@v1"]["root"] == "./test_respect.openapi.json"
