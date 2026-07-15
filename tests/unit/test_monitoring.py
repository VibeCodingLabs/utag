from utag_core.monitoring import (
    AgentReadinessScore,
    DocsSmellReport,
    MCPToolQualityScore,
    OperationCoverageReport,
    RuntimeDriftReport,
    UsageAnalyticsEvent
)

def test_agent_readiness_score():
    s = AgentReadinessScore(total_score=85, dimensions={"schema": 10}, remediation_suggestions=["Add examples"])
    assert s.total_score == 85
    assert s.dimensions["schema"] == 10
    assert "Add examples" in s.remediation_suggestions

def test_docs_smell_report():
    r = DocsSmellReport(smells_found=2, details=["smell 1", "smell 2"])
    assert r.smells_found == 2
    assert len(r.details) == 2

def test_mcp_tool_quality_score():
    s = MCPToolQualityScore(tool_name="test-tool", score=90, warnings=[])
    assert s.tool_name == "test-tool"
    assert s.score == 90

def test_operation_coverage_report():
    r = OperationCoverageReport(covered_operations=5, total_operations=10)
    assert r.covered_operations == 5
    assert r.total_operations == 10

def test_runtime_drift_report():
    r = RuntimeDriftReport(drift_detected=True, drift_details=["type mismatch"])
    assert r.drift_detected is True
    assert "type mismatch" in r.drift_details

def test_usage_analytics_event():
    e = UsageAnalyticsEvent(event_type="generation", event_data={"target": "python-sdk"})
    assert e.event_type == "generation"
    assert e.event_data["target"] == "python-sdk"
