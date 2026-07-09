"""pi-RPC bridge tested against a fake pi process speaking the documented JSONL protocol."""
import sys
import textwrap

import pytest
from pydantic import BaseModel, ConfigDict

from utag_core.ports import TextPortStructuredAdapter
from utag_core.repair import TerminalGenerationError
from utag_generators.backends.pi_rpc_backend import PiRpcPort

FAKE_PI = textwrap.dedent('''
    import json, sys
    last = ""
    for line in sys.stdin:
        line = line.rstrip("\\r\\n")
        if not line: continue
        msg = json.loads(line)
        t, i = msg.get("type"), msg.get("id")
        if t == "prompt":
            # echo a JSON body; first prompt returns invalid (missing field) to exercise repair
            last = '{"name": "kb"}' if "failed validation" not in msg.get("message", "") \\
                   else '{"name": "kb", "chunks": 3}'
            print(json.dumps({"type": "event", "event": "agent_end"}), flush=True)
            print(json.dumps({"type": "response", "id": i, "success": True}), flush=True)
        elif t == "get_last_assistant_text":
            print(json.dumps({"type": "response", "id": i, "success": True, "data": last}), flush=True)
        else:
            print(json.dumps({"type": "response", "id": i, "success": True}), flush=True)
''')


class KB(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    chunks: int


def _fake_cmd(tmp_path):
    f = tmp_path / "fake_pi.py"
    f.write_text(FAKE_PI)
    return [sys.executable, str(f)]


def test_pi_rpc_roundtrip_with_shared_repair_loop(tmp_path):
    with PiRpcPort(cmd=_fake_cmd(tmp_path), timeout=10) as port:
        adapter = TextPortStructuredAdapter(port)
        out = adapter.generate(prompt="ingest kb", response_model=KB, max_attempts=3)
    assert out == KB(name="kb", chunks=3)  # repaired on attempt 2 via feedback


def test_pi_rpc_missing_binary_is_terminal():
    port = PiRpcPort(cmd=["definitely-not-a-binary-xyz"])
    with pytest.raises(TerminalGenerationError):
        port.start()
