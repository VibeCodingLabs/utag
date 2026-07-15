from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_mcp_ecosystem_generators():
    targets = [
        "fastmcp-server",
        "typescript-mcp-server",
        "mcp-tool-manifest",
        "mcp-gateway-config",
        "mcp-app-ui-manifest",
        "agentify-bundle",
        "llms-txt",
        "agents-md",
        "skill-md",
    ]
    module = ModuleSpec(name="mcpmod")
    for t in targets:
        gen = get_generator(t)
        assert gen is not None, f"Generator {t} not found"
        out = gen.generate(module)
        assert len(out) > 0
