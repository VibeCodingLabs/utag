"""TUI e2e, fully headless: real control-plane binary + real worker + Textual
pilot driving the actual app — submit via command bar, watch the table reach
succeeded, select the row, read the artifact verdict in the log."""
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from utag_tui.app import UtagTUI
from utag_worker.worker import ControlPlane, loop

BIN = Path(__file__).parents[2] / "control-plane" / "utag-control-plane"
FIXTURE = Path(__file__).parents[2] / "fixtures" / "prompts" / "categorize-file.prompt.yaml"
TOKEN = "tui-token"


@pytest.fixture(scope="module")
def server():
    if not BIN.exists():
        pytest.skip("control-plane binary not built")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    env = {**os.environ, "UTAG_PORT": str(port), "UTAG_API_TOKEN": TOKEN}
    proc = subprocess.Popen([str(BIN), "serve"], env=env,
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


def _table_statuses(app) -> list[str]:
    table = app.query_one("#jobs")
    return [str(table.get_row_at(i)[2]) for i in range(table.row_count)]


@pytest.mark.asyncio
async def test_tui_submit_watch_succeed_inspect(server):
    app = UtagTUI(base_url=server, token=TOKEN, poll_seconds=0.2)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # targets tree populated from the live registry
        assert "pydantic-models" in [str(n.label) for n in app.query_one("#nav").root.children]
        # submit through the real command bar
        cmd = app.query_one("#cmd")
        cmd.focus()
        cmd.value = f"generate pydantic-models {FIXTURE}"
        await pilot.press("enter")
        await pilot.pause()
        assert any("queued" in s for s in _table_statuses(app))
        # a real worker drains the queue while the TUI polls
        cp = ControlPlane(server, token=TOKEN)
        t = threading.Thread(target=loop, args=(cp,), kwargs={"poll_seconds": 0.05, "max_jobs": 1})
        t.start(); t.join(timeout=30)
        deadline = time.time() + 10
        while time.time() < deadline:
            await pilot.pause(0.3)
            if any("succeeded" in s for s in _table_statuses(app)):
                break
        assert any("succeeded" in s for s in _table_statuses(app)), _table_statuses(app)
        # row select -> artifact verdict in the log
        table = app.query_one("#jobs")
        table.focus()
        await pilot.press("enter")
        await pilot.pause()
        log_text = "\n".join(str(line) for line in app.query_one("#log").lines)
        assert "artifacts: 1" in log_text and "valid" in log_text


@pytest.mark.asyncio
async def test_tui_rejects_unknown_target_and_bad_path(server):
    app = UtagTUI(base_url=server, token=TOKEN, poll_seconds=5)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        cmd = app.query_one("#cmd")
        cmd.focus()
        cmd.value = "generate not-a-target x.yaml"
        await pilot.press("enter"); await pilot.pause()
        cmd.value = f"generate pydantic-models /nope/missing.yaml"
        await pilot.press("enter"); await pilot.pause()
        log_text = "\n".join(str(line) for line in app.query_one("#log").lines)
        assert "unknown target" in log_text and "no such input file" in log_text


@pytest.mark.asyncio
async def test_tui_status_panel_counts(server):
    app = UtagTUI(base_url=server, token=TOKEN, poll_seconds=0.2)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.5)
        status = str(app.query_one("#status").content)
        assert "succeeded" in status and "targets" in status
