"""~/.utag conventions + session loop, all against real dirs on disk:
lazy skill index vs on-demand bodies, $SKILL_DIR injection, project-over-global
override, NL trigger + slash invocation, custom commands with $ARGUMENTS,
hooks firing with env, credentials 0600, models catalog (cached, offline-safe)."""
import asyncio
import json
import os
import stat
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

from agent_harness import Session, UtagHome, load_catalog, models

SKILL_MD = """---
name: {name}
description: {desc}
triggers: [reconcile, month-end]
---

# {name}

Run `$SKILL_DIR/scripts/close.sh` then verify totals.
"""


def _mk_home(tmp_path, monkeypatch) -> UtagHome:
    g = tmp_path / "ghome" / ".utag"
    proj = tmp_path / "work" / "repo"
    (proj / ".utag").mkdir(parents=True)
    monkeypatch.chdir(proj)
    sk = g / "skills" / "finance" / "accounting" / "close" / "monthly"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(SKILL_MD.format(name="monthly-close",
                                                 desc="Close the books monthly. Use for reconciliation."))
    (sk / "scripts").mkdir()
    cmd = g / "commands"; cmd.mkdir(parents=True)
    (cmd / "review.md").write_text("---\ndescription: review a file\n---\nReview this thoroughly: $ARGUMENTS")
    rules = g / "rules"; rules.mkdir()
    (rules / "00-style.md").write_text("Always answer tersely.")
    (g / "hooks.yaml").write_text("pre-prompt:\n  - 'echo \"hook saw: $UTAG_PROMPT\" > "
                                  + str(tmp_path / "hook.out") + "'\n")
    return UtagHome.resolve(cwd=proj, global_dir=g)


def test_lazy_index_and_skill_dir_injection(tmp_path, monkeypatch):
    home = _mk_home(tmp_path, monkeypatch)
    assert home.project_dir and home.project_dir.name == ".utag"
    idx = home.skills_index()
    assert "/monthly-close" in idx and "$SKILL_DIR" not in idx  # index is frontmatter-only
    ref = home.find_skill("monthly-close")
    body = ref.load()
    assert "$SKILL_DIR" not in body and str(ref.path.parent) in body  # injected


def test_project_overrides_global(tmp_path, monkeypatch):
    home = _mk_home(tmp_path, monkeypatch)
    psk = home.project_dir / "skills" / "finance" / "accounting" / "close" / "monthly"
    psk.mkdir(parents=True)
    (psk / "SKILL.md").write_text(SKILL_MD.format(name="monthly-close",
                                                  desc="PROJECT variant."))
    home.reindex()
    ref = home.find_skill("monthly-close")
    assert ref.scope == "project" and "PROJECT" in ref.description
    assert len([s for s in home.skills if s.name == "monthly-close"]) == 1  # deduped


def test_nl_trigger_preloads_skill_body(tmp_path, monkeypatch):
    home = _mk_home(tmp_path, monkeypatch)
    s = Session(home=home, model=TestModel())
    kind, payload = s.route("please help me reconcile the ledger")
    assert kind == "prompt" and "[skill monthly-close]" in payload and "close.sh" in payload


def test_slash_skill_and_custom_command(tmp_path, monkeypatch):
    home = _mk_home(tmp_path, monkeypatch)
    s = Session(home=home, model=TestModel())
    kind, payload = s.route("/monthly-close for Q2")
    assert kind == "prompt" and "for Q2" in payload and "close.sh" in payload
    kind, payload = s.route("/review src/api.py")
    assert kind == "prompt" and payload == "Review this thoroughly: src/api.py"
    kind, payload = s.route("/help")
    assert kind == "local" and "/monthly-close" in payload and "/review" in payload


def test_turn_runs_hooks_and_model(tmp_path, monkeypatch):
    home = _mk_home(tmp_path, monkeypatch)
    s = Session(home=home, model=TestModel(custom_output_text="terse answer"))
    out = asyncio.run(s.turn("summarize the repo"))
    assert out == "terse answer"
    assert (tmp_path / "hook.out").read_text().startswith("hook saw: summarize")
    assert "Always answer tersely." in s.system_prompt()  # rules always in force
    assert "load_skill" in {t for t in s.agent()._function_toolset.tools}


def test_credentials_written_0600(tmp_path, monkeypatch):
    home = _mk_home(tmp_path, monkeypatch)
    home.set_credential("anthropic", "sk-test-123")
    p = home.credentials_path()
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert home.get_credential("anthropic") == "sk-test-123"
    assert json.loads(p.read_text())["anthropic"]["api_key"] == "sk-test-123"


def test_models_catalog_cached_and_offline_safe(tmp_path):
    cache = tmp_path / "cache"
    try:
        cat = load_catalog(cache)
    except Exception:
        pytest.skip("no network for models.dev")
    rows = models(cat, provider="anthropic", tool_call_only=True, limit=5)
    assert rows and all(m.tool_call for m in rows) and rows[0].context > 0
    # offline path: unreachable URL must serve the stale cache, not fail
    cat2 = load_catalog(cache, refresh=True, url="http://127.0.0.1:1/nope")
    assert cat2.keys() == cat.keys()
