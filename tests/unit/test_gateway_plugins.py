import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="kongmod",
        operations=[
            OperationSpec(
                name="getUser",
                method="GET",
                path="/users/{id}",
                request=RequestSpec(path_params=[FieldSpec(name="id", type=ScalarKind.string)]),
            )
        ]
    )

def test_kong_gateway_config_generator_content():
    gen = get_generator("kong-gateway-config")
    out = gen.generate(_get_module())
    
    import yaml
    data = yaml.safe_load(out["kongmod-kong.yaml"])
    
    assert data["_format_version"] == "3.0"
    assert len(data["services"]) == 1
    
    service = data["services"][0]
    assert service["name"] == "kongmod-service"
    assert len(service["routes"]) == 1
    
    route = service["routes"][0]
    # The path /users/{id} strips {id} resulting in /users/
    assert route["paths"][0] == "~^/users/"
