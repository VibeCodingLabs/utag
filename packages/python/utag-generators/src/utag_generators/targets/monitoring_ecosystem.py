from __future__ import annotations
from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator

@register_generator("redocly-respect-config")
class RedoclyRespectConfigGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import yaml
        config = {
            "extends": ["recommended"],
            "rules": {
                "operation-description": "error",
                "operation-2xx-response": "error",
                "path-parameters-defined": "error"
            },
            "apis": {
                f"{module.name}@v1": {
                    "root": f"./{module.name}.openapi.json"
                }
            }
        }
        
        return {f"{module.name}-respect.yaml": yaml.safe_dump(config, sort_keys=False)}

@register_generator("bump-sh-manifest")
class BumpShManifestGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        content = f"api: {module.name}-api\nfile: {module.name}.openapi.json\nauto_create: true\n"
        return {f"{module.name}-bump.yaml": content}

@register_generator("specway-monitor")
class SpecwayMonitorGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import yaml
        config = {
            "monitor": module.name,
            "schema": f"./{module.name}.openapi.json",
            "endpoints": [op.path for op in module.operations]
        }
        return {f"{module.name}-specway.yaml": yaml.safe_dump(config, sort_keys=False)}
