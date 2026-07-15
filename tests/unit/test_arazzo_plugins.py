import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="arazzomod",
        operations=[
            OperationSpec(
                name="createUser",
                method="POST",
                path="/users",
                request=RequestSpec(),
                responses=[ResponseSpec(status_code=201)]
            )
        ]
    )

def test_arazzo_workflows_generator_content():
    gen = get_generator("arazzo-workflows")
    out = gen.generate(_get_module())
    
    import yaml
    data = yaml.safe_load(out["arazzomod-workflows.arazzo.yaml"])
    
    assert data["arazzo"] == "1.0.0"
    assert data["info"]["title"] == "arazzomod Workflows"
    assert data["sourceDescriptions"][0]["type"] == "openapi"
    assert len(data["workflows"]) == 1
    
    workflow = data["workflows"][0]
    assert len(workflow["steps"]) == 1
    step = workflow["steps"][0]
    assert step["operationId"] == "createUser"
    assert step["successCriteria"][0]["condition"] == "$statusCode == 201"
