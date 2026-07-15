from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_testing_ecosystem_generators():
    targets = [
        "mock-server",
        "wiremock-stubs",
        "prism-config",
        "schemathesis-suite",
        "hurl-tests",
        "postman-collection",
        "contract-test-suite",
        "behavior-verification-manifest",
    ]
    module = ModuleSpec(name="testmod")
    for t in targets:
        gen = get_generator(t)
        assert gen is not None, f"Generator {t} not found"
        out = gen.generate(module)
        assert len(out) > 0
