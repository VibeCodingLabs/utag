import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec

def _get_module():
    return ModuleSpec(
        name="test_testing",
        operations=[OperationSpec(name="op1", method="GET", path="/test")]
    )

def test_nock_generator():
    gen = get_generator("nock-tests")
    out = gen.generate(_get_module())
    content = out["test_testing-nock.ts"]
    assert 'import nock from "nock";' in content
    assert "nock('http://api.backend.internal')" in content
    assert ".get('/test')" in content

def test_supertest_generator():
    gen = get_generator("supertest-tests")
    out = gen.generate(_get_module())
    content = out["test_testing-supertest.ts"]
    assert 'import request from "supertest";' in content
    assert "request(app).get('/test')" in content
