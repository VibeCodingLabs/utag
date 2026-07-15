"""react-component-library + contract types + fixtures: typed, accessible,
data-rendering TSX generated from design.yaml."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import utag_generators  # noqa: F401
from utag_core.ir import ModuleSpec
from utag_core.registry import get_generator
from utag_core.schemas.observability import RunTrace

ROOT = Path(__file__).resolve().parents[2]


def _module(design_text: str | None = None) -> ModuleSpec:
    return ModuleSpec(name="design", description="d",
                      provenance={"design_yaml": design_text or (ROOT / "design.yaml").read_text()})


@pytest.fixture(scope="module")
def files():
    return get_generator("react-component-library").generate(_module())


def test_components_layouts_routes_hooks_emitted(files):
    assert "generated/components/RunTable.tsx" in files
    assert "generated/components/NavSidebar.tsx" in files
    assert "generated/layouts/ConsoleShell.tsx" in files
    assert "generated/routes/RunsPage.tsx" in files
    assert "generated/routes/HomePage.tsx" in files
    assert "generated/hooks/useInteractions.tsx" in files


def test_table_renders_data_and_wires_interaction(files):
    tsx = files["generated/components/RunTable.tsx"]
    assert "records?: RunTrace[]" in tsx
    assert 'import type { RunTrace } from "../schemas/contracts"' in tsx
    assert "<th>run_id</th>" in tsx
    assert "records.map((r, i) =>" in tsx
    assert 'select("select-run", r);' in tsx  # interaction source, generated from design.yaml
    assert 'if (e.key === "Enter")' in tsx    # keyboardRequired contract


def test_panel_target_renders_selected_record(files):
    tsx = files["generated/components/RunInspector.tsx"]
    assert 'useSelected("select-run") as RunTrace | undefined' in tsx
    assert "selected ?? records[0]" in tsx
    assert "<dt>run_id</dt>" in tsx
    assert "JSON.stringify(record.spans, null, 2)" in tsx  # complex fields shown as JSON


def test_timeline_chart_board_graph_render_real_fields(files):
    timeline = files["generated/components/RunTimeline.tsx"]
    assert "(r.spans ?? []).map((s, j)" in timeline and "s.end_ms" in timeline
    chart = files["generated/components/CostLatencyChart.tsx"]
    assert "(r.value / max) * 100" in chart
    board = files["generated/components/QueueDlqPanel.tsx"]
    assert 'r.status === "dead-letter"' in board  # enum columns known at generation time
    graph = files["generated/components/ArazzoWorkflowGraph.tsx"]
    assert "String(r.task_id)" in graph


def test_no_hex_colors_outside_tokens(files):
    for rel, tsx in files.items():
        body = tsx.split("do not edit by hand", 1)[-1]
        assert "#" not in body.replace("№", ""), f"hex/hash in {rel}"


def test_route_places_targets_in_inspector_and_nav_in_sidebar(files):
    tsx = files["generated/routes/RunsPage.tsx"]
    assert "sidebar={<NavSidebar />}" in tsx
    assert "inspector={" in tsx and "<RunInspector records={runs} />" in tsx
    assert "<RunTable records={runs} />" in tsx
    assert "SelectionProvider" in tsx
    assert 'import { runs } from "../fixtures/runs"' in tsx


def test_contract_types_close_over_nested_models():
    ts = get_generator("typescript-contract-types").generate(_module())["generated/schemas/contracts.ts"]
    assert "export interface RunTrace {" in ts
    assert "export interface RunSpan {" in ts          # nested model pulled in
    assert "spans?: RunSpan[];" in ts
    assert '"dead-letter"' in ts                        # enums become literal unions
    assert "extensions?: Record<string, unknown> | null;" in ts


def test_fixtures_are_schema_valid_and_typed():
    files = get_generator("design-fixtures").generate(_module())
    ts = files["generated/fixtures/runs.ts"]
    assert "export const runs: RunTrace[] =" in ts
    payload = json.loads(ts.split("=", 1)[1].rstrip().rstrip(";"))
    assert len(payload) == 3
    for record in payload:
        RunTrace.model_validate(record)
    assert payload[0]["run_id"] != payload[1]["run_id"]


def test_unknown_component_type_rejected():
    bad = (ROOT / "design.yaml").read_text().replace("type: nav", "type: hologram")
    with pytest.raises(ValueError, match="unknown type"):
        get_generator("react-component-library").generate(_module(bad))


def test_timeline_requires_spans_contract():
    bad = (ROOT / "design.yaml").read_text().replace(
        "  - id: run-timeline\n    type: timeline\n    props:\n      resource: runs",
        "  - id: run-timeline\n    type: timeline\n    props:\n      resource: metrics")
    with pytest.raises(ValueError, match="spans"):
        get_generator("react-component-library").generate(_module(bad))
