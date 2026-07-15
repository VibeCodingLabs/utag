import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="testmod",
        types=[TypeSpec(name="User", fields=[FieldSpec(name="id", type=ScalarKind.string)])],
        operations=[
            OperationSpec(
                name="getUser",
                method="GET",
                path="/users/{id}",
                request=RequestSpec(path_params=[FieldSpec(name="id", type=ScalarKind.string)]),
                responses=[ResponseSpec(status_code=200, body_type="User")]
            )
        ]
    )

def test_openapi_3_1_generator_content():
    gen = get_generator("openapi-3.1")
    out = gen.generate(_get_module())
    
    import json
    data = json.loads(out["testmod.openapi.json"])
    assert "openapi" in data
    assert data["openapi"] == "3.1.1"
    
    assert "/users/{id}" in data["paths"]
    get_op = data["paths"]["/users/{id}"]["get"]
    assert get_op["operationId"] == "getUser"
    assert get_op["parameters"][0]["name"] == "id"
    assert "200" in get_op["responses"]
    assert "content" in get_op["responses"]["200"]
