from __future__ import annotations
from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator

@register_generator("stoplight-studio-project")
class StoplightStudioProjectGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {
            f"{module.name}-stoplight/stoplight.json": '{"version": "1.0.0"}',
            f"{module.name}-stoplight/project.yaml": f"name: {module.name}\nopenapi: ./{module.name}.openapi.json\n"
        }

@register_generator("swaggerhub-sync-manifest")
class SwaggerhubSyncManifestGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        content = f"swaggerhub:\n  api: {module.name}\n  owner: utag\n  file: {module.name}.openapi.json\n"
        return {f"{module.name}-swaggerhub.yaml": content}

@register_generator("api-fiddle-workspace")
class ApiFiddleWorkspaceGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import json
        out = {
            "workspace": module.name,
            "endpoints": [op.path for op in module.operations]
        }
        return {f"{module.name}-fiddle.json": json.dumps(out, indent=2)}
