from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="postman_mod",
        types=[TypeSpec(name="User", fields=[FieldSpec(name="id", type=ScalarKind.string)])],
        operations=[
            OperationSpec(
                name="createUser",
                method="POST",
                path="/users",
                request=RequestSpec(body_type="User", query_params=[FieldSpec(name="token", type=ScalarKind.string)]),
                responses=[ResponseSpec(status_code=201, body_type="User")]
            )
        ]
    )

def test_postman_collection_generator_content():
    gen = get_generator("postman-collection")
    out = gen.generate(_get_module())
    assert "postman_mod-postman.json" in out
    
    import json
    data = json.loads(out["postman_mod-postman.json"])
    assert data["info"]["name"] == "postman_mod"
    assert len(data["item"]) == 1
    
    item = data["item"][0]
    assert item["name"] == "createUser"
    assert item["request"]["method"] == "POST"
    
    # Query parameter
    assert len(item["request"]["url"]["query"]) == 1
    assert item["request"]["url"]["query"][0]["key"] == "token"
    
    # Body
    assert item["request"]["body"]["mode"] == "raw"
    assert "raw" in item["request"]["body"]
