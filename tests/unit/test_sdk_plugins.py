import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="test_sdk",
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

def test_python_sdk_generator_content():
    gen = get_generator("python-sdk")
    out = gen.generate(_get_module())
    content = out["test_sdk_sdk.py"]
    assert "import httpx" in content
    assert "class ApiClient:" in content
    assert "async def getUser(self, id: str) -> User:" in content
    assert 'url = f"{self.base_url}/users/{id}"' in content
    assert 'response = await self.client.request("GET", url, params=params)' in content

def test_go_sdk_generator_content():
    gen = get_generator("go-sdk")
    out = gen.generate(_get_module())
    content = out["test_sdk_sdk.go"]
    assert "package sdk" in content
    assert "type ApiClient struct" in content
    assert "func (c *ApiClient) Getuser(id string) (User, error) {" in content
    assert 'reqURL := c.BaseURL + fmt.Sprintf("/users/%s", id)' in content
    assert 'req, err := http.NewRequest("GET", reqURL, nil)' in content
