"""design.yaml -> UI pipeline (v2.14.0 Phase 3).

Three deterministic generators consume the strict `DesignYaml` contract from
`module.provenance["design_yaml"]`:
  design-tokens-css      -> tokens.css / theme.css / dark.css / motion.css
                            + tokens.json + css-variables.manifest.json
  tailwind-v4-theme      -> tailwind.css (CSS-first @theme mapping)
  react-component-library-> typed TSX components/layouts/routes with
                            accessibility attributes; colors only via var(--utag-*)
"""
from __future__ import annotations

import json

import yaml

from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator
from utag_core.schemas.core import GeneratorManifest
from utag_core.schemas.design import CssVariable, CssVariableManifest, DesignYaml

# design token family -> CSS variable family (prompt-contracted names)
_FAMILY = {"color": "color", "spacing": "space", "radius": "radius",
           "typography": "font", "shadow": "shadow", "motion": "motion"}


def _design(module: ModuleSpec) -> DesignYaml:
    raw = module.provenance.get("design_yaml")
    if not raw:
        raise ValueError("design generators need module.provenance['design_yaml']")
    return DesignYaml.model_validate(yaml.safe_load(raw))


def _variables(design: DesignYaml) -> list[CssVariable]:
    out = []
    for field, family in sorted(_FAMILY.items()):
        for key, value in sorted(getattr(design.tokens, field).items()):
            out.append(CssVariable(name=f"--utag-{family}-{key}", value=value))
    return out


def _block(selector: str, pairs: list[tuple[str, str]]) -> str:
    body = "\n".join(f"  {name}: {value};" for name, value in pairs)
    return f"{selector} {{\n{body}\n}}\n"


def _manifest(id_: str, outputs: list[str]) -> GeneratorManifest:
    return GeneratorManifest(
        id=id_, name=id_, version="1.0.0",
        input_schema="design-yaml", output_schema="css-variable-manifest",
        output_files=outputs,
        entrypoints=[f"utag generate --target {id_}", "utag design app"],
        test_files=["tests/unit/test_design_tokens.py", "tests/unit/test_udc_generators.py",
                    "tests/golden/test_determinism.py"],
        validation_gates=["schema", "golden"])


@register_generator("design-tokens-css", manifest=_manifest(
    "design-tokens-css", ["styles/tokens.css", "styles/theme.css", "styles/dark.css",
                          "styles/motion.css", "styles/tokens.json",
                          "styles/css-variables.manifest.json"]))
class DesignTokensCssGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        design = _design(module)
        variables = _variables(design)
        manifest = CssVariableManifest(file="styles/tokens.css", source_design=design.id,
                                       variables=variables)
        theme_css = "".join(
            _block(f':root[data-theme="{name}"]',
                   [(f"--utag-color-{k}", v) for k, v in sorted(tokens.items())])
            for name, tokens in sorted(design.themes.items()) if name != "dark")
        dark = design.themes.get("dark", {})
        dark_pairs = [(f"--utag-color-{k}", v) for k, v in sorted(dark.items())]
        dark_css = ""
        if dark_pairs:
            dark_css = (_block(':root[data-theme="dark"]', dark_pairs)
                        + "@media (prefers-color-scheme: dark) {\n"
                        + "".join("  " + line + "\n" for line in
                                  _block(":root:not([data-theme])", dark_pairs).splitlines())
                        + "}\n")
        motion_css = (
            "@media (prefers-reduced-motion: reduce) {\n"
            "  *, *::before, *::after {\n"
            "    animation-duration: 0.01ms !important;\n"
            "    transition-duration: 0.01ms !important;\n"
            "  }\n"
            "}\n")
        return {
            "styles/tokens.css": _block(":root", [(v.name, v.value) for v in variables]),
            "styles/theme.css": theme_css or "/* no non-dark themes declared */\n",
            "styles/dark.css": dark_css or "/* no dark theme declared */\n",
            "styles/motion.css": motion_css,
            "styles/tokens.json": json.dumps({v.name: v.value for v in variables},
                                             indent=2, sort_keys=True) + "\n",
            "styles/css-variables.manifest.json":
                manifest.model_dump_json(indent=2, exclude_none=True) + "\n",
        }


@register_generator("tailwind-v4-theme", manifest=_manifest(
    "tailwind-v4-theme", ["styles/tailwind.css"]))
class TailwindV4ThemeGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        design = _design(module)
        pairs = []
        for field, family in sorted(_FAMILY.items()):
            tw = {"space": "spacing", "motion": "transition-duration"}.get(family, family)
            for key in sorted(getattr(design.tokens, field)):
                pairs.append((f"--{tw}-{key}", f"var(--utag-{family}-{key})"))
        return {"styles/tailwind.css":
                '@import "tailwindcss";\n\n' + _block("@theme", pairs)}


_ARIA_ROLE = {"card": "group", "panel": "region", "table": None}  # table is semantic


def _pascal(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-"))


def _ts_type(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return "string"


def _component_tsx(spec) -> str:
    name = _pascal(spec.id)
    prop_lines = [f"  {k}?: {_ts_type(v)};" for k, v in sorted(spec.props.items())]
    states = " | ".join(f'"{s}"' for s in spec.states) or '"idle"'
    role = _ARIA_ROLE.get(spec.type)
    if spec.type == "table":
        body = (f'    <table aria-label="{spec.id}" data-state={{state}}>\n'
                "      <tbody>{children}</tbody>\n"
                "    </table>")
    else:
        role_attr = f' role="{role}"' if role else ""
        body = (f'    <section{role_attr} aria-label="{spec.id}" data-state={{state}} tabIndex={{0}}\n'
                '      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>\n'
                "      {children}\n"
                "    </section>")
    props_block = "\n".join(prop_lines)
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
import React from "react";

export type {name}State = {states};

export interface {name}Props {{
{props_block}
  state?: {name}State;
  children?: React.ReactNode;
}}

export function {name}({{ state = {json.dumps(spec.states[0] if spec.states else "idle")}, children }}: {name}Props) {{
  return (
{body}
  );
}}
"""


_REGION_TAG = {"sidebar": "aside", "header": "header", "main": "main",
               "footer": "footer", "inspector": "aside"}


def _layout_tsx(layout) -> str:
    name = _pascal(layout.id)
    slots = ", ".join(layout.regions)
    props = "\n".join(f"  {r}?: React.ReactNode;" for r in layout.regions)
    areas = " ".join(f'"{r}"' for r in layout.regions)
    regions = "\n".join(
        f'      <{_REGION_TAG.get(r, "section")} aria-label="{r}" '
        f'style={{{{ gridArea: "{r}" }}}}>{{{r}}}</{_REGION_TAG.get(r, "section")}>'
        for r in layout.regions)
    return f"""// generated from design.yaml layout `{layout.id}` — do not edit by hand
import React from "react";

export interface {name}Props {{
{props}
}}

export function {name}({{ {slots} }}: {name}Props) {{
  return (
    <div style={{{{ display: "grid", gridTemplateAreas: {json.dumps(areas)}, gap: "var(--utag-space-2)" }}}}>
{regions}
    </div>
  );
}}
"""


def _route_tsx(route, design: DesignYaml) -> str:
    name = _pascal(route.path.strip("/").replace("/", "-") or "home") + "Page"
    layout = _pascal(route.layout)
    comps = [_pascal(c) for c in route.components]
    imports = "\n".join(f'import {{ {c} }} from "../components/{c}";' for c in sorted(set(comps)))
    children = "\n".join(f"        <{c} />" for c in comps)
    return f"""// generated from design.yaml route `{route.path}` — do not edit by hand
import React from "react";
import {{ {layout} }} from "../layouts/{layout}";
{imports}

export function {name}() {{
  return (
    <{layout}
      main={{
        <>
{children}
        </>
      }}
    />
  );
}}
"""


@register_generator("react-component-library", manifest=_manifest(
    "react-component-library", ["generated/components/*.tsx", "generated/layouts/*.tsx",
                                "generated/routes/*.tsx"]))
class ReactComponentLibraryGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        design = _design(module)
        out: dict[str, str] = {}
        for spec in design.components:
            out[f"generated/components/{_pascal(spec.id)}.tsx"] = _component_tsx(spec)
        for layout in design.layouts:
            out[f"generated/layouts/{_pascal(layout.id)}.tsx"] = _layout_tsx(layout)
        for route in design.routes:
            name = _pascal(route.path.strip("/").replace("/", "-") or "home") + "Page"
            out[f"generated/routes/{name}.tsx"] = _route_tsx(route, design)
        return out
