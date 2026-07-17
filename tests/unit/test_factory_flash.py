"""F6: Flash burst tool catalog — sizing from profile, capability gating.

The endpoints only construct with the optional `flash` extra + RUNPOD_API_KEY,
so v1 tests the catalog/manifest logic and the honest gate, not live provisioning.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from utag_factory.config import load_config
from utag_factory.flash_tools import build_endpoints, catalog, flash_available

ROOT = Path(__file__).resolve().parents[2]


def test_catalog_sized_from_cloud_burst(monkeypatch):
    monkeypatch.setenv("UTAG_AUTOSCALING_PROFILE", "cloud_burst")
    specs = {s.name: s for s in catalog(load_config(ROOT))}
    assert set(specs) == {"run-python", "embed", "batch-generate"}
    assert specs["run-python"].max_workers == 20      # cloud_burst max_workers
    assert specs["run-python"].min_workers == 0        # scale-to-zero
    assert specs["embed"].max_workers == 10            # max_embedding_workers
    assert specs["embed"].resource == "gpu"


def test_build_endpoints_gated_without_key(monkeypatch):
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    assert flash_available() is False
    with pytest.raises(RuntimeError, match="RUNPOD_API_KEY"):
        build_endpoints(load_config(ROOT))
