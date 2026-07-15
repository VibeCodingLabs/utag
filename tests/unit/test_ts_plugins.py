import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="test_mod",
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

def test_typescript_types_generator():
    gen = get_generator("typescript-types")
    out = gen.generate(_get_module())
    assert "test-mod-types.ts" in out
    content = out["test-mod-types.ts"]
    assert "export interface User {" in content
    assert "id: string;" in content

def test_fetch_client_generator():
    gen = get_generator("fetch-client")
    out = gen.generate(_get_module())
    assert "test-mod-client.ts" in out
    content = out["test-mod-client.ts"]
    assert "export class ApiClient" in content
    assert "async getUser(id: string): Promise<User>" in content
    assert "const url = `${this.baseUrl}/users/${id}`;" in content

def test_tanstack_query_hooks_generator():
    gen = get_generator("tanstack-query-hooks")
    out = gen.generate(_get_module())
    assert "test-mod-hooks.ts" in out
    content = out["test-mod-hooks.ts"]
    assert "export const useGetUser = (id: string) => {" in content
    assert "useQuery<User, Error>" in content
    assert "queryKey: ['getUser', id]" in content

def test_msw_handlers_generator():
    gen = get_generator("msw-handlers")
    out = gen.generate(_get_module())
    assert "test-mod-msw.ts" in out
    content = out["test-mod-msw.ts"]
    assert "export const test_modHandlers = [" in content
    assert "http.get('*/users/:id'" in content
