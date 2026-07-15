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

def test_hurl_generator_content():
    gen = get_generator("hurl-tests")
    out = gen.generate(_get_module())
    content = out["testmod.hurl"]
    assert "GET {{BASE_URL}}/users/test_id" in content
    assert "HTTP 200" in content

def test_wiremock_generator_content():
    gen = get_generator("wiremock-stubs")
    out = gen.generate(_get_module())
    
    import json
    data = json.loads(out["testmod-wiremock.json"])
    assert "mappings" in data
    assert len(data["mappings"]) == 1
    assert data["mappings"][0]["request"]["method"] == "GET"
    assert data["mappings"][0]["request"]["urlPath"] == "/users/test_id"
    assert data["mappings"][0]["response"]["status"] == 200
