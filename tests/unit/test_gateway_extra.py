import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def _get_module():
    return ModuleSpec(name="test_gateway")

def test_membrane_policy_generator():
    gen = get_generator("membrane-policy")
    out = gen.generate(_get_module())
    import yaml
    data = yaml.safe_load(out["test_gateway-membrane.yaml"])
    assert data["name"] == "test_gateway"
    assert "rate-limit" in data["policies"]

def test_oauth2_proxy_config_generator():
    gen = get_generator("oauth2-proxy-config")
    out = gen.generate(_get_module())
    content = out["test_gateway-oauth2-proxy.cfg"]
    assert "email_domains = ['*']" in content
    assert "upstreams = ['http://backend:8080']" in content

def test_rate_limit_policy_generator():
    gen = get_generator("rate-limit-policy")
    out = gen.generate(_get_module())
    import yaml
    data = yaml.safe_load(out["test_gateway-rate-limit.yaml"])
    assert data["rate_limit"]["requests_per_second"] == 100
