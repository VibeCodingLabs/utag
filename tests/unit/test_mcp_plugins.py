import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec, RequestSpec, FieldSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="test_mcp",
        operations=[
            OperationSpec(
                name="createUser",
                method="POST",
                path="/users",
                request=RequestSpec(path_params=[FieldSpec(name="id", type=ScalarKind.string, required=True)]),
            )
        ]
    )

def test_mcp_tool_manifest_generator_content():
    gen = get_generator("mcp-tool-manifest")
    out = gen.generate(_get_module())
    
    import json
    data = json.loads(out["test_mcp-mcp-tools.json"])
    
    assert data["version"] == "1.0.0"
    assert len(data["tools"]) == 1
    
    tool = data["tools"][0]
    assert tool["name"] == "createUser"
    assert tool["sideEffect"] == "write"
    assert "id" in tool["inputSchema"]["properties"]
    assert "id" in tool["inputSchema"]["required"]
