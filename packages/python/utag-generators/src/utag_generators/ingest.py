"""Ingest: any knowledge -> normalized IR.

Sources v1: prompt YAML (user format), raw JSON records, plain text/markdown (via
a StructuredPort — LLM extracts TypeSpecs), transcript adapter slot (deferred).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol

from utag_core.ir import FieldSpec, ModuleSpec, ScalarKind, TypeSpec
from utag_core.ports import StructuredPort
from utag_generators.targets.prompt_yaml import PromptFile

_ENUM_HINT = {"string": ScalarKind.string, "enum": ScalarKind.string,
              "array": ScalarKind.string, "number": ScalarKind.number,
              "integer": ScalarKind.integer, "boolean": ScalarKind.boolean}


def _prov(kind: str, source: str, text: str) -> dict[str, str]:
    return {"kind": kind, "source": source,
            "sha256": hashlib.sha256(text.encode()).hexdigest()}


def ingest_prompt_yaml(text: str, source: str = "<inline>") -> ModuleSpec:
    pf = PromptFile.parse(text)
    fields = [FieldSpec(name=v.name.lower(), type=_ENUM_HINT.get(v.type, ScalarKind.string),
                        required=v.required, array=(v.type == "array"),
                        default=v.default) for v in pf.variables]
    return ModuleSpec(
        name=pf.name.replace("-", "_"),
        description=f"Normalized from prompt {pf.name!r} v{pf.version}",
        types=[TypeSpec(name=_pascal(pf.name) + "Input", fields=fields)],
        provenance=_prov("prompt-yaml", source, text),
    )


def ingest_json_record(text: str, type_name: str, source: str = "<inline>") -> ModuleSpec:
    """Infer a TypeSpec from a flat JSON example (KB records)."""
    obj: dict[str, Any] = json.loads(text)
    fields = []
    for k, v in obj.items():
        kind = (ScalarKind.integer if isinstance(v, bool) is False and isinstance(v, int)
                else ScalarKind.boolean if isinstance(v, bool)
                else ScalarKind.number if isinstance(v, float)
                else ScalarKind.string)
        fields.append(FieldSpec(name=k, type=kind, array=isinstance(v, list)))
    return ModuleSpec(name=type_name.lower(), types=[TypeSpec(name=type_name, fields=fields)],
                      provenance=_prov("json-record", source, text))


class TranscriptAdapter(Protocol):
    """Deferred: YouTube/audio transcript sources plug in here (YAGNI slot)."""
    def fetch(self, ref: str) -> str: ...


def ingest_freeform(text: str, port: StructuredPort, source: str = "<inline>",
                    max_attempts: int = 3) -> ModuleSpec:
    """NL/markdown/KB/transcript text -> ModuleSpec via any structured backend."""
    module = port.generate(
        prompt=("Extract a normalized data model from the following knowledge. "
                "Emit types with typed, constrained fields.\n\n" + text),
        response_model=ModuleSpec, max_attempts=max_attempts,
        system="You are a schema extraction engine. JSON only.",
    )
    module.provenance.update(_prov("freeform", source, text))
    return module


def _pascal(name: str) -> str:
    return "".join(p.capitalize() for p in name.replace("-", "_").split("_"))
