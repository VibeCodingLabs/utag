"""Static validation of .github/workflows: parseable, jobbed, mapped, secret-free."""
from __future__ import annotations

from pathlib import Path

import yaml

from utag_core.automations import _SECRET_PATTERN, load_automations

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((ROOT / ".github/workflows").glob("*.yml"))


def test_workflows_exist():
    names = {p.stem for p in WORKFLOWS}
    assert {"schema-drift", "design-build", "ui-snapshot", "observability-export",
            "autoresearch-weekly", "release-gate", "ci"} <= names


def test_workflows_parse_with_jobs_and_steps():
    for path in WORKFLOWS:
        doc = yaml.safe_load(path.read_text())
        assert doc.get("jobs"), f"{path.name}: no jobs"
        for job_name, job in doc["jobs"].items():
            assert job.get("steps"), f"{path.name}:{job_name}: no steps"


def test_workflow_automation_bijection():
    automations = set(load_automations(ROOT))
    workflows = {p.stem for p in WORKFLOWS}
    assert automations == workflows


def test_no_plaintext_secrets():
    for path in WORKFLOWS:
        assert not _SECRET_PATTERN.search(path.read_text()), f"{path.name}: secret-like value"
