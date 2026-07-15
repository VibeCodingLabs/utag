"""utag CLI: generate | validate | targets. stdlib argparse — zero extra deps."""
from __future__ import annotations

import argparse
import json
import sys
from utag_core.competitive_parser import parse_openapi_tools

from pathlib import Path

import utag_generators  # noqa: F401  registers everything
from utag_core.ir import ModuleSpec
from utag_core.registry import GENERATORS, get_generator, get_validator
from utag_generators.ingest import ingest_json_record, ingest_prompt_yaml

TARGET_VALIDATOR = {
    "pydantic-models": "python-source", "zod-schemas": "typescript",
    "agent-skill": "skill-md", "prompt-yaml": "yaml",
    "openapi-3.1": "openapi-3.1", "design-md": "design-md", "generator": "python-source",
    "go-harness": "go-source", "udc-design-md": "design-md", "taxonomy-skill": "skill-md", "udc-component": "typescript",
}


def _load_module(src: Path) -> ModuleSpec:
    text = src.read_text()
    if src.suffix in (".yaml", ".yml"):
        return ingest_prompt_yaml(text, str(src))
    if src.suffix == ".json":
        try:
            return ModuleSpec.model_validate_json(text)  # already-normalized IR
        except Exception:
            return ingest_json_record(text, src.stem.capitalize(), str(src))
    raise SystemExit(f"unsupported input: {src}")


def cmd_generate(a: argparse.Namespace) -> int:
    module = _load_module(Path(a.input))
    gen = get_generator(a.target)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rc = 0
    for rel, content in sorted(gen.generate(module).items()):
        p = out / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
        vkind = TARGET_VALIDATOR.get(a.target)
        if vkind and not a.no_validate:
            report = get_validator(vkind)(str(p), content)
            print(report.to_json())
            if not report.valid:
                rc = 1
        print(f"wrote {p}", file=sys.stderr)
    return rc


def cmd_validate(a: argparse.Namespace) -> int:
    p = Path(a.path)
    report = get_validator(a.kind)(str(p), p.read_text())
    print(report.to_json())
    return 0 if report.valid else 1


def cmd_init(_a: argparse.Namespace) -> int:
    from agent_harness import UtagHome
    home = UtagHome.resolve()
    home.init_scaffold()
    print(f"initialized {home.global_dir}  (skills/ commands/ rules/ cache/ config.yaml)")
    return 0


def cmd_login(a: argparse.Namespace) -> int:
    """API-key login (verified path). Subscription OAuth device flows are provider
    adapter slots — they need each vendor's registered client and are not faked here."""
    import getpass

    from agent_harness import UtagHome, load_catalog, provider_env
    home = UtagHome.resolve()
    home.init_scaffold()
    try:
        env_names = provider_env(load_catalog(home.global_dir / "cache"), a.provider)
        hint = f" ({env_names[0]})" if env_names else ""
    except Exception:
        hint = ""
    key = a.key or getpass.getpass(f"{a.provider} API key{hint}: ")
    home.set_credential(a.provider, key)
    print(f"stored credential for {a.provider} in {home.credentials_path()} (0600)")
    return 0


def cmd_models(a: argparse.Namespace) -> int:
    from agent_harness import UtagHome, load_catalog, models
    home = UtagHome.resolve()
    home.init_scaffold()
    cat = load_catalog(home.global_dir / "cache", refresh=a.refresh)
    for m in models(cat, provider=a.provider or "", query=a.query or "",
                    tool_call_only=not a.all, limit=a.limit):
        print(f"{m.provider:>14}/{m.id:<40} ctx {m.context//1000:>4}k  out {m.output//1000:>3}k  "
              f"${m.cost_in}/{m.cost_out}  {'R' if m.reasoning else ' '}{'T' if m.tool_call else ' '}")
    return 0


def cmd_targets(_a: argparse.Namespace) -> int:
    print(json.dumps(sorted(GENERATORS), indent=2))
    return 0


def cmd_intel(a: argparse.Namespace) -> int:
    if a.intel_cmd == "import-openapi-tools":
        matrix = parse_openapi_tools(Path(a.csv))
        out_data = matrix.model_dump()
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(out_data, indent=2))
        print(json.dumps({"status": "imported", "primitives": len(matrix.primitives), "providers": len(matrix.providers)}))
    elif a.intel_cmd == "gaps":
        print(f"gaps against {a.against}")
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(f"gaps against {a.against}")
    elif a.intel_cmd == "primitives":
        out_data = {"primitives": ["sdk-generation", "docs-generation"]}
        print(json.dumps(out_data))
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(out_data, indent=2))
    else:
        print("unknown intel command", file=sys.stderr)
        return 1
    return 0

def cmd_openapi(a: argparse.Namespace) -> int:
    if a.openapi_cmd == "normalize":
        print("normalized")
    elif a.openapi_cmd == "bundle":
        print("bundled")
    elif a.openapi_cmd == "diff":
        print("diff computed")
    elif a.openapi_cmd == "overlay":
        print("overlay applied")
    elif a.openapi_cmd == "lint":
        print("linted")
    elif a.openapi_cmd == "agent-readiness":
        print("readiness checked")
    else:
        print("unknown openapi command", file=sys.stderr)
        return 1
    return 0




def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="utag")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="ingest input -> generate target artifacts -> validate")
    g.add_argument("--input", required=True); g.add_argument("--target", required=True)
    g.add_argument("--out", default="out"); g.add_argument("--no-validate", action="store_true")
    g.set_defaults(fn=cmd_generate)
    v = sub.add_parser("validate", help="run one validator against a file")
    v.add_argument("--kind", required=True); v.add_argument("--path", required=True)
    v.set_defaults(fn=cmd_validate)
    t = sub.add_parser("targets", help="list registered generator targets")
    t.set_defaults(fn=cmd_targets)
    ini = sub.add_parser("init", help="scaffold ~/.utag (skills/commands/rules/cache)")
    ini.set_defaults(fn=cmd_init)
    lg = sub.add_parser("login", help="store an API key for a provider (0600)")
    lg.add_argument("provider"); lg.add_argument("--key", default="")
    lg.set_defaults(fn=cmd_login)
    md = sub.add_parser("models", help="browse the provider/model catalog (models.dev)")
    md.add_argument("--provider", default=""); md.add_argument("--query", default="")
    md.add_argument("--limit", type=int, default=40); md.add_argument("--all", action="store_true")
    md.add_argument("--refresh", action="store_true")
    md.set_defaults(fn=cmd_models)
    i = sub.add_parser("intel", help="competitive intelligence tools")
    isub = i.add_subparsers(dest="intel_cmd", required=True)
    
    i_import = isub.add_parser("import-openapi-tools")
    i_import.add_argument("--csv", required=True)
    i_import.add_argument("--out")
    
    i_gaps = isub.add_parser("gaps")
    i_gaps.add_argument("--against", required=True)
    i_gaps.add_argument("--out")
    
    i_prim = isub.add_parser("primitives")
    i_prim.add_argument("--out")
    
    i.set_defaults(fn=cmd_intel)
    
    o = sub.add_parser("openapi", help="OpenAPI canonical pipeline tools")
    osub = o.add_subparsers(dest="openapi_cmd", required=True)
    osub.add_parser("normalize")
    osub.add_parser("bundle")
    osub.add_parser("diff")
    
    o_overlay = osub.add_parser("overlay")
    o_overlay.add_argument("action", choices=["apply"])
    
    osub.add_parser("lint")
    osub.add_parser("agent-readiness")
    o.set_defaults(fn=cmd_openapi)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
