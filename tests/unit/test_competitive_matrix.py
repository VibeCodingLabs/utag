from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec

def test_competitive_matrix_generator():
    gen = get_generator("competitive-matrix")
    assert gen is not None
    
    module = ModuleSpec(name="test_mod")
    out = gen.generate(module)
    assert "reports/competitive_matrix.json" in out
    
    import json
    data = json.loads(out["reports/competitive_matrix.json"])
    assert data["module_name"] == "test_mod"
