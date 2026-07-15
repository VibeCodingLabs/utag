import json
from utag_core.registry import get_importer

def test_p2_importers():
    formats = [
        "django-drf-importer",
        "rails-importer",
        "laravel-importer",
        "aspnet-importer",
        "fastify-importer",
    ]
    for fmt in formats:
        imp = get_importer(fmt)
        assert imp is not None
        module = imp.ingest("dummy content")
        assert len(module.types) == 1

def _mock_openapi():
    return {
        "openapi": "3.1.0",
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"}
                    }
                }
            }
        },
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "parameters": [{"name": "id", "in": "path"}],
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }

def test_fastapi_importer_content():
    imp = get_importer("fastapi-importer")
    module = imp.ingest(json.dumps(_mock_openapi()))
    assert module.name == "fastapi_imported"
    assert len(module.types) == 1
    assert module.types[0].name == "User"
    assert len(module.operations) == 1
    assert module.operations[0].name == "getUser"

def test_springdoc_importer_content():
    imp = get_importer("springdoc-importer")
    module = imp.ingest(json.dumps(_mock_openapi()))
    assert module.name == "springdoc_imported"
    assert len(module.types) == 1
    assert module.types[0].name == "User"
    assert len(module.operations) == 1
    assert module.operations[0].name == "getUser"

def test_express_nest_importer_content():
    imp = get_importer("express-nest-importer")
    module = imp.ingest(json.dumps(_mock_openapi()))
    assert module.name == "express_nest_imported"
    assert len(module.types) == 1
    assert module.types[0].name == "User"
    assert len(module.operations) == 1
    assert module.operations[0].name == "getUser"
