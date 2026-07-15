from __future__ import annotations
from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator

@register_generator("docs-portal-static")
class DocsPortalStaticGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        lines = ["<!DOCTYPE html>"]
        lines.append("<html>")
        lines.append("<head>")
        lines.append(f"  <title>{module.name} API Documentation</title>")
        lines.append("  <style>")
        lines.append("    body { font-family: sans-serif; margin: 40px; }")
        lines.append("    .type, .op { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; }")
        lines.append("  </style>")
        lines.append("</head>")
        lines.append("<body>")
        lines.append(f"  <h1>{module.name} API Reference</h1>")
        if module.description:
            lines.append(f"  <p>{module.description}</p>")
            
        lines.append("  <h2>Types</h2>")
        for t in module.types:
            lines.append('  <div class="type">')
            lines.append(f"    <h3>{t.name}</h3>")
            if t.description: lines.append(f"    <p>{t.description}</p>")
            lines.append("    <ul>")
            for f in t.fields:
                req = "" if f.required else " (optional)"
                lines.append(f"      <li><strong>{f.name}</strong>: <code>{f.type.value if hasattr(f.type, 'value') else f.type}</code>{req}</li>")
            lines.append("    </ul>")
            lines.append("  </div>")
            
        lines.append("  <h2>Operations</h2>")
        for op in module.operations:
            lines.append('  <div class="op">')
            lines.append(f"    <h3>{op.method.upper()} {op.path}</h3>")
            lines.append(f"    <p><strong>Operation ID:</strong> {op.name}</p>")
            if op.description: lines.append(f"    <p>{op.description}</p>")
            
            if op.request.path_params or op.request.query_params or op.request.body_type:
                lines.append("    <h4>Request</h4><ul>")
                for p in op.request.path_params:
                    lines.append(f"      <li>Path: <strong>{p.name}</strong></li>")
                for q in op.request.query_params:
                    lines.append(f"      <li>Query: <strong>{q.name}</strong></li>")
                if op.request.body_type:
                    lines.append(f"      <li>Body: <code>{op.request.body_type}</code></li>")
                lines.append("    </ul>")
                
            if op.responses:
                lines.append("    <h4>Responses</h4><ul>")
                for r in op.responses:
                    b = f": <code>{r.body_type}</code>" if r.body_type else ""
                    lines.append(f"      <li>{r.status_code}{b}</li>")
                lines.append("    </ul>")
            lines.append("  </div>")
            
        lines.append("</body>")
        lines.append("</html>")
        return {f"{module.name}-portal/index.html": "\n".join(lines)}

@register_generator("redoc-compatible-reference")
class RedocCompatibleReferenceGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        html = f"""<!DOCTYPE html>
<html>
  <head>
    <title>{module.name} Redoc Reference</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
  </head>
  <body>
    <redoc spec-url="./{module.name}.openapi.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"> </script>
  </body>
</html>"""
        return {f"{module.name}-redoc.html": html}

@register_generator("scalar-compatible-reference")
class ScalarCompatibleReferenceGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        html = f"""<!DOCTYPE html>
<html>
  <head>
    <title>{module.name} Scalar Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <script
      id="api-reference"
      data-url="./{module.name}.openapi.json"
    ></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>"""
        return {f"{module.name}-scalar.html": html}

@register_generator("zudoku-compatible-site")
class ZudokuCompatibleSiteGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        html = f"""<!DOCTYPE html>
<html>
  <head>
    <title>{module.name} Zudoku API</title>
    <meta charset="utf-8" />
  </head>
  <body>
    <div id="zudoku"></div>
    <script type="module">
      import {{ createZudoku }} from 'https://cdn.jsdelivr.net/npm/zudoku/dist/index.js';
      createZudoku({{
        api: {{
          url: "./{module.name}.openapi.json"
        }}
      }});
    </script>
  </body>
</html>"""
        return {f"{module.name}-zudoku/index.html": html}

@register_generator("mintlify-compatible-content")
class MintlifyCompatibleContentGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        import json
        pages = []
        for op in module.operations:
            slug = op.name.lower()
            pages.append(f"api-reference/{slug}")
            
        mint_config = {
            "name": module.name,
            "logo": {
                "dark": "/logo/dark.svg",
                "light": "/logo/light.svg"
            },
            "navigation": [
                {
                    "group": "API Reference",
                    "pages": pages
                }
            ]
        }
        return {f"{module.name}-mintlify/mint.json": json.dumps(mint_config, indent=2) + "\n"}

@register_generator("search-index")
class SearchIndexGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {"search-index.json": "{}\n"}

@register_generator("api-guides")
class ApiGuidesGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        intro = f"# {module.name} API Guide\n\n{module.description}\n\nWelcome to the API."
        auth = f"# Authentication\n\nAll endpoints in {module.name} require a Bearer token."
        return {
            f"{module.name}-guides/intro.md": intro,
            f"{module.name}-guides/auth.md": auth
        }

@register_generator("api-changelog")
class ApiChangelogGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        lines = [f"# {module.name} Changelog", "", "## Initial Release", ""]
        if module.operations:
            lines.append("### Operations Added")
            for op in module.operations:
                lines.append(f"- `[{op.method.upper()}] {op.path}`")
            lines.append("")
        if module.types:
            lines.append("### Types Added")
            for t in module.types:
                lines.append(f"- `{t.name}`")
            lines.append("")
            
        return {f"{module.name}-changelog.md": "\n".join(lines)}

@register_generator("sitemap")
class SitemapGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        for op in module.operations:
            # Remove OpenAPI path params for simple HTML page routes
            import re
            clean_path = re.sub(r'\{[^}]+\}', '', op.path).strip('/')
            url = f"https://example.com/api/{clean_path}" if clean_path else "https://example.com/api"
            
            lines.append('  <url>')
            lines.append(f'    <loc>{url}</loc>')
            lines.append('  </url>')
            
        lines.append('</urlset>')
        return {f"{module.name}-sitemap.xml": "\n".join(lines)}
class SearchIndexGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {"search-index.json": "{}\n"}

@register_generator("agent-score-report")
class AgentScoreReportGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        score = 100
        penalties = []
        
        if not module.description:
            score -= 10
            penalties.append("- Missing module description")
            
        for op in module.operations:
            if not op.description:
                score -= 5
                penalties.append(f"- Missing description for operation {op.name}")
                
        for t in module.types:
            if not t.description:
                score -= 2
                penalties.append(f"- Missing description for type {t.name}")
                
        lines = [
            f"# Agent Readiness Score: {score}/100",
            "",
            f"Module: {module.name}",
            ""
        ]
        
        if penalties:
            lines.append("## Penalties")
            lines.extend(penalties)
        else:
            lines.append("Perfect score! The API is fully documented for agent consumption.")
            
        return {"agent-score-report.md": "\n".join(lines) + "\n"}
