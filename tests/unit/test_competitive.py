from utag_core.competitive import (
    ToolProviderSpec,
    PrimitiveSpec,
    CapabilityMatrix,
    ProviderGap,
    ImplementationStatus,
)

def test_implementation_status():
    assert ImplementationStatus.implemented.value == "implemented"

def test_primitive_spec():
    prim = PrimitiveSpec(id="p1", name="Prim 1", category="Cat A")
    assert prim.id == "p1"
    assert prim.description == ""

def test_provider_gap():
    gap = ProviderGap(
        primitive_id="p1",
        competitor_status=ImplementationStatus.implemented,
        utag_status=ImplementationStatus.planned,
        gap_notes="Needs work"
    )
    assert gap.utag_status == ImplementationStatus.planned

def test_tool_provider_spec():
    tool = ToolProviderSpec(id="t1", name="Tool 1")
    assert tool.capabilities == {}
    tool.capabilities["p1"] = ImplementationStatus.implemented
    assert tool.capabilities["p1"] == ImplementationStatus.implemented

def test_capability_matrix():
    mat = CapabilityMatrix()
    assert mat.primitives == []
    assert mat.providers == []
    mat.primitives.append(PrimitiveSpec(id="p1", name="P1", category="C1"))
    mat.providers.append(ToolProviderSpec(id="t1", name="T1"))
    assert len(mat.primitives) == 1
    assert len(mat.providers) == 1
