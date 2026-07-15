"""Automation manifests: valid, filename-matched, entrypointed, workflow-mapped."""
from __future__ import annotations

from pathlib import Path

import pytest

from utag_core.automations import automation_problems, load_automations
from utag_core.schemas.core import RegistryKind

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = {"schema-drift", "design-build", "ui-snapshot", "observability-export",
            "autoresearch-weekly", "release-gate", "ci", "ui-build"}


def test_all_expected_automations_present_and_valid():
    automations = load_automations(ROOT)
    assert set(automations) == EXPECTED
    for aid, m in automations.items():
        assert m.kind == RegistryKind.automation
        assert m.entrypoints, f"{aid}: no entrypoints"
        assert m.test_files, f"{aid}: no test files"


def test_doctor_clean_on_repo():
    assert automation_problems(ROOT) == []


def test_id_filename_mismatch_rejected(tmp_path):
    d = tmp_path / ".utag/automations"
    d.mkdir(parents=True)
    (d / "wrong-name.yaml").write_text(
        "id: other\nname: X\nversion: 1.0.0\nkind: automation\nentrypoints: ['true']\n")
    with pytest.raises(ValueError, match="filename stem"):
        load_automations(tmp_path)


def test_doctor_flags_unmapped_workflow_and_secrets(tmp_path):
    (tmp_path / ".utag/automations").mkdir(parents=True)
    wf = tmp_path / ".github/workflows"
    wf.mkdir(parents=True)
    (wf / "rogue.yml").write_text(
        "name: rogue\non: [push]\njobs:\n  x:\n    steps:\n"
        "      - run: echo ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n")
    problems = automation_problems(tmp_path)
    assert any("no matching automation manifest" in p for p in problems)
    assert any("plaintext secret" in p for p in problems)
