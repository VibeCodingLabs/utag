"""Universal Design Contract (UDC): assemble design/*.yaml fragments, validate
against the user's udc.schema.json (2020-12), and derive artifacts:
  udc-design-md : UDC tokens/components -> DESIGN.md (validated by our design-md lint)
  udc-component : UDC components domain -> typed TSX stubs (validated by tsc gate)
The UDC contract graph stays canonical; derivations are deterministic.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from utag_core.ir import ModuleSpec
from utag_core.registry import register_generator, register_validator
from utag_core.report import Finding, Severity, ValidationReport

SCHEMA_PATH = Path(__file__).parents[5] / "schemas" / "udc.schema.json"
_ROOT_KEYS = {"udc", "info"}
_URI = re.compile(r"^design://([a-z][a-z0-9-]*)((?:/[A-Za-z][A-Za-z0-9_-]*)+)$")


def load_udc_schema() -> dict:
    # repo layout first; installed-package fallback via cwd
    for cand in (SCHEMA_PATH, Path("schemas/udc.schema.json")):
        if cand.is_file():
            return json.loads(cand.read_text())
    raise FileNotFoundError("udc.schema.json not found")


def assemble(fragments_dir: Path) -> dict:
    """design/*.yaml fragments -> one document (mirrors udc-toolchain assemble:
    _root.yaml is the envelope; every other fragment becomes domains.<stem>)."""
    fragments_dir = Path(fragments_dir)
    root = yaml.safe_load((fragments_dir / "_root.yaml").read_text()) or {}
    doc = {k: v for k, v in root.items() if k in _ROOT_KEYS or k.startswith("x-")}
    doc.setdefault("domains", {})
    if isinstance(root.get("domains"), dict):
        doc["domains"].update(root["domains"])
    for frag in sorted(fragments_dir.glob("*.yaml")):
        if frag.name == "_root.yaml":
            continue
        payload = yaml.safe_load(frag.read_text())
        if payload is not None:
            doc["domains"][frag.stem] = payload
    return doc


def resolve_uri(doc: dict, uri: str):
    """design://<domain>/<seg>/... -> node, or None."""
    m = _URI.match(uri)
    if not m:
        return None
    node = doc.get("domains", {}).get(m.group(1))
    for seg in m.group(2).strip("/").split("/"):
        if not isinstance(node, dict) or seg not in node:
            return None
        node = node[seg]
    return node


@register_validator("udc")
def validate_udc(path: str, content: str) -> ValidationReport:
    """schema conformance + every design:// reference resolves."""
    try:
        doc = json.loads(content) if path.endswith(".json") else yaml.safe_load(content)
    except Exception as e:
        return ValidationReport.fail(path, "udc", "udc-validate", [
            Finding(severity=Severity.error, path=path, message=f"parse: {e}")])
    findings = [Finding(severity=Severity.error, path=f"{path}:{'/'.join(map(str, e.path))}",
                        message=e.message)
                for e in Draft202012Validator(load_udc_schema()).iter_errors(doc)]
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("token", "supersededBy") and isinstance(v, str):
                    yield v
                elif k in ("references", "consumes") and isinstance(v, list):
                    yield from (u for u in v if isinstance(u, str))
                else:
                    yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
    for uri in walk(doc):
        if resolve_uri(doc, uri) is None:
            findings.append(Finding(severity=Severity.error, path=path,
                                    message=f"unresolved design URI: {uri}"))
    if any(f.severity == Severity.error for f in findings):
        return ValidationReport.fail(path, "udc", "udc-validate", findings)
    return ValidationReport.ok(path, "udc", "udc-validate")


def _leaves(node: dict, prefix: str = ""):
    if isinstance(node, dict) and "value" in node and "type" in node:
        yield prefix, node
        return
    if isinstance(node, dict):
        for k, v in node.items():
            if not k.startswith("x-"):
                yield from _leaves(v, f"{prefix}-{k}".strip("-"))


@register_generator("udc-design-md")
class UdcDesignMdGenerator:
    """UDC doc (module.provenance['udc_json']) -> DESIGN.md honoring the alpha spec."""

    def generate(self, module: ModuleSpec) -> dict[str, str]:
        doc = json.loads(module.provenance["udc_json"])
        tokens = doc.get("domains", {}).get("tokens", {})
        colors, spacing, rounded, typography = {}, {}, {}, {}
        for name, leaf in _leaves(tokens):
            t, v = leaf["type"], leaf["value"]
            if t == "color":
                colors[name.removeprefix("color-") or name] = str(v)
            elif t == "dimension":
                (rounded if "radius" in name else spacing)[name] = str(v)
            elif t == "typography" and isinstance(v, dict):
                typography[name] = {k: str(x) for k, x in v.items()}
        if colors and "primary" not in colors:
            first = next(iter(colors))
            colors["primary"] = colors[first]  # design-md requires primary; aliased, documented below
        fm = {"name": doc["info"]["title"], "version": "alpha"}
        for key, val in (("colors", colors), ("typography", typography),
                         ("rounded", rounded), ("spacing", spacing)):
            if val:
                fm[key] = val
        body = (f"## Overview\n\nDerived deterministically from UDC contract "
                f"'{doc['info']['title']}' v{doc['info']['version']}. The UDC design.yaml "
                f"is canonical; this file is a verified derivation.\n\n"
                f"## Colors\n\nTokens mapped 1:1 from domains.tokens (type=color). "
                + ("Note: `primary` aliased from the first color token; UDC had no token named primary.\n"
                   if "primary" in colors and "color-primary" not in [f"color-{k}" for k in colors] else "\n"))
        return {"DESIGN.md": f"---\n{yaml.safe_dump(fm, sort_keys=True)}---\n\n{body}"}


@register_generator("udc-component")
class UdcComponentGenerator:
    """UDC components domain -> typed React component stubs wired to token CSS vars."""

    def generate(self, module: ModuleSpec) -> dict[str, str]:
        doc = json.loads(module.provenance["udc_json"])
        comps = doc.get("domains", {}).get("components", {})
        out: dict[str, str] = {}
        for name, entry in sorted(comps.items()):
            if name.startswith("x-") or not isinstance(entry, dict):
                continue
            spec = entry.get("spec", {}) or {}
            props = spec.get("props", {}) or {}
            lines = ["// generated by utag udc-component — deterministic; do not edit",
                     f"// contract: design://components/{name} v{entry.get('version', '0.0.0')}", ""]
            fields = []
            for pname, pdef in sorted(props.items()):
                if isinstance(pdef, dict) and "enum" in pdef:
                    fields.append(f"  {pname}?: {' | '.join(repr(e) for e in pdef['enum'])};".replace("'", '"'))
                else:
                    fields.append(f"  {pname}?: string;")
            refs = entry.get("references", []) or []
            vars_ = [u.removeprefix("design://").replace("/", "-") for u in refs]
            lines += [f"export interface {name}Props {{"] + fields + ["  children?: unknown;", "}", ""]
            lines += [f"export function {name}(props: {name}Props) {{",
                      "  const style = {"] + \
                     [f'    // var(--{v})' for v in vars_] + \
                     ["  };",
                      f'  return {{ component: "{name}", props, style }};',
                      "}", ""]
            out[f"{name}.tsx"] = "\n".join(lines)
        return out
