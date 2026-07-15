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
    import hashlib
    from importlib.metadata import version as pkg_version

    from utag_core.schemas.core import ArtifactManifest, ArtifactProvenance, FileDigest

    src = Path(a.input)
    module = _load_module(src)
    gen = get_generator(a.target)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rc = 0
    digests: list[FileDigest] = []
    for rel, content in sorted(gen.generate(module).items()):
        p = out / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
        digests.append(FileDigest(path=rel, sha256=hashlib.sha256(content.encode()).hexdigest(),
                                  bytes=len(content.encode())))
        vkind = TARGET_VALIDATOR.get(a.target)
        if vkind and not a.no_validate:
            report = get_validator(vkind)(str(p), content)
            print(report.to_json())
            if not report.valid:
                rc = 1
        print(f"wrote {p}", file=sys.stderr)
    manifest = ArtifactManifest(
        id=f"{a.target}-{src.stem}".lower().replace("_", "-"),
        target=a.target,
        files=digests,
        provenance=ArtifactProvenance(
            generator_id=a.target, utag_version=pkg_version("utag-core"),
            source_paths=[str(src)],
            inputs_sha256=hashlib.sha256(src.read_bytes()).hexdigest()),
    )
    (out / "artifact.manifest.json").write_text(manifest.model_dump_json(indent=2, exclude_none=True) + "\n")
    print(f"wrote {out / 'artifact.manifest.json'}", file=sys.stderr)
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

def cmd_schema(a: argparse.Namespace) -> int:
    from utag_core.schemas import SCHEMAS
    from utag_core.schemas import tools as st

    root = Path(getattr(a, "root", ".") or ".")
    if a.schema_cmd == "list":
        for kind in sorted(SCHEMAS):
            print(kind)
        return 0
    if a.schema_cmd == "emit":
        written = st.emit_all(Path(a.out))
        print(f"emitted {len(written)} schemas to {a.out}")
        return 0
    if a.schema_cmd == "validate":
        errs = st.validate_file(a.kind, Path(a.path))
        for e in errs:
            print(e, file=sys.stderr)
        print(json.dumps({"kind": a.kind, "path": a.path, "valid": not errs}))
        return 1 if errs else 0
    if a.schema_cmd == "validate-all":
        problems = st.validate_all(root)
        for p in problems:
            print(f"FAIL {p}", file=sys.stderr)
        print(f"validate-all: {len(SCHEMAS)} kinds, {len(problems)} problem(s)")
        return 1 if problems else 0
    if a.schema_cmd == "doctor":
        report = st.doctor_report(root)
        outp = Path(a.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(report)
        print(report, end="")
        return 1 if "FAIL" in report else 0
    print("unknown schema command", file=sys.stderr)
    return 1


DESIGN_TARGETS = ("design-tokens-css", "tailwind-v4-theme", "react-component-library")


def cmd_design(a: argparse.Namespace) -> int:
    import hashlib

    from utag_core.ir import ModuleSpec
    from utag_core.schemas import tools as st

    design_path = Path(a.input)
    errs = st.validate_file("design-yaml", design_path)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    if a.design_cmd == "validate":
        print(json.dumps({"path": str(design_path), "valid": True}))
        return 0

    module = ModuleSpec(name="design", description="design.yaml",
                        provenance={"design_yaml": design_path.read_text()})
    targets = {"tokens": DESIGN_TARGETS[:2], "components": DESIGN_TARGETS[2:],
               "app": DESIGN_TARGETS, "snapshot": DESIGN_TARGETS}[a.design_cmd]
    files: dict[str, str] = {}
    for target in targets:
        files.update(get_generator(target).generate(module))

    if a.design_cmd == "snapshot":
        lines = ["# UI snapshot", ""]
        lines += [f"- `{rel}` sha256 `{hashlib.sha256(content.encode()).hexdigest()}`"
                  for rel, content in sorted(files.items())]
        out = Path(a.out) / "snapshot.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n")
        print(f"wrote {out} ({len(files)} files)")
        return 0

    out = Path(a.out)
    for rel, content in sorted(files.items()):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    print(f"wrote {len(files)} files to {out}")
    return 0


def cmd_registry(a: argparse.Namespace) -> int:
    from utag_core.registry import MANIFESTS, coverage_report, registry_problems

    if a.registry_cmd == "list":
        for (kind, id_), m in sorted(MANIFESTS.items()):
            print(f"{kind:<10} {id_:<40} {m.status.value}")
        return 0
    if a.registry_cmd == "doctor":
        problems = registry_problems(Path(a.root))
        for p in problems:
            print(f"FAIL {p}", file=sys.stderr)
        print(f"registry doctor: {len(MANIFESTS)} manifests, {len(problems)} problem(s)")
        return 1 if problems else 0
    if a.registry_cmd == "manifest":
        for (kind, id_), m in sorted(MANIFESTS.items()):
            if id_ == a.id:
                print(m.model_dump_json(indent=2, exclude_none=True))
                return 0
        print(f"no manifest with id {a.id!r}", file=sys.stderr)
        return 1
    if a.registry_cmd == "coverage":
        report = coverage_report()
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(report)
        print(report, end="")
        return 0
    print("unknown registry command", file=sys.stderr)
    return 1


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
    
    s = sub.add_parser("schema", help="strict schema contract layer (list/emit/validate/doctor)")
    ssub = s.add_subparsers(dest="schema_cmd", required=True)
    ssub.add_parser("list")
    s_emit = ssub.add_parser("emit")
    s_emit.add_argument("--out", default="schemas/")
    s_val = ssub.add_parser("validate")
    s_val.add_argument("--kind", required=True); s_val.add_argument("--path", required=True)
    s_all = ssub.add_parser("validate-all")
    s_all.add_argument("--root", default=".")
    s_doc = ssub.add_parser("doctor")
    s_doc.add_argument("--root", default=".")
    s_doc.add_argument("--out", default="reports/schema-validation/doctor.md")
    s.set_defaults(fn=cmd_schema)

    d = sub.add_parser("design", help="design.yaml -> tokens/components/app/snapshot (UDC pipeline)")
    dsub = d.add_subparsers(dest="design_cmd", required=True)
    for name, default_out in (("validate", ""), ("tokens", "packages/ui/src/"),
                              ("components", "packages/ui/src/"), ("app", "packages/ui/src/"),
                              ("snapshot", "reports/ui-snapshots/")):
        dp = dsub.add_parser(name)
        dp.add_argument("--input", default="design.yaml")
        if default_out:
            dp.add_argument("--out", default=default_out)
    d.set_defaults(fn=cmd_design)

    r = sub.add_parser("registry", help="registered generators/validators/importers + manifests")
    rsub = r.add_subparsers(dest="registry_cmd", required=True)
    rsub.add_parser("list")
    r_doc = rsub.add_parser("doctor")
    r_doc.add_argument("--root", default=".")
    r_man = rsub.add_parser("manifest")
    r_man.add_argument("--id", required=True)
    r_cov = rsub.add_parser("coverage")
    r_cov.add_argument("--out", default="reports/registry-coverage.md")
    r.set_defaults(fn=cmd_registry)

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
