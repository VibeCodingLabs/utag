"""design.yaml -> UI pipeline (v2.15.0: data-rendering, self-generated console).

Five deterministic generators consume the strict `DesignYaml` contract from
`module.provenance["design_yaml"]`:
  design-tokens-css        -> tokens/theme/dark/motion CSS + tokens.json + manifest
  tailwind-v4-theme        -> tailwind.css (CSS-first @theme mapping)
  typescript-contract-types-> generated/schemas/contracts.ts (TS interfaces for
                              every schema kind referenced by data.contracts)
  design-fixtures          -> generated/fixtures/<resource>.ts (schema-valid mock
                              records so every screen renders offline)
  react-component-library  -> typed TSX components/layouts/routes/hooks that
                              render REAL data from the bound contracts; colors
                              only via var(--utag-*); interactions generated from
                              design.yaml `interactions:`

Component `type` vocabulary (supersedes the once-planned separate dashboard
generators): card, table, matrix, panel, timeline, chart, board, graph, nav.
"""
from __future__ import annotations

import copy
import json
import types
import typing
from enum import Enum

import yaml
from pydantic import BaseModel

from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator
from utag_core.schemas import SCHEMAS
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


def _manifest(id_: str, outputs: list[str], output_schema: str = "css-variable-manifest") -> GeneratorManifest:
    return GeneratorManifest(
        id=id_, name=id_, version="2.0.0",
        input_schema="design-yaml", output_schema=output_schema,
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


# ---------------------------------------------------------------------------
# TypeScript contract emission
# ---------------------------------------------------------------------------

_SCALARS = {str: "string", int: "number", float: "number", bool: "boolean"}


def _ts_of(ann, needed: dict[str, type]) -> str:
    """Pydantic annotation -> TS type; collects nested models into `needed`."""
    if ann in _SCALARS:
        return _SCALARS[ann]
    if ann is typing.Any:
        return "unknown"
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)
    if origin in (typing.Union, types.UnionType):
        parts = [a for a in args if a is not type(None)]
        ts = " | ".join(sorted({_ts_of(a, needed) for a in parts}))
        return f"{ts} | null" if type(None) in args else ts
    if origin is list:
        inner = _ts_of(args[0], needed) if args else "unknown"
        return f"({inner})[]" if " " in inner else f"{inner}[]"
    if origin is dict:
        value = _ts_of(args[1], needed) if len(args) == 2 else "unknown"
        return f"Record<string, {value}>"
    if origin is typing.Literal:
        return " | ".join(json.dumps(a.value if isinstance(a, Enum) else a) for a in args)
    if isinstance(ann, type) and issubclass(ann, Enum):
        return " | ".join(json.dumps(v.value) for v in ann)
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        needed.setdefault(ann.__name__, ann)
        return ann.__name__
    return "unknown"


def _interface(model: type[BaseModel], needed: dict[str, type]) -> str:
    lines = [f"export interface {model.__name__} {{"]
    for name, field in model.model_fields.items():
        opt = "" if field.is_required() else "?"
        lines.append(f"  {name}{opt}: {_ts_of(field.annotation, needed)};")
    lines.append("}")
    return "\n".join(lines)


def contract_models(design: DesignYaml) -> dict[str, type[BaseModel]]:
    """resource -> schema model for every entry in data.contracts (validated)."""
    out = {}
    for resource, kind in sorted(design.data.contracts.items()):
        if kind not in SCHEMAS:
            raise ValueError(f"design data.contracts[{resource!r}] = {kind!r}: unknown schema kind")
        out[resource] = SCHEMAS[kind]
    return out


def _emit_contracts_ts(design: DesignYaml) -> str:
    needed: dict[str, type] = {m.__name__: m for m in contract_models(design).values()}
    emitted: dict[str, str] = {}
    while len(emitted) < len(needed):
        for name, model in sorted(needed.items()):
            if name not in emitted:
                emitted[name] = _interface(model, needed)  # may grow `needed`
    header = "// generated from design.yaml data.contracts — do not edit by hand\n"
    return header + "\n\n".join(emitted[n] for n in sorted(emitted)) + "\n"


@register_generator("typescript-contract-types", manifest=_manifest(
    "typescript-contract-types", ["generated/schemas/contracts.ts"],
    output_schema=None))
class TypescriptContractTypesGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        return {"generated/schemas/contracts.ts": _emit_contracts_ts(_design(module))}


# ---------------------------------------------------------------------------
# Fixtures: schema-valid mock records per resource
# ---------------------------------------------------------------------------

def _ident(resource: str) -> str:
    return resource.replace("-", "_")


def _fixture_records(kind: str, model: type[BaseModel]) -> list[dict]:
    from utag_core.schemas import EXAMPLES
    base = EXAMPLES[kind]
    model.model_validate(base)
    records = [base]
    for n in (2, 3):
        variant = copy.deepcopy(base)
        for key in ("id", "run_id", "span_id", "task_id", "job_id", "operation_id",
                    "artifact_id", "case_id", "name", "task_kind", "tool", "uri"):
            original = variant.get(key)
            if not isinstance(original, str):
                continue
            for suffix in (f"-{n}", f"_{n}"):  # keep whichever the field pattern allows
                variant[key] = f"{original}{suffix}"
                try:
                    model.model_validate(variant)
                    break
                except Exception:  # noqa: BLE001 — pattern mismatch, try next suffix
                    variant[key] = original
            if variant[key] != original:
                break
        model.model_validate(variant)  # never emit an invalid fixture
        records.append(variant)
    return records


@register_generator("design-fixtures", manifest=_manifest(
    "design-fixtures", ["generated/fixtures/*.ts"], output_schema=None))
class DesignFixturesGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        design = _design(module)
        out = {}
        for resource, kind in sorted(design.data.contracts.items()):
            model = SCHEMAS[kind]
            records = _fixture_records(kind, model)
            body = json.dumps(records, indent=2, sort_keys=True)
            out[f"generated/fixtures/{_ident(resource)}.ts"] = (
                f"// generated fixtures for resource `{resource}` ({kind}) — do not edit by hand\n"
                f'import type {{ {model.__name__} }} from "../schemas/contracts";\n\n'
                f"export const {_ident(resource)}: {model.__name__}[] = {body};\n")
        return out


# ---------------------------------------------------------------------------
# React component library: data-rendering, accessible, interaction-wired
# ---------------------------------------------------------------------------

def _pascal(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-"))


def _scalar_fields(model: type[BaseModel], limit: int = 6) -> list[str]:
    cols = []
    for name, field in model.model_fields.items():
        if name == "extensions":
            continue
        ann = field.annotation
        origin = typing.get_origin(ann)
        if origin in (typing.Union, types.UnionType):
            args = [a for a in typing.get_args(ann) if a is not type(None)]
            ann = args[0] if len(args) == 1 else None
        if ann in _SCALARS or (isinstance(ann, type) and issubclass(ann, Enum)):
            cols.append(name)
        if len(cols) == limit:
            break
    return cols


def _first_field(model: type[BaseModel], candidates: tuple[str, ...]) -> str | None:
    return next((c for c in candidates if c in model.model_fields), None)


def _enum_field(model: type[BaseModel], candidates: tuple[str, ...]) -> tuple[str, list[str]] | None:
    for name in candidates:
        field = model.model_fields.get(name)
        if field is not None and isinstance(field.annotation, type) \
                and issubclass(field.annotation, Enum):
            return name, [v.value for v in field.annotation]
    return None


class _Ctx:
    """Generation-time wiring: contracts + interaction roles per component."""

    def __init__(self, design: DesignYaml):
        self.design = design
        self.models = contract_models(design)
        self.sources: dict[str, list[str]] = {}
        self.targets: dict[str, list[str]] = {}
        for i in design.interactions:
            self.sources.setdefault(i.source, []).append(i.id)
            self.targets.setdefault(i.target, []).append(i.id)

    def model_for(self, spec) -> type[BaseModel] | None:
        resource = spec.props.get("resource")
        if resource is None:
            return None
        if resource not in self.models:
            raise ValueError(f"component {spec.id!r}: resource {resource!r} has no "
                             f"entry in design data.contracts")
        return self.models[resource]


_SELECT_HELPERS = """\
// generated from design.yaml interactions — do not edit by hand
import React from "react";

type Selections = Record<string, unknown>;

const SelectionContext = React.createContext<{
  selections: Selections;
  select: (key: string, value: unknown) => void;
}>({ selections: {}, select: () => undefined });

export function SelectionProvider({ children }: { children?: React.ReactNode }) {
  const [selections, setSelections] = React.useState<Selections>({});
  const select = (key: string, value: unknown) =>
    setSelections((prev) => ({ ...prev, [key]: value }));
  return (
    <SelectionContext.Provider value={{ selections, select }}>
      {children}
    </SelectionContext.Provider>
  );
}

export function useSelect(): (key: string, value: unknown) => void {
  return React.useContext(SelectionContext).select;
}

export function useSelected(key: string): unknown {
  return React.useContext(SelectionContext).selections[key];
}
"""

# single-braced object literal; call sites interpolate it as style={{{_BOX_STYLE}}}
# inside f-strings, which renders style={{ ... }}
_BOX_STYLE = ('{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", '
              'padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }')


def _select_call(iids: list[str], value: str) -> str:
    return " ".join(f'select("{iid}", {value});' for iid in iids)


def _component_header(name: str, tname: str | None, uses_select: bool,
                      uses_selected: bool, states: list[str]) -> str:
    imports = ['import React from "react";']
    if tname:
        imports.append(f'import type {{ {tname} }} from "../schemas/contracts";')
    hooks = [h for h, used in (("useSelect", uses_select), ("useSelected", uses_selected)) if used]
    if hooks:
        imports.append(f'import {{ {", ".join(hooks)} }} from "../hooks/useInteractions";')
    state_union = " | ".join(json.dumps(s) for s in states) or '"idle"'
    records_line = f"  records?: {tname}[];\n" if tname else ""
    return (f"{chr(10).join(imports)}\n\n"
            f"export type {name}State = {state_union};\n\n"
            f"export interface {name}Props {{\n"
            f"{records_line}"
            f"  state?: {name}State;\n"
            f"  children?: React.ReactNode;\n"
            f"}}\n")


def _row_handlers(iids: list[str]) -> str:
    if not iids:
        return ""
    call = _select_call(iids, "r")
    return ("\n              onClick={() => { " + call + " }}"
            "\n              onKeyDown={(e: { key: string }) => { "
            'if (e.key === "Enter") { ' + call + " } }}")


def _table_tsx(spec, ctx: _Ctx, dense: bool = False) -> str:
    name = _pascal(spec.id)
    model = ctx.model_for(spec)
    if model is None:
        raise ValueError(f"component {spec.id!r} (type {spec.type}) needs props.resource")
    cols = _scalar_fields(model)
    iids = ctx.sources.get(spec.id, [])
    default_state = json.dumps(spec.states[0] if spec.states else "idle")
    ths = "".join(f"<th>{c}</th>" for c in cols)
    tds = "".join(f"<td>{{String(r.{c} ?? \"\")}}</td>" for c in cols)
    font = ' style={{ font: "var(--utag-font-mono)" }}' if dense else ""
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
{_component_header(name, model.__name__, bool(iids), False, spec.states)}
export function {name}({{ records = [], state = {default_state}, children }}: {name}Props) {{
  {"const select = useSelect();" if iids else ""}
  return (
    <table aria-label="{spec.id}" data-state={{state}}{font}>
      <thead>
        <tr>{ths}</tr>
      </thead>
      <tbody>
        {{records.map((r, i) => (
          <tr key={{i}} tabIndex={{0}}{_row_handlers(iids)}>
            {tds}
          </tr>
        ))}}
      </tbody>
      {{children}}
    </table>
  );
}}
"""


def _panel_tsx(spec, ctx: _Ctx) -> str:
    name = _pascal(spec.id)
    model = ctx.model_for(spec)
    if model is None:
        raise ValueError(f"component {spec.id!r} (type panel) needs props.resource")
    tname = model.__name__
    source_iids = ctx.sources.get(spec.id, [])
    target_iids = ctx.targets.get(spec.id, [])
    default_state = json.dumps(spec.states[0] if spec.states else "idle")
    scalars = set(_scalar_fields(model, limit=99))
    rows = []
    for field in model.model_fields:
        if field == "extensions":
            continue
        if field in scalars:
            rows.append(f"          <dt>{field}</dt><dd>{{String(record.{field} ?? \"\")}}</dd>")
        else:
            rows.append(f"          <dt>{field}</dt>"
                        f"<dd><pre>{{JSON.stringify(record.{field}, null, 2)}}</pre></dd>")
    selected_line = ""
    record_expr = "records[0]"
    if target_iids:
        selected_line = (f'  const selected = useSelected("{target_iids[0]}") as {tname} | undefined;\n')
        record_expr = "selected ?? records[0]"
    click = ""
    if source_iids:
        call = _select_call(source_iids, "record")
        click = ("\n      onClick={() => { if (record) { " + call + " } }}"
                 "\n      onKeyDown={(e: { key: string }) => { "
                 'if (e.key === "Enter" && record) { ' + call + " } }}")
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
{_component_header(name, tname, bool(source_iids), bool(target_iids), spec.states)}
export function {name}({{ records = [], state = {default_state}, children }}: {name}Props) {{
  {"const select = useSelect();" if source_iids else ""}
{selected_line}  const record = {record_expr};
  return (
    <section role="region" aria-label="{spec.id}" data-state={{state}} tabIndex={{0}}{click}
      style={{{_BOX_STYLE}}}>
      {{record ? (
        <dl>
{chr(10).join(rows)}
        </dl>
      ) : (
        <p>No data</p>
      )}}
      {{children}}
    </section>
  );
}}
"""


def _card_tsx(spec, ctx: _Ctx) -> str:
    name = _pascal(spec.id)
    model = ctx.model_for(spec)
    tname = model.__name__ if model else None
    default_state = json.dumps(spec.states[0] if spec.states else "idle")
    title = spec.props.get("title", spec.id)
    id_field = _first_field(model, ("id", "run_id", "name", "task_id")) if model else None
    latest = (f'      <p>latest: {{records.length ? String(records[0].{id_field}) : "—"}}</p>\n'
              if id_field else "")
    count = "      <p>{records.length} record(s)</p>\n" if tname else ""
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
{_component_header(name, tname, False, False, spec.states)}
export function {name}({{ {"records = [], " if tname else ""}state = {default_state}, children }}: {name}Props) {{
  return (
    <section role="group" aria-label="{spec.id}" data-state={{state}} tabIndex={{0}}
      style={{{_BOX_STYLE}}}>
      <h3>{title}</h3>
{count}{latest}      {{children}}
    </section>
  );
}}
"""


def _timeline_tsx(spec, ctx: _Ctx) -> str:
    name = _pascal(spec.id)
    model = ctx.model_for(spec)
    if model is None or "spans" not in model.model_fields:
        raise ValueError(f"component {spec.id!r} (type timeline) must bind a contract "
                         f"with a `spans` field (e.g. run-trace)")
    default_state = json.dumps(spec.states[0] if spec.states else "idle")
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
{_component_header(name, model.__name__, False, False, spec.states)}
export function {name}({{ records = [], state = {default_state}, children }}: {name}Props) {{
  const max = Math.max(1, ...records.flatMap((r) => (r.spans ?? []).map((s) => s.end_ms)));
  return (
    <section role="region" aria-label="{spec.id}" data-state={{state}} tabIndex={{0}}
      style={{{_BOX_STYLE}}}>
      {{records.map((r, i) => (
        <div key={{i}} aria-label={{r.run_id}}>
          <h4>{{r.run_id}}</h4>
          {{(r.spans ?? []).map((s, j) => (
            <div key={{j}} title={{`${{s.name}} (${{s.start_ms}}–${{s.end_ms}}ms)`}}
              style={{{{
                marginLeft: `${{(s.start_ms / max) * 100}}%`,
                width: `${{Math.max(1, ((s.end_ms - s.start_ms) / max) * 100)}}%`,
                background: "var(--utag-color-accent)",
                color: "var(--utag-color-bg)",
                borderRadius: "var(--utag-radius-sm)",
                marginBottom: "var(--utag-space-1)",
                paddingLeft: "var(--utag-space-1)",
              }}}}>
              {{s.name}}
            </div>
          ))}}
        </div>
      ))}}
      {{children}}
    </section>
  );
}}
"""


def _chart_tsx(spec, ctx: _Ctx) -> str:
    name = _pascal(spec.id)
    model = ctx.model_for(spec)
    if model is None or "value" not in model.model_fields or "name" not in model.model_fields:
        raise ValueError(f"component {spec.id!r} (type chart) must bind a contract "
                         f"with `name` and `value` fields (e.g. metric-point)")
    default_state = json.dumps(spec.states[0] if spec.states else "idle")
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
{_component_header(name, model.__name__, False, False, spec.states)}
export function {name}({{ records = [], state = {default_state}, children }}: {name}Props) {{
  const max = Math.max(1, ...records.map((r) => r.value));
  return (
    <section role="region" aria-label="{spec.id}" data-state={{state}} tabIndex={{0}}
      style={{{_BOX_STYLE}}}>
      {{records.map((r, i) => (
        <div key={{i}}>
          <span>{{r.name}}: {{r.value}}</span>
          <div role="img" aria-label={{`${{r.name}} ${{r.value}}`}}
            style={{{{
              width: `${{(r.value / max) * 100}}%`,
              background: "var(--utag-color-accent)",
              height: "var(--utag-space-2)",
              borderRadius: "var(--utag-radius-sm)",
            }}}} />
        </div>
      ))}}
      {{children}}
    </section>
  );
}}
"""


def _board_tsx(spec, ctx: _Ctx) -> str:
    name = _pascal(spec.id)
    model = ctx.model_for(spec)
    grouped = _enum_field(model, ("status", "mode")) if model else None
    if model is None or grouped is None:
        raise ValueError(f"component {spec.id!r} (type board) must bind a contract "
                         f"with an enum `status` or `mode` field")
    group_field, values = grouped
    id_field = _first_field(model, ("id", "task_id", "job_id", "run_id", "name")) or group_field
    default_state = json.dumps(spec.states[0] if spec.states else "idle")
    columns = "\n".join(
        f'''        <section key="{v}" aria-label="{v}">
          <h4>{v}</h4>
          {{records.filter((r) => r.{group_field} === "{v}").map((r, i) => (
            <div key={{i}} tabIndex={{0}} style={{{_BOX_STYLE}}}>{{String(r.{id_field})}}</div>
          ))}}
        </section>''' for v in values)
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
{_component_header(name, model.__name__, False, False, spec.states)}
export function {name}({{ records = [], state = {default_state}, children }}: {name}Props) {{
  return (
    <section role="region" aria-label="{spec.id}" data-state={{state}} tabIndex={{0}}
      style={{{{ display: "grid", gridAutoFlow: "column", gap: "var(--utag-space-2)" }}}}>
{columns}
      {{children}}
    </section>
  );
}}
"""


def _graph_tsx(spec, ctx: _Ctx) -> str:
    name = _pascal(spec.id)
    model = ctx.model_for(spec)
    id_field = _first_field(model, ("id", "task_id", "name", "run_id")) if model else None
    if model is None or id_field is None:
        raise ValueError(f"component {spec.id!r} (type graph) must bind a contract "
                         f"with an id-like field")
    default_state = json.dumps(spec.states[0] if spec.states else "idle")
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
{_component_header(name, model.__name__, False, False, spec.states)}
export function {name}({{ records = [], state = {default_state}, children }}: {name}Props) {{
  return (
    <nav aria-label="{spec.id}" data-state={{state}}>
      <ol style={{{{ display: "flex", listStyle: "none", gap: "var(--utag-space-2)" }}}}>
        {{records.map((r, i) => (
          <li key={{i}} tabIndex={{0}} style={{{_BOX_STYLE}}}>
            {{i > 0 ? <span aria-hidden="true">→ </span> : null}}
            {{String(r.{id_field})}}
          </li>
        ))}}
      </ol>
      {{children}}
    </nav>
  );
}}
"""


def _nav_tsx(spec, ctx: _Ctx) -> str:
    name = _pascal(spec.id)
    links = "\n".join(
        f'        <li><NavLink to="{r.path}">{r.path.strip("/") or "overview"}</NavLink></li>'
        for r in ctx.design.routes)
    return f"""// generated from design.yaml component `{spec.id}` — do not edit by hand
import React from "react";
import {{ NavLink }} from "react-router-dom";

export function {name}() {{
  return (
    <nav aria-label="{spec.id}">
      <ul style={{{{ listStyle: "none", padding: "var(--utag-space-2)" }}}}>
{links}
      </ul>
    </nav>
  );
}}
"""


_RENDERERS = {
    "table": _table_tsx,
    "matrix": lambda spec, ctx: _table_tsx(spec, ctx, dense=True),
    "panel": _panel_tsx,
    "card": _card_tsx,
    "timeline": _timeline_tsx,
    "chart": _chart_tsx,
    "board": _board_tsx,
    "graph": _graph_tsx,
    "nav": _nav_tsx,
}

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


def route_page_name(path: str) -> str:
    return _pascal(path.strip("/").replace("/", "-") or "home") + "Page"


def _route_tsx(route, ctx: _Ctx) -> str:
    design = ctx.design
    name = route_page_name(route.path)
    layout = next(l for l in design.layouts if l.id == route.layout)
    layout_name = _pascal(route.layout)
    specs = {c.id: c for c in design.components}
    nav_spec = next((c for c in design.components if c.type == "nav"), None)

    imports = [f'import {{ {layout_name} }} from "../layouts/{layout_name}";',
               'import { SelectionProvider } from "../hooks/useInteractions";']
    resources: dict[str, str] = {}
    main_parts, inspector_parts = [], []
    for cid in route.components:
        spec = specs.get(cid)
        if spec is None:
            raise ValueError(f"route {route.path!r} references unknown component {cid!r}")
        cname = _pascal(cid)
        imports.append(f'import {{ {cname} }} from "../components/{cname}";')
        resource = spec.props.get("resource")
        element = f"<{cname} />"
        if resource:
            ident = _ident(resource)
            resources[ident] = f'import {{ {ident} }} from "../fixtures/{ident}";'
            element = f"<{cname} records={{{ident}}} />"
        if ctx.targets.get(cid) and "inspector" in layout.regions:
            inspector_parts.append(element)
        else:
            main_parts.append(element)
    if nav_spec and "sidebar" in layout.regions:
        nav_name = _pascal(nav_spec.id)
        imports.append(f'import {{ {nav_name} }} from "../components/{nav_name}";')

    imports += sorted(resources.values())
    region_props = [f'header={{<strong>{design.brand.name}</strong>}}'] \
        if "header" in layout.regions else []
    if nav_spec and "sidebar" in layout.regions:
        region_props.append(f"sidebar={{<{_pascal(nav_spec.id)} />}}")
    main = "\n            ".join(main_parts)
    region_props.append(f"main={{\n          <>\n            {main}\n          </>\n        }}")
    if inspector_parts:
        inspector = "\n            ".join(inspector_parts)
        region_props.append(f"inspector={{\n          <>\n            {inspector}\n          </>\n        }}")
    joined_props = "\n        ".join(region_props)
    return f"""// generated from design.yaml route `{route.path}` — do not edit by hand
import React from "react";
{chr(10).join(imports)}

export function {name}() {{
  return (
    <SelectionProvider>
      <{layout_name}
        {joined_props}
      />
    </SelectionProvider>
  );
}}
"""


def _routes_index_tsx(design: DesignYaml) -> str:
    imports = "\n".join(
        f'import {{ {route_page_name(r.path)} }} from "./{route_page_name(r.path)}";'
        for r in design.routes)
    entries = "\n".join(
        f'  {{ path: "{r.path}", element: <{route_page_name(r.path)} /> }},'
        for r in design.routes)
    return f"""// generated route table from design.yaml — do not edit by hand
import React from "react";
{imports}

export const routes = [
{entries}
];
"""


@register_generator("react-component-library", manifest=_manifest(
    "react-component-library",
    ["generated/components/*.tsx", "generated/layouts/*.tsx",
     "generated/routes/*.tsx", "generated/hooks/useInteractions.tsx"],
    output_schema=None))
class ReactComponentLibraryGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        design = _design(module)
        ctx = _Ctx(design)
        out: dict[str, str] = {"generated/hooks/useInteractions.tsx": _SELECT_HELPERS,
                               "generated/routes/index.tsx": _routes_index_tsx(design)}
        for spec in design.components:
            renderer = _RENDERERS.get(spec.type)
            if renderer is None:
                raise ValueError(f"component {spec.id!r}: unknown type {spec.type!r}; "
                                 f"known: {sorted(_RENDERERS)}")
            out[f"generated/components/{_pascal(spec.id)}.tsx"] = renderer(spec, ctx)
        for layout in design.layouts:
            out[f"generated/layouts/{_pascal(layout.id)}.tsx"] = _layout_tsx(layout)
        for route in design.routes:
            out[f"generated/routes/{route_page_name(route.path)}.tsx"] = _route_tsx(route, ctx)
        return out
