from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def _get_module():
    return ModuleSpec(name="test_mcp_extra")

def test_typescript_mcp_server_generator():
    gen = get_generator("typescript-mcp-server")
    out = gen.generate(_get_module())
    content = out["test_mcp_extra-mcp.ts"]
    assert 'import { Server } from "@modelcontextprotocol/sdk/server/index.js";' in content
    assert 'const server = new Server({ name: "test_mcp_extra", version: "1.0.0" }, {});' in content

def test_mcp_ui_manifest_generator():
    gen = get_generator("mcp-app-ui-manifest")
    out = gen.generate(_get_module())
    import json
    data = json.loads(out["test_mcp_extra-ui.json"])
    assert data["name"] == "test_mcp_extra"
    assert "sidebar" in data["ui_elements"]

def test_agentify_bundle_generator():
    gen = get_generator("agentify-bundle")
    out = gen.generate(_get_module())
    import json
    data = json.loads(out["test_mcp_extra-agentify.json"])
    assert data["bundle"] == "test_mcp_extra"


def test_fastmcp_server_metadata():
    gen = get_generator("fastmcp-server")
    out = gen.generate(_get_module())
    import json
    data = json.loads(out["test_mcp_extra-sdk-metadata.json"])
    assert data["target"] == "fastmcp-server"
    assert data["implemented"] is False

def test_skill_md_metadata():
    gen = get_generator("skill-md")
    out = gen.generate(_get_module())
    import json
    data = json.loads(out["test_mcp_extra-sdk-metadata.json"])
    assert data["target"] == "skill-md"
    assert data["implemented"] is False