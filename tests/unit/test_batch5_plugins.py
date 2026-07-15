import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def _get_module():
    return ModuleSpec(name="testmod")

def test_schemathesis_generator():
    gen = get_generator("schemathesis-suite")
    out = gen.generate(_get_module())
    assert "testmod-schemathesis.py" in out
    assert "import schemathesis" in out["testmod-schemathesis.py"]
    assert "@schema.parametrize()" in out["testmod-schemathesis.py"]

def test_mcp_gateway_generator():
    gen = get_generator("mcp-gateway-config")
    out = gen.generate(_get_module())
    import yaml
    data = yaml.safe_load(out["testmod-gateway.yaml"])
    assert data["name"] == "testmod"
    assert data["proxy"]["enabled"] is True
