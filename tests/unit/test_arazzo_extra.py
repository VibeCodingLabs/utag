import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, OperationSpec

def _get_module():
    return ModuleSpec(
        name="testarazzo",
        operations=[OperationSpec(name="op1", method="GET", path="/test")]
    )

def test_arazzo_agent_workflows_generator():
    gen = get_generator("arazzo-agent-workflows")
    out = gen.generate(_get_module())
    assert "testarazzo-agent-workflows.arazzo.yaml" in out
    assert "arazzo: 1.0.0" in out["testarazzo-agent-workflows.arazzo.yaml"]
    assert "agent-op1" in out["testarazzo-agent-workflows.arazzo.yaml"]

def test_overlay_diff_generator():
    gen = get_generator("overlay-diff")
    out = gen.generate(_get_module())
    assert "testarazzo-diff.yaml" in out
    assert "overlay: 1.0.0" in out["testarazzo-diff.yaml"]

def test_workflow_test_suite_generator():
    gen = get_generator("workflow-test-suite")
    out = gen.generate(_get_module())
    assert "testarazzo-workflow-tests.ts" in out
    assert "// Test workflow for op1" in out["testarazzo-workflow-tests.ts"]
    assert "assert.ok(true)" in out["testarazzo-workflow-tests.ts"]
