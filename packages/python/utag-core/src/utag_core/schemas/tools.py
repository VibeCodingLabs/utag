"""Schema tooling shared by `utag schema` and scripts/: emit, validate, fixtures, doctor."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pydantic
import yaml

from utag_core.schemas import EXAMPLES, SCHEMAS, emit_json_schema, get_schema

FIXTURES_DIR = "fixtures/schemas"
SCHEMAS_DIR = "schemas"


def load_payload(path: Path) -> Any:
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def emit_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for kind, model in sorted(SCHEMAS.items()):
        p = out_dir / f"{kind}.schema.json"
        p.write_text(emit_json_schema(model))
        written.append(p)
    return written


def validate_file(kind: str, path: Path) -> list[str]:
    """Return error strings; empty means valid."""
    try:
        get_schema(kind).model_validate(load_payload(path))
        return []
    except pydantic.ValidationError as e:
        return [f"{path}: {err['loc']}: {err['msg']}" for err in e.errors()]
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        return [f"{path}: unparseable: {e}"]


def write_fixtures(root: Path) -> list[Path]:
    """One valid + one invalid (unknown top-level property) fixture per schema kind."""
    fdir = root / FIXTURES_DIR
    fdir.mkdir(parents=True, exist_ok=True)
    written = []
    for kind in sorted(SCHEMAS):
        valid = fdir / f"{kind}.valid.json"
        valid.write_text(json.dumps(EXAMPLES[kind], indent=2, sort_keys=True) + "\n")
        invalid_payload = dict(EXAMPLES[kind])
        invalid_payload["__unknown_property__"] = True
        invalid = fdir / f"{kind}.invalid.json"
        invalid.write_text(json.dumps(invalid_payload, indent=2, sort_keys=True) + "\n")
        written += [valid, invalid]
    return written


def validate_all(root: Path) -> list[str]:
    """Validate every schema fixture pair, emitted-schema freshness, and design.yaml."""
    problems: list[str] = []
    fdir = root / FIXTURES_DIR
    for kind, model in sorted(SCHEMAS.items()):
        valid, invalid = fdir / f"{kind}.valid.json", fdir / f"{kind}.invalid.json"
        if not valid.is_file():
            problems.append(f"{kind}: missing valid fixture {valid}")
        elif errs := validate_file(kind, valid):
            problems += [f"{kind}: valid fixture rejected: {e}" for e in errs]
        if not invalid.is_file():
            problems.append(f"{kind}: missing invalid fixture {invalid}")
        elif not validate_file(kind, invalid):
            problems.append(f"{kind}: invalid fixture was accepted — schema not strict")
        emitted = root / SCHEMAS_DIR / f"{kind}.schema.json"
        if not emitted.is_file():
            problems.append(f"{kind}: schema not emitted to {emitted} (run `utag schema emit`)")
        elif emitted.read_text() != emit_json_schema(model):
            problems.append(f"{kind}: emitted schema stale vs models (run `utag schema emit`)")
    design = root / "design.yaml"
    if design.is_file():
        problems += [f"design-yaml: {e}" for e in validate_file("design-yaml", design)]
    else:
        problems.append("design.yaml missing at repo root")
    return problems


def check_no_unknown_extensions() -> list[str]:
    """Every emitted schema must forbid unknown props and offer `extensions`."""
    problems = []
    for kind, model in sorted(SCHEMAS.items()):
        schema = json.loads(emit_json_schema(model))
        if schema.get("additionalProperties") is not False:
            problems.append(f"{kind}: additionalProperties is not false")
        if "extensions" not in schema.get("properties", {}):
            problems.append(f"{kind}: no `extensions` escape hatch")
    return problems


def doctor_report(root: Path) -> str:
    problems = validate_all(root) + check_no_unknown_extensions()
    lines = ["# Schema doctor", "", f"- schemas: {len(SCHEMAS)}",
             f"- problems: {len(problems)}", ""]
    lines += [f"- FAIL: {p}" for p in problems] or ["All schema contracts healthy."]
    return "\n".join(lines) + "\n"
