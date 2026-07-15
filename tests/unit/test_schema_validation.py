"""Fixture contract: valid fixture passes, invalid fixture is rejected, per kind."""
from __future__ import annotations

from pathlib import Path

import pytest

from utag_core.schemas import SCHEMAS
from utag_core.schemas import tools

ROOT = Path(__file__).resolve().parents[2]
FDIR = ROOT / tools.FIXTURES_DIR


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_fixture_pair(kind):
    valid, invalid = FDIR / f"{kind}.valid.json", FDIR / f"{kind}.invalid.json"
    assert valid.is_file(), f"missing {valid}"
    assert invalid.is_file(), f"missing {invalid}"
    assert tools.validate_file(kind, valid) == []
    assert tools.validate_file(kind, invalid) != []


def test_design_yaml_validates():
    assert tools.validate_file("design-yaml", ROOT / "design.yaml") == []


def test_emitted_schemas_fresh():
    problems = [p for p in tools.validate_all(ROOT) if "stale" in p or "not emitted" in p]
    assert problems == []
