from __future__ import annotations
from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator

@register_generator("fastmcp-server")
class FastmcpServerGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {f"{module.name}_fastmcp.py": "# fastmcp server stub\n"}

@register_generator("typescript-mcp-server")
class TypescriptMcpServerGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {f"{module.name}-mcp.ts": "// typescript mcp server stub\n"}

@register_generator("mcp-tool-manifest")
class McpToolManifestGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import json
        tools = []
        
        for op in module.operations:
            input_schema = {
                "type": "object",
                "properties": {}
            }
            required = []
            
            # Path params
            for p in op.request.path_params:
                input_schema["properties"][p.name] = {"type": "string", "description": "Path parameter"}
                if p.required:
                    required.append(p.name)
                    
            # Query params
            for q in op.request.query_params:
                input_schema["properties"][q.name] = {"type": "string", "description": "Query parameter"}
                if q.required:
                    required.append(q.name)
                    
            if op.request.body_type:
                input_schema["properties"]["body"] = {"type": "object", "$ref": f"#/components/schemas/{op.request.body_type}"}
                required.append("body")
                
            if required:
                input_schema["required"] = required
                
            tools.append({
                "name": op.name,
                "description": op.description or f"Execute {op.name}",
                "inputSchema": input_schema,
                "authRequired": True, # default secure assumption
                "sideEffect": "write" if op.method.upper() in ["POST", "PUT", "PATCH", "DELETE"] else "read",
            })
            
        manifest = {
            "version": "1.0.0",
            "tools": tools
        }
        return {f"{module.name}-mcp-tools.json": json.dumps(manifest, indent=2) + "\n"}

@register_generator("mcp-gateway-config")
class McpGatewayConfigGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {f"{module.name}-gateway.yaml": "# mcp gateway config stub\n"}

@register_generator("mcp-app-ui-manifest")
class McpAppUiManifestGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {f"{module.name}-ui.json": "{}\n"}

@register_generator("agentify-bundle")
class AgentifyBundleGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {f"{module.name}-agentify.zip": "binary_stub\n"}

@register_generator("llms-txt")
class LlmsTxtGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {"llms.txt": "llms.txt stub\n"}

@register_generator("agents-md")
class AgentsMdGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {"AGENTS.md": "AGENTS.md stub\n"}

@register_generator("skill-md")
class SkillMdGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {"SKILL.md": "SKILL.md stub\n"}
