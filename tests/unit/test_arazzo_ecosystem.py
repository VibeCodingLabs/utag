from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_arazzo_ecosystem_generators():
    targets = [
        "arazzo-workflows",
        "arazzo-agent-workflows",
        "arazzo-ui-model",
        "overlay-patch",
        "overlay-diff",
        "workflow-test-suite",
    ]
    module = ModuleSpec(name="arazzomod")
    for t in targets:
        gen = get_generator(t)
        assert gen is not None, f"Generator {t} not found"
        out = gen.generate(module)
        assert len(out) > 0
