import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec

def _get_module():
    return ModuleSpec(
        name="testmod",
        operations=[
            OperationSpec(name="op1", method="GET", path="/test")
        ]
    )

def test_docs_reference_generators():
    for name in ["redoc-compatible-reference", "scalar-compatible-reference"]:
        gen = get_generator(name)
        out = gen.generate(_get_module())
        
        # Check standard properties
        assert len(out) == 1
        content = list(out.values())[0]
        assert "<!DOCTYPE html>" in content
        assert "testmod.openapi.json" in content

def test_apisix_gateway_config_generator():
    gen = get_generator("apisix-gateway-config")
    out = gen.generate(_get_module())
    
    import yaml
    data = yaml.safe_load(out["testmod-apisix.yaml"])
    
    assert "routes" in data
    assert len(data["routes"]) == 1
    assert data["routes"][0]["uri"] == "/test"

def test_mock_server_generator():
    gen = get_generator("mock-server")
    out = gen.generate(_get_module())
    
    content = out["testmod-mock.js"]
    assert "const express = require" in content
    assert "app.get('/test', (req, res) => {" in content
    assert "res.status(200).json" in content
