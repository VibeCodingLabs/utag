import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def _get_module():
    return ModuleSpec(name="test_prism_schema")

def test_prism_config_generator():
    gen = get_generator("prism-config")
    out = gen.generate(_get_module())
    
    content = out["test_prism_schema-prism.yaml"]
    assert "mock:" in content
    assert "port: 4010" in content
    assert "spec: ./test_prism_schema.openapi.json" in content

def test_schemathesis_suite_generator():
    gen = get_generator("schemathesis-suite")
    out = gen.generate(_get_module())
    
    content = out["test_prism_schema-schemathesis.py"]
    assert "import schemathesis" in content
    assert '@schema.parametrize()' in content
    assert "case.call_and_validate()" in content
