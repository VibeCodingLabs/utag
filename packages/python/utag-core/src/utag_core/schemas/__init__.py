"""Strict schema contract layer (v2.14.0 Phase 1).

Every generated artifact, UI, automation, run record, and AI call validates
against one of these models. Rules: unknown properties rejected everywhere;
vendor/private data goes under the explicit `extensions` field; JSON Schema
emission is deterministic (sorted keys) with a `$id` per schema.
"""
from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict

SCHEMA_ID_BASE = "https://utag.dev/schemas"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

SLUG = r"^[a-z0-9][a-z0-9._/-]*$"
SHA256 = r"^[a-f0-9]{64}$"


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    extensions: dict[str, Any] | None = None


def kind_of(model: type[BaseModel]) -> str:
    """Class name -> kebab kind: MCPToolContract -> mcp-tool-contract."""
    name = model.__name__
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    return name.lower()


def emit_json_schema(model: type[BaseModel]) -> str:
    """Deterministic JSON Schema 2020-12 text for one model."""
    schema = model.model_json_schema()
    schema["$schema"] = JSON_SCHEMA_DIALECT
    schema["$id"] = f"{SCHEMA_ID_BASE}/{kind_of(model)}.schema.json"
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


from utag_core.schemas import ai, autoresearch, core, design, factory, mcp, observability, openapi  # noqa: E402
from utag_core.schemas.ai import *  # noqa: F403,E402
from utag_core.schemas.autoresearch import *  # noqa: F403,E402
from utag_core.schemas.core import *  # noqa: F403,E402
from utag_core.schemas.design import *  # noqa: F403,E402
from utag_core.schemas.factory import *  # noqa: F403,E402
from utag_core.schemas.mcp import *  # noqa: F403,E402
from utag_core.schemas.observability import *  # noqa: F403,E402
from utag_core.schemas.openapi import *  # noqa: F403,E402

_MODULES = (core, autoresearch, design, observability, ai, mcp, openapi, factory)

#: kind -> top-level schema model (only models listed in a module's TOP_LEVEL)
SCHEMAS: dict[str, type[StrictSchema]] = {
    kind_of(m): m for mod in _MODULES for m in mod.TOP_LEVEL
}

#: kind -> one valid example payload (fixture + doc source)
EXAMPLES: dict[str, dict[str, Any]] = {
    kind_of(m): mod.EXAMPLES[m.__name__] for mod in _MODULES for m in mod.TOP_LEVEL
}


def get_schema(kind: str) -> type[StrictSchema]:
    try:
        return SCHEMAS[kind]
    except KeyError:
        raise KeyError(f"unknown schema kind {kind!r}; known: {sorted(SCHEMAS)}") from None
