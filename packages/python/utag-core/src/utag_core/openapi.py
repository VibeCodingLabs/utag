from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Any

class OpenAPISource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uri: str
    content: str = ""

class OpenAPIDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    paths: dict[str, Any] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)

class OpenAPIBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document: OpenAPIDocument
    resolved_refs: list[str] = Field(default_factory=list)

class OpenAPIDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    changed: list[str] = Field(default_factory=list)

class OverlayPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: list[dict[str, Any]] = Field(default_factory=list)

class ValidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    message: str
    severity: str

class BreakingChangeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    breaking_changes: list[str] = Field(default_factory=list)

class AgentReadinessReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_ready: bool
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Real pipeline (v2.15.0): normalize / bundle / diff / overlay / lint / readiness
# operating on parsed OpenAPI documents; reports use the strict schema contracts.
# ---------------------------------------------------------------------------

import json  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

from utag_core.schemas.core import Severity, ValidationFinding as ContractFinding  # noqa: E402
from utag_core.schemas.openapi import (  # noqa: E402
    HttpMethod, OpenApiDiffEntry, OpenApiDiffReport, OpenApiOperation,
    OpenApiReadinessReport,
)

_METHODS = [m.value for m in HttpMethod]


def load_spec(path: Path) -> dict:
    text = path.read_text()
    doc = yaml.safe_load(text) if path.suffix in (".yaml", ".yml") else json.loads(text)
    if not isinstance(doc, dict) or "openapi" not in doc:
        raise ValueError(f"{path}: not an OpenAPI document (missing `openapi` key)")
    return doc


def canonical(doc: dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def _resolve_pointer(doc: dict, pointer: str):
    node = doc
    for part in pointer.lstrip("#/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[part]
    return node


def resolve_local_refs(doc: dict) -> dict:
    """Inline internal $refs; cycles keep the $ref in place (never infinite)."""
    def walk(node, seen: frozenset[str]):
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/"):
                if ref in seen:
                    return node  # cycle: leave the reference
                return walk(_resolve_pointer(doc, ref), seen | {ref})
            return {k: walk(v, seen) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, seen) for v in node]
        return node
    return walk(doc, frozenset())


def bundle(doc: dict, base_dir: Path) -> tuple[dict, list[str]]:
    """Inline external-file $refs (`other.yaml#/pointer` or whole-file); local
    `#/...` refs stay untouched. Returns (bundled doc, resolved ref list)."""
    resolved: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and not ref.startswith("#"):
                file_part, _, pointer = ref.partition("#")
                target_path = (base_dir / file_part).resolve()
                # referenced files may be fragments, so no `openapi` key required
                target = yaml.safe_load(target_path.read_text())
                payload = _resolve_pointer(target, pointer) if pointer else target
                resolved.append(ref)
                return walk(payload)
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(doc), sorted(set(resolved))


def operations(doc: dict) -> list[OpenApiOperation]:
    ops = []
    for path, item in sorted((doc.get("paths") or {}).items()):
        if not isinstance(item, dict):
            continue
        for method in _METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            responses = op.get("responses") or {}
            has_response_schema = any(
                isinstance(r, dict) and any(
                    isinstance(c, dict) and "schema" in c
                    for c in (r.get("content") or {}).values())
                for r in responses.values())
            body = op.get("requestBody") or {}
            has_request_schema = any(
                isinstance(c, dict) and "schema" in c
                for c in (body.get("content") or {}).values()) if isinstance(body, dict) else False
            ops.append(OpenApiOperation(
                operation_id=op.get("operationId") or f"{method} {path}",
                method=HttpMethod(method), path=path,
                summary=op.get("summary") or "",
                tags=list(op.get("tags") or []),
                has_request_schema=has_request_schema,
                has_response_schema=has_response_schema))
    return ops


def _op_index(doc: dict) -> dict[str, dict]:
    out = {}
    for path, item in (doc.get("paths") or {}).items():
        if isinstance(item, dict):
            for method in _METHODS:
                if isinstance(item.get(method), dict):
                    out[f"/paths/{path.replace('~', '~0').replace('/', '~1')}/{method}"] = item[method]
    return out


def diff(old: dict, new: dict, old_name: str, new_name: str) -> OpenApiDiffReport:
    entries: list[OpenApiDiffEntry] = []
    old_ops, new_ops = _op_index(old), _op_index(new)
    for pointer in sorted(new_ops.keys() - old_ops.keys()):
        entries.append(OpenApiDiffEntry(kind="added", pointer=pointer, detail="operation added"))
    for pointer in sorted(old_ops.keys() - new_ops.keys()):
        entries.append(OpenApiDiffEntry(kind="removed", pointer=pointer, detail="operation removed"))
    for pointer in sorted(old_ops.keys() & new_ops.keys()):
        if canonical(old_ops[pointer]) != canonical(new_ops[pointer]):
            entries.append(OpenApiDiffEntry(kind="changed", pointer=pointer, detail="operation changed"))
    old_schemas = (old.get("components") or {}).get("schemas") or {}
    new_schemas = (new.get("components") or {}).get("schemas") or {}
    for name in sorted(new_schemas.keys() - old_schemas.keys()):
        entries.append(OpenApiDiffEntry(kind="added", pointer=f"/components/schemas/{name}", detail="schema added"))
    for name in sorted(old_schemas.keys() - new_schemas.keys()):
        entries.append(OpenApiDiffEntry(kind="removed", pointer=f"/components/schemas/{name}", detail="schema removed"))
    for name in sorted(old_schemas.keys() & new_schemas.keys()):
        if canonical(old_schemas[name]) != canonical(new_schemas[name]):
            entries.append(OpenApiDiffEntry(kind="changed", pointer=f"/components/schemas/{name}", detail="schema changed"))
    return OpenApiDiffReport(old=old_name, new=new_name, entries=entries)


_SEGMENT = re.compile(r"\.([A-Za-z_][A-Za-z0-9_-]*)|\[['\"]([^'\"]+)['\"]\]")


def _walk_target(doc: dict, target: str):
    """JSONPath-lite: `$`, `.name`, `['name']`. Returns (parent, key) or raises."""
    if not target.startswith("$"):
        raise ValueError(f"overlay target must start with $: {target!r}")
    keys = [a or b for a, b in _SEGMENT.findall(target[1:])]
    if not keys and target != "$":
        raise ValueError(f"unsupported overlay target: {target!r}")
    parent = doc
    for key in keys[:-1]:
        parent = parent[key]
    return (parent, keys[-1]) if keys else (None, None)


def apply_overlay(doc: dict, overlay: dict) -> dict:
    """OpenAPI Overlay 1.0 subset: actions with `target` + `update`|`remove`."""
    if "overlay" not in overlay or "actions" not in overlay:
        raise ValueError("not an Overlay document (needs `overlay` and `actions`)")
    import copy
    out = copy.deepcopy(doc)

    def merge(dst, patch):
        for k, v in patch.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                merge(dst[k], v)
            else:
                dst[k] = v

    for action in overlay["actions"]:
        target = action.get("target", "$")
        parent, key = _walk_target(out, target)
        if action.get("remove"):
            if parent is None:
                raise ValueError("cannot remove the document root")
            parent.pop(key, None)
        elif "update" in action:
            node = out if parent is None else parent.setdefault(key, {})
            merge(node, action["update"])
        else:
            raise ValueError(f"overlay action needs `update` or `remove`: {action}")
    return out


def lint(doc: dict, spec_name: str) -> list[ContractFinding]:
    findings: list[ContractFinding] = []
    used_refs = set(re.findall(r'"#/components/schemas/([^"]+)"', json.dumps(doc)))
    for path, item in sorted((doc.get("paths") or {}).items()):
        if not isinstance(item, dict):
            continue
        for method in _METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            where = f"{method.upper()} {path}"
            if not op.get("operationId"):
                findings.append(ContractFinding(severity=Severity.error, code="missing-operation-id",
                                                message=f"{where}: no operationId", path=spec_name))
            if not op.get("summary") and not op.get("description"):
                findings.append(ContractFinding(severity=Severity.warn, code="missing-summary",
                                                message=f"{where}: no summary/description", path=spec_name))
            if not op.get("tags"):
                findings.append(ContractFinding(severity=Severity.warn, code="untagged-operation",
                                                message=f"{where}: no tags", path=spec_name))
            responses = op.get("responses") or {}
            if not any(str(code).startswith("2") for code in responses):
                findings.append(ContractFinding(severity=Severity.error, code="no-success-response",
                                                message=f"{where}: no 2xx response", path=spec_name))
    for name in sorted((doc.get("components") or {}).get("schemas") or {}):
        if name not in used_refs:
            findings.append(ContractFinding(severity=Severity.info, code="orphan-schema",
                                            message=f"components.schemas.{name} is never referenced",
                                            path=spec_name))
    return findings


def readiness(doc: dict, spec_name: str) -> OpenApiReadinessReport:
    ops = operations(doc)
    findings: list[str] = []
    if not ops:
        return OpenApiReadinessReport(spec=spec_name, score=0.0, operations=0,
                                      findings=["no operations found"])
    raw_ops = list(_op_index(doc).values())
    with_id = sum(1 for o in raw_ops if o.get("operationId"))
    with_summary = sum(1 for o in ops if o.summary)
    with_schema = sum(1 for o in ops if o.has_response_schema)
    checks = {
        "operationId coverage": with_id / len(ops),
        "summary coverage": with_summary / len(ops),
        "response schema coverage": with_schema / len(ops),
        "security defined": 1.0 if (doc.get("security") or doc.get("components", {}).get("securitySchemes")) else 0.0,
        "servers declared": 1.0 if doc.get("servers") else 0.0,
    }
    for name, value in checks.items():
        if value < 1.0:
            findings.append(f"{name}: {value:.0%}")
    score = round(sum(checks.values()) / len(checks), 4)
    return OpenApiReadinessReport(spec=spec_name, score=score, operations=len(ops),
                                  findings=findings)
