from __future__ import annotations
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind
from utag_core.registry import register_importer
import json

def _parse_openapi_doc(doc: dict, name: str, source: str) -> ModuleSpec:
    mod = ModuleSpec(name=name, provenance={"source": source})
    
    schemas = doc.get("components", {}).get("schemas", {})
    for tname, schema in schemas.items():
        fields = []
        props = schema.get("properties", {})
        for prop_name, prop_def in props.items():
            prop_type = prop_def.get("type", "string")
            kind = ScalarKind.string
            if prop_type == "integer": kind = ScalarKind.integer
            elif prop_type == "number": kind = ScalarKind.number
            elif prop_type == "boolean": kind = ScalarKind.boolean
            fields.append(FieldSpec(name=prop_name, type=kind))
        mod.types.append(TypeSpec(name=tname, fields=fields))
        
    paths = doc.get("paths", {})
    for path, methods in paths.items():
        for method, op in methods.items():
            op_spec = OperationSpec(
                name=op.get("operationId", f"{method}_{path.replace('/', '_')}"),
                method=method.upper(),
                path=path,
                description=op.get("description", "")
            )
            
            for param in op.get("parameters", []):
                f = FieldSpec(name=param["name"], type=ScalarKind.string)
                if param.get("in") == "path":
                    op_spec.request.path_params.append(f)
                elif param.get("in") == "query":
                    op_spec.request.query_params.append(f)
                    
            for status, resp in op.get("responses", {}).items():
                try:
                    code = int(status)
                    op_spec.responses.append(ResponseSpec(status_code=code))
                except ValueError:
                    pass
            
            mod.operations.append(op_spec)
            
    return mod

@register_importer("fastapi-importer")
class FastapiImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return _parse_openapi_doc(json.loads(content), "fastapi_imported", source)

@register_importer("springdoc-importer")
class SpringdocImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return _parse_openapi_doc(json.loads(content), "springdoc_imported", source)

@register_importer("express-nest-importer")
class ExpressNestImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return _parse_openapi_doc(json.loads(content), "express_nest_imported", source)

@register_importer("django-drf-importer")
class DjangoDrfImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return ModuleSpec(name="drf_imported", types=[TypeSpec(name="DrfStub")])

@register_importer("rails-importer")
class RailsImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return ModuleSpec(name="rails_imported", types=[TypeSpec(name="RailsStub")])

@register_importer("laravel-importer")
class LaravelImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return ModuleSpec(name="laravel_imported", types=[TypeSpec(name="LaravelStub")])

@register_importer("aspnet-importer")
class AspnetImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return ModuleSpec(name="aspnet_imported", types=[TypeSpec(name="AspnetStub")])

@register_importer("fastify-importer")
class FastifyImporter:
    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        return ModuleSpec(name="fastify_imported", types=[TypeSpec(name="FastifyStub")])
