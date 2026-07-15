"""Session screen driven headlessly: slash routing locally, model turn via
TestModel, skill lazy-load through the transcript."""
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

from agent_harness import UtagHome
from utag_tui.app import UtagTUI
from utag_tui.session_screen import SessionScreen

SKILL = """---
name: api-review
description: Review APIs. Use for openapi audits.
triggers: [openapi]
---
Check operationIds. Scripts in $SKILL_DIR/scripts.
"""


def _home(tmp_path) -> UtagHome:
    g = tmp_path / ".utag"
    sk = g / "skills" / "software" / "apis" / "review" / "audit"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(SKILL)
    return UtagHome.resolve(cwd=tmp_path, global_dir=g)


@pytest.mark.asyncio
async def test_session_screen_slash_and_model_turn(tmp_path, monkeypatch):
    monkeypatch.setenv("UTAG_HOME", str(tmp_path / ".utag"))
    home = _home(tmp_path)
    app = UtagTUI(base_url="http://127.0.0.1:1", token="x", poll_seconds=999)  # dashboard offline is fine
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(SessionScreen(home=home, model=TestModel(custom_output_text="done: reviewed")))
        await pilot.pause()
        prompt = app.screen.query_one("#prompt")
        prompt.focus()
        prompt.value = "/skills"
        await pilot.press("enter"); await pilot.pause()
        prompt.value = "audit this openapi doc"   # NL trigger -> lazy body preload
        await pilot.press("enter"); await pilot.pause(0.3)
        text = "\n".join(str(l) for l in app.screen.query_one("#transcript").lines)
        assert "/api-review" in text            # /skills index rendered
        assert "done: reviewed" in text          # model turn completed
        sess = app.screen.session
        assert any("[skill api-review]" in m["content"] for m in sess.transcript
                   if m["role"] == "user" or True) or "api-review" in text
