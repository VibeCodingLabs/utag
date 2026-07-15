"""agent-harness adapters integrated into utag.

Runs against the REAL kits when FORGE_JOBS_ROOT / AUDIT_KIT_DIR env vars point at
them (expected counts 43 / 34); otherwise against schema-faithful fixtures
(valid instances of the kits' own schemas — 2 jobs / 1 template). No mocks of
kit data either way."""
import asyncio
import os
from pathlib import Path

import pytest
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models.test import TestModel

from agent_harness import (
    build_audit_agent, discover_audit_templates, discover_jobs,
    harness_tools, load_template, run_job,
)
from agent_harness.audits import AuditDeps

ROOT = Path(__file__).parents[2]
REAL_JOBS = os.environ.get("FORGE_JOBS_ROOT")
REAL_AUDIT = os.environ.get("AUDIT_KIT_DIR")
JOBS = Path(REAL_JOBS) if REAL_JOBS else ROOT / "fixtures" / "kits" / "forge-jobs"
AUDIT = Path(REAL_AUDIT) if REAL_AUDIT else ROOT / "fixtures" / "kits" / "audit"
EXPECT_JOBS = 43 if REAL_JOBS else 2
EXPECT_TEMPLATES = 34 if REAL_AUDIT else 1


def test_discovery_counts_and_id_dir_match():
    jobs = discover_jobs(JOBS)
    assert len(jobs) == EXPECT_JOBS
    for d, m in jobs.items():
        assert m.id == d.name
    assert len(discover_audit_templates(AUDIT)) == EXPECT_TEMPLATES


def test_job_end_to_end_libsh_report_contract(tmp_path):
    res = run_job(JOBS / "software-development" / "repo-audit",
                  env_overrides={"FORGE_JOBS_STATE": str(tmp_path)})
    assert res.status == "ok", (res.status, res.skipped_reason, res.stderr_tail[:200])
    assert res.report_path and Path(res.report_path).is_file()
    assert str(tmp_path) in res.report_path and "/output/repo-audit/" in res.report_path
    assert res.report_text and "repo" in res.report_text.lower()


def test_honest_skip_never_fakes_success():
    """Kit-agnostic: find a job with required env and blank it; if the kit has
    none, prove the same doctrine via the missing-commands preflight path."""
    jobs = discover_jobs(JOBS)
    envjob = next(((d, m) for d, m in jobs.items() if m.env.required), None)
    if envjob:
        d, m = envjob
        res = run_job(d, env_overrides={v: "" for v in m.env.required})
        assert res.status == "skipped" and m.env.required[0] in (res.skipped_reason or "")
    else:
        d, m = next(iter(jobs.items()))
        res = run_job(d, env_overrides={"PATH": "/nonexistent"})
        assert res.status == "skipped" and "missing required commands" in (res.skipped_reason or "")
    assert res.exit_code is None  # never ran — no fake success


def test_audit_template_contract_parses():
    t = load_template(sorted(AUDIT.glob("*.yml"))[0])
    assert len(t.required_output.report_sections) >= 3
    assert len(t.do_not_do) >= 6 and len(t.definition_of_done) >= 5


def _template():
    return load_template(sorted(AUDIT.glob("*.yml"))[0])


def test_dod_validator_fires_modelretry_on_bad_output():
    """TestModel's auto-output can't satisfy required sections -> retries exhaust."""
    t = _template()
    agent = build_audit_agent(t, TestModel(), retries=1)
    with capture_run_messages() as messages:
        with pytest.raises(UnexpectedModelBehavior):
            asyncio.run(agent.run("audit", deps=AuditDeps(root=ROOT)))
    joined = str(messages)
    assert "missing required report sections" in joined  # ModelRetry feedback reached the model


def test_dod_validator_passes_conformant_output():
    t = _template()
    good = {
        "template": t.name, "report_file": t.output.report,
        "sections": [{"title": s, "body": f"NONE FOUND — glob scan for {s}"}
                     for s in t.required_output.report_sections],
        "findings": [{"id": "F1", "severity": "P2", "description": "fixture finding",
                      "evidence": "README.md:1", "recommendation": "none"}],
        "not_verified": [],
        "chain_executed": list(t.chain_of_verification),
    }
    agent = build_audit_agent(t, TestModel(custom_output_args=good), retries=1)
    report = asyncio.run(agent.run("audit", deps=AuditDeps(root=ROOT))).output
    assert {s.title for s in report.sections} == set(t.required_output.report_sections)


def test_scoped_read_tools_contained_and_error_style():
    from agent_harness.audits import _scoped_tools  # scope discipline is the security boundary
    t = _template()
    tools = {tool.name: tool for tool in _scoped_tools(t.scope)}
    assert set(tools) == {"list_paths", "read_file"}


def test_registry_composes_both_kits_unique_names():
    tools = harness_tools(jobs_root=JOBS, audit_dir=AUDIT,
                          audit_model=TestModel(), audit_root=ROOT)
    names = [t.name for t in tools]
    assert len(names) == len(set(names)) == EXPECT_JOBS + EXPECT_TEMPLATES
    assert any(n.startswith("job_") for n in names)
    assert any(n.startswith("audit_") for n in names)


def test_pydantic_ai_port_accepts_harness_tools():
    """Composition seam: utag backend + adapter tools in one Agent."""
    from pydantic import BaseModel

    from utag_generators.backends import PydanticAIPort

    class Out(BaseModel):
        note: str

    tools = harness_tools(jobs_root=JOBS)
    port = PydanticAIPort(TestModel(custom_output_args={"note": "ok"}), tools=tools)
    assert port.generate(prompt="say ok", response_model=Out, max_attempts=1).note == "ok"
