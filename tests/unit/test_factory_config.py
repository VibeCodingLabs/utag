"""F0: the operator template is canonical, validated, and drives config resolution."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from utag_core.schemas.factory import AutoscalingProfile
from utag_factory.config import load_config, parse_bytes, parse_duration_s

ROOT = Path(__file__).resolve().parents[2]


def test_operator_template_validates_and_is_canonical():
    doc = yaml.safe_load((ROOT / "policies/autoscaling.yaml").read_text())
    profile = AutoscalingProfile.model_validate(doc)
    assert profile.template.status == "canonical"
    assert profile.execution.supervisor == "python"          # decision of record
    assert profile.queue.streams.dead_letters == "utag:dlq"
    assert profile.cache.semantic.similarity_threshold == 0.94
    assert "cloud_burst" in profile.profiles


def test_unknown_fields_rejected():
    doc = yaml.safe_load((ROOT / "policies/autoscaling.yaml").read_text())
    doc["surprise"] = True
    with pytest.raises(Exception, match="surprise"):
        AutoscalingProfile.model_validate(doc)


def test_profile_selection_via_env(monkeypatch):
    cfg = load_config(ROOT)
    assert cfg.active_profile_name == "local_jetson_8gb"      # template default
    monkeypatch.setenv("UTAG_AUTOSCALING_PROFILE", "cloud_burst")
    cfg = load_config(ROOT)
    assert cfg.worker_profile.max_workers == 20
    monkeypatch.setenv("UTAG_AUTOSCALING_PROFILE", "nope")
    with pytest.raises(ValueError, match="unknown autoscaling profile"):
        load_config(ROOT)


def test_duration_and_size_parsing():
    assert parse_duration_s("5s") == 5
    assert parse_duration_s("15m") == 900
    assert parse_duration_s("500ms") == 0.5
    assert parse_bytes("2GiB") == 2 * 1024**3
    with pytest.raises(ValueError):
        parse_duration_s("5 parsecs")
