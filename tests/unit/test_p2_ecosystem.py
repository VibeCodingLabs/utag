from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_p2_ecosystem_generators():
    targets = [
        "kong-gateway-config",
        "zuplo-gateway-config",
        "apisix-gateway-config",
        "barbacane-policy",
        "membrane-policy",
        "oauth2-proxy-config",
        "opa-policy",
        "rate-limit-policy",
        "stoplight-studio-project",
        "swaggerhub-sync-manifest",
        "api-fiddle-workspace",
        "redocly-respect-config",
        "bump-sh-manifest",
        "specway-monitor",
    ]
    module = ModuleSpec(name="p2mod")
    for t in targets:
        gen = get_generator(t)
        assert gen is not None, f"Generator {t} not found"
        out = gen.generate(module)
        assert len(out) > 0
