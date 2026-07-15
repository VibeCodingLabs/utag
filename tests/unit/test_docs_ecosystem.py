from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_docs_ecosystem_generators():
    targets = [
        "docs-portal-static",
        "redoc-compatible-reference",
        "scalar-compatible-reference",
        "zudoku-compatible-site",
        "mintlify-compatible-content",
        "api-guides",
        "api-changelog",
        "sitemap",
        "search-index",
        "agent-score-report",
    ]
    module = ModuleSpec(name="docsmod")
    for t in targets:
        gen = get_generator(t)
        assert gen is not None, f"Generator {t} not found"
        out = gen.generate(module)
        assert len(out) > 0
