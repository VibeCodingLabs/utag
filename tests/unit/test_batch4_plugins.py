import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec

def _get_module():
    return ModuleSpec(
        name="testmod",
        operations=[
            OperationSpec(name="op1", method="GET", path="/test/{id}")
        ]
    )

def test_mintlify_content_generator():
    gen = get_generator("mintlify-compatible-content")
    out = gen.generate(_get_module())
    
    import json
    data = json.loads(out["testmod-mintlify/mint.json"])
    assert data["name"] == "testmod"
    assert "navigation" in data
    assert len(data["navigation"]) == 1
    assert "api-reference/op1" in data["navigation"][0]["pages"]

def test_sitemap_generator():
    gen = get_generator("sitemap")
    out = gen.generate(_get_module())
    
    content = out["testmod-sitemap.xml"]
    assert "<?xml version=" in content
    assert "<urlset xmlns=" in content
    # path was /test/{id}, stripped down to /test
    assert "<loc>https://example.com/api/test</loc>" in content

def test_zuplo_gateway_config_generator():
    gen = get_generator("zuplo-gateway-config")
    out = gen.generate(_get_module())
    
    import json
    data = json.loads(out["testmod-zuplo.json"])
    assert "routes" in data
    assert len(data["routes"]) == 1
    
    route = data["routes"][0]
    assert route["path"] == "/test/:id"
    assert route["methods"][0] == "GET"
    assert route["handler"]["export"] == "urlRewrite"
