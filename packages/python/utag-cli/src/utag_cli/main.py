"""utag CLI: generate | validate | targets. stdlib argparse — zero extra deps."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import utag_generators  # noqa: F401  registers everything
from utag_core.ir import ModuleSpec
from utag_core.registry import GENERATORS, get_generator, get_validator
from utag_generators.ingest import ingest_json_record, ingest_prompt_yaml

TARGET_VALIDATOR = {
    "pydantic-models": "python-source", "zod-schemas": "typescript",
    "agent-skill": "skill-md", "prompt-yaml": "yaml",
    "openapi-3.1": "openapi-3.1", "design-md": "design-md", "generator": "python-source",
    "go-harness": "go-source",
}


def _load_module(src: Path) -> ModuleSpec:
    text = src.read_text()
    if src.suffix in (".yaml", ".yml"):
        return ingest_prompt_yaml(text, str(src))
    if src.suffix == ".json":
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "types" in parsed:
                return ModuleSpec.model_validate(parsed)
            return ingest_json_record(text, src.stem.capitalize(), str(src))
        except Exception as e:
            raise SystemExit(f"invalid json in {src}: {e}")
    raise SystemExit(f"unsupported input: {src}")


def cmd_generate(a: argparse.Namespace) -> int:
    module = _load_module(Path(a.input))
    gen = get_generator(a.target)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rc = 0
    for rel, content in sorted(gen.generate(module).items()):
        p = out / rel
        if not p.resolve().is_relative_to(out.resolve()):
            raise SystemExit(f"error: path traversal detected for {rel!r}")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
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


def cmd_targets(_a: argparse.Namespace) -> int:
    print(json.dumps(sorted(GENERATORS), indent=2))
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
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
