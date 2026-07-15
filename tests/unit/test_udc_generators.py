"""react-component-library: typed, accessible, token-driven TSX from design.yaml."""
from __future__ import annotations

from pathlib import Path

import pytest

import utag_generators  # noqa: F401
from utag_core.ir import ModuleSpec
from utag_core.registry import get_generator

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def files():
    module = ModuleSpec(name="design", description="d",
                        provenance={"design_yaml": (ROOT / "design.yaml").read_text()})
    return get_generator("react-component-library").generate(module)


def test_components_layouts_routes_emitted(files):
    assert "generated/components/RunStatusCard.tsx" in files
    assert "generated/layouts/ConsoleShell.tsx" in files
    assert "generated/routes/RunsPage.tsx" in files


def test_component_typed_and_accessible(files):
    tsx = files["generated/components/RunStatusCard.tsx"]
    assert "export interface RunStatusCardProps" in tsx
    assert 'export type RunStatusCardState = "idle" | "loading" | "error"' in tsx
    assert 'aria-label="run-status-card"' in tsx
    assert "tabIndex={0}" in tsx
    assert "var(--utag-color-bg)" in tsx and "#" not in tsx.split("//", 1)[1]


def test_table_component_is_semantic(files):
    tsx = files["generated/components/RunTable.tsx"]
    assert "<table" in tsx and 'aria-label="run-table"' in tsx


def test_layout_regions_have_accessible_names(files):
    tsx = files["generated/layouts/ConsoleShell.tsx"]
    for region in ("sidebar", "header", "main", "inspector"):
        assert f'aria-label="{region}"' in tsx
    assert "gridTemplateAreas" in tsx


def test_route_composes_layout_and_components(files):
    tsx = files["generated/routes/RunsPage.tsx"]
    assert "ConsoleShell" in tsx and "<RunTable />" in tsx and "<RunInspector />" in tsx
