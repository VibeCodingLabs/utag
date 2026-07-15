import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec

def _get_module():
    return ModuleSpec(
        name="testmod",
        operations=[
            OperationSpec(name="getUser", method="GET", path="/users/{id}"),
            OperationSpec(name="updateUser", method="POST", path="/users")
        ]
    )

def test_swr_hooks_generator():
    gen = get_generator("swr-hooks")
    out = gen.generate(_get_module())
    assert "testmod-swr.ts" in out
    content = out["testmod-swr.ts"]
    assert 'import useSWR from "swr";' in content
    assert "export const useGetUser" in content
    assert "useSWR('getUser'" in content

def test_zustand_client_generator():
    gen = get_generator("zustand-client")
    out = gen.generate(_get_module())
    assert "testmod-zustand.ts" in out
    content = out["testmod-zustand.ts"]
    assert 'import { create } from "zustand";' in content
    assert "export const useTestmodStore" in content
    assert "getUser" in content
    assert "updateUser" in content
