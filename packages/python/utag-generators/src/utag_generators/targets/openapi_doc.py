"""IR -> minimal valid OpenAPI 3.1 document (CRUD-read shape), validated downstream."""
from __future__ import annotations

import json

from utag_core.ir import ModuleSpec, ScalarKind
from utag_core.registry import register_generator

OAS_TYPES = {
    ScalarKind.string: {"type": "string"}, ScalarKind.integer: {"type": "integer"},
    ScalarKind.number: {"type": "number"}, ScalarKind.boolean: {"type": "boolean"},
    ScalarKind.datetime: {"type": "string", "format": "date-time"},
    ScalarKind.any: {},
}


@register_generator("openapi-3.1")
class OpenAPIGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        schemas, paths = {}, {}
        for t in module.types:
            props, required = {}, []
            for f in t.fields:
                s = dict(OAS_TYPES[f.type]) if isinstance(f.type, ScalarKind) \
                    else {"$ref": f"#/components/schemas/{f.type}"}
                for c in f.constraints:
                    key = {"min_length": "minLength", "max_length": "maxLength",
                           "ge": "minimum", "le": "maximum", "pattern": "pattern",
                           "format": "format"}.get(c.kind)
                    if key:
                        s[key] = c.value
                if f.array:
                    s = {"type": "array", "items": s}
                if f.description:
                    s["description"] = f.description
                props[f.name] = s
                if f.required:
                    required.append(f.name)
            schema = {"type": "object", "additionalProperties": False, "properties": props}
            if required:
                schema["required"] = required
            schemas[t.name] = schema
            slug = t.name.lower()
            paths[f"/{slug}s/{{id}}"] = {"get": {
                "operationId": f"get{t.name}",
                "parameters": [{"name": "id", "in": "path", "required": True,
                                "schema": {"type": "string"}}],
                "responses": {
                    "200": {"description": f"{t.name} found", "content": {"application/json": {
                        "schema": {"$ref": f"#/components/schemas/{t.name}"}}}},
                    "404": {"description": f"{t.name} not found"},
                },
            }}
        doc = {
            "openapi": "3.1.1",
            "info": {"title": module.name, "version": "1.0.0",
                     "description": module.description or module.name},
            "paths": paths,
            "components": {"schemas": schemas},
        }
        return {f"{module.name}.openapi.json": json.dumps(doc, indent=2, sort_keys=True) + "\n"}
