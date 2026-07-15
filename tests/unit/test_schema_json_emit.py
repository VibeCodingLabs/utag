"""JSON Schema emission: deterministic, 2020-12 dialect, $id, strict, extensions."""
from __future__ import annotations

import json

import pytest

from utag_core.schemas import JSON_SCHEMA_DIALECT, SCHEMAS, emit_json_schema


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_emit_deterministic_and_wellformed(kind):
    model = SCHEMAS[kind]
    text = emit_json_schema(model)
    assert text == emit_json_schema(model)  # byte-identical on re-emit
    schema = json.loads(text)
    assert schema["$schema"] == JSON_SCHEMA_DIALECT
    assert schema["$id"].endswith(f"/{kind}.schema.json")
    assert schema["additionalProperties"] is False
    assert "extensions" in schema["properties"]
    assert schema["type"] == "object"
    assert schema.get("required"), f"{kind} lists no required fields"
