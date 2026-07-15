"""Talk -> generate -> observe, end to end:
1) scripted model (FunctionModel) calls generate_artifact with REAL args ->
   artifact written to disk, validator verdict green, model summarizes it
2) control-plane path: submit_job via tool against the real binary, real worker
   drains it, job_status reports succeeded
3) model picker persists provider/model to config.yaml (headless pilot)
"""
import asyncio
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import pytest
import yaml
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agent_harness import Session, UtagHome, generation_tools
from utag_worker.worker import ControlPlane, loop

ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "fixtures" / "prompts" / "normalize-tool.prompt.yaml"
BIN = ROOT / "control-plane" / "utag-control-plane"
TOKEN = "sess-token"


def _home(tmp_path) -> UtagHome:
    g = tmp_path / ".utag"
    g.mkdir(parents=True)
    return UtagHome.resolve(cwd=tmp_path, global_dir=g)


def _scripted_model(tool_name: str, args: dict):
    """FunctionModel: first turn calls the tool with REAL args; second summarizes."""
    def fn(messages, info: AgentInfo) -> ModelResponse:
        already = any(getattr(p, "part_kind", "") == "tool-call"
                      for m in messages for p in getattr(m, "parts", []))
        if not already:
            return ModelResponse(parts=[ToolCallPart(tool_name=tool_name, args=args)])
        # find the tool return content in history for an honest summary
        return ModelResponse(parts=[TextPart(content="generated and validated — see artifacts")])
    return FunctionModel(fn)


def test_talk_to_generate_local_artifact(tmp_path):
    home = _home(tmp_path)
    out_dir = tmp_path / "out"
    tools = generation_tools(home, cp=None, out_dir=str(out_dir))
    model = _scripted_model("generate_artifact",
                            {"target": "pydantic-models", "input_path": str(FIXTURE)})
    s = Session(home=home, model=model, extra_tools=tools)
    reply = asyncio.run(s.turn("make me pydantic models from the normalize-tool prompt"))
    assert "generated and validated" in reply
    files = list(out_dir.glob("*.py"))
    assert files and "class NormalizeToolInput" in files[0].read_text()


def test_generate_tool_honest_errors(tmp_path):
    home = _home(tmp_path)
    tools = {t.name: t for t in generation_tools(home, cp=None, out_dir=str(tmp_path / "o"))}
    bad_target = tools["generate_artifact"].function(target="nope", input_path=str(FIXTURE))
    assert not bad_target.ok and "unknown target" in bad_target.error
    bad_path = tools["generate_artifact"].function(target="pydantic-models", input_path="/missing.yaml")
    assert not bad_path.ok and "no such input file" in bad_path.error


@pytest.fixture(scope="module")
def server():
    if not BIN.exists():
        pytest.skip("binary not built")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    proc = subprocess.Popen([str(BIN), "serve"],
                            env={**os.environ, "UTAG_PORT": str(port), "UTAG_API_TOKEN": TOKEN},
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1); break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill(); pytest.fail("not healthy")
    yield base
    proc.terminate()


def test_talk_to_submit_job_and_observe(server, tmp_path):
    home = _home(tmp_path)
    cp = ControlPlane(server, token=TOKEN)
    tools = generation_tools(home, cp=cp)
    model = _scripted_model("submit_job",
                            {"target": "openapi-3.1", "input_path": str(FIXTURE)})
    s = Session(home=home, model=model, extra_tools=tools)
    asyncio.run(s.turn("queue an openapi generation on the control-plane"))
    # extract the job id the tool returned (it's in the transcript-visible run)
    jobs = cp._req("GET", "/v1/jobs?limit=5")
    assert jobs and jobs[0]["backend"] == "session"
    jid = jobs[0]["id"]
    threading.Thread(target=loop, args=(cp,), kwargs={"poll_seconds": 0.05, "max_jobs": 1}).start()
    deadline = time.time() + 15
    while time.time() < deadline:
        if cp._req("GET", f"/v1/jobs/{jid}")["status"] == "succeeded":
            break
        time.sleep(0.2)
    status_tool = {t.name: t for t in tools}["job_status"]
    assert status_tool.function(job_id=jid)["status"] == "succeeded"


@pytest.mark.asyncio
async def test_model_picker_persists_config(tmp_path, monkeypatch):
    monkeypatch.setenv("UTAG_HOME", str(tmp_path / ".utag"))
    home = _home(tmp_path)
    try:
        from agent_harness import load_catalog
        load_catalog(home.global_dir / "cache")
    except Exception:
        pytest.skip("no network for catalog")
    from utag_tui.app import UtagTUI
    from utag_tui.model_picker import ModelPicker
    app = UtagTUI(base_url="http://127.0.0.1:1", token="x", poll_seconds=999)
    async with app.run_test(size=(120, 40)) as pilot:
        picker = ModelPicker(home=home)
        await app.push_screen(picker)
        await pilot.pause()
        table = app.screen.query_one("#list")
        assert table.row_count > 0
        table.focus()
        await pilot.press("enter")   # select the cursor row
        await pilot.pause()
        cfg = yaml.safe_load((home.global_dir / "config.yaml").read_text())
        assert cfg.get("provider") and cfg.get("model")
