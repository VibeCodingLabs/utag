from __future__ import annotations
from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator

@register_generator("kong-gateway-config")
class KongGatewayConfigGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import yaml
        
        # Extract unique paths (Kong routes by path/method)
        paths = set()
        for op in module.operations:
            # Strip OpenAPI path parameters to bare prefixes or regexes for Kong
            # E.g. /users/{id} -> /users/
            import re
            kong_path = re.sub(r'\{[^}]+\}', '', op.path)
            paths.add(kong_path)
            
        routes = []
        for idx, path in enumerate(sorted(paths)):
            # If path ends with /, it indicates it had stripped params, add regex marker
            kong_path_str = f"~^{path}" if path.endswith("/") and path != "/" else path
            routes.append({
                "name": f"{module.name}-route-{idx}",
                "paths": [kong_path_str],
                "strip_path": False
            })
            
        deck_format = {
            "_format_version": "3.0",
            "services": [
                {
                    "name": f"{module.name}-service",
                    "url": "http://backend-service:8080",
                    "routes": routes
                }
            ]
        }
        
        return {f"{module.name}-kong.yaml": yaml.safe_dump(deck_format, sort_keys=False)}

@register_generator("zuplo-gateway-config")
class ZuploGatewayConfigGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import json
        import re
        
        routes = []
        for op in module.operations:
            zuplo_path = re.sub(r'\{([^}]+)\}', r':\1', op.path)
            routes.append({
                "path": zuplo_path,
                "methods": [op.method.upper()],
                "corsPolicy": "none",
                "handler": {
                    "export": "urlRewrite",
                    "module": "zuplo.runtime",
                    "options": {
                        "rewrite": f"https://api.backend.internal{zuplo_path}"
                    }
                }
            })
            
        return {f"{module.name}-zuplo.json": json.dumps({"routes": routes}, indent=2) + "\n"}

@register_generator("apisix-gateway-config")
class ApisixGatewayConfigGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import yaml
        import re
        
        routes = []
        for idx, op in enumerate(module.operations):
            # APISIX routing uses explicit URIs
            # e.g., /users/*
            apisix_path = re.sub(r'\{[^}]+\}', '*', op.path)
            routes.append({
                "uri": apisix_path,
                "methods": [op.method.upper()],
                "upstream": {
                    "type": "roundrobin",
                    "nodes": {
                        "backend-service:8080": 1
                    }
                }
            })
            
        config = {
            "routes": routes
        }
        
        return {f"{module.name}-apisix.yaml": yaml.safe_dump(config, sort_keys=False)}

@register_generator("barbacane-policy")
class BarbacanePolicyGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import yaml
        config = {
            "policy": "barbacane",
            "version": "1.0.0",
            "rules": [
                {"action": "allow", "scope": f"utag:{module.name}:*"}
            ]
        }
        return {f"{module.name}-barbacane.yaml": yaml.safe_dump(config, sort_keys=False)}

@register_generator("opa-policy")
class OpaPolicyGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        lines = [f"package utag.{module.name.replace('-', '_')}"]
        lines.append("")
        lines.append("default allow := false")
        lines.append("")
        lines.append("# Allow operations defined in the module")
        for op in module.operations:
            lines.append(f'allow {{ input.method == "{op.method.upper()}"; input.path == "{op.path}" }}')
        return {f"{module.name}-opa.rego": "\n".join(lines) + "\n"}

@register_generator("membrane-policy")
class MembranePolicyGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        config = {"name": module.name, "policies": ["rate-limit", "auth"]}
        import yaml
        return {f"{module.name}-membrane.yaml": yaml.safe_dump(config, sort_keys=False)}

@register_generator("oauth2-proxy-config")
class Oauth2ProxyConfigGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        config = f"email_domains = ['*']\nupstreams = ['http://backend:8080']\n"
        return {f"{module.name}-oauth2-proxy.cfg": config}

@register_generator("rate-limit-policy")
class RateLimitPolicyGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import yaml
        config = {"rate_limit": {"requests_per_second": 100, "burst": 200}}
        return {f"{module.name}-rate-limit.yaml": yaml.safe_dump(config, sort_keys=False)}
