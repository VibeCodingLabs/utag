"""pi RPC bridge — JSONL over stdio to `pi --mode rpc` (earendil-works/pi).

Protocol (verified against upstream rpc docs):
- newline-delimited JSON, LF-only; strip optional trailing CR
- commands: {"type": "...", "id": "..."} on stdin
- responses: {"type": "response", "id": ..., ...} + event stream on stdout
Text-generation-only (no host-tools RPC in current pi); structured output is
achieved by wrapping this port in TextPortStructuredAdapter (shared repair loop).
"""
from __future__ import annotations

import json
import subprocess
import threading
import uuid
from queue import Empty, Queue

from utag_core.repair import TerminalGenerationError

DEFAULT_CMD = ["pi", "--mode", "rpc", "--no-session"]


class PiRpcPort:
    name = "pi-rpc"

    def __init__(self, cmd: list[str] | None = None, timeout: float = 120.0):
        self._cmd = cmd or DEFAULT_CMD
        self._timeout = timeout
        self._proc: subprocess.Popen | None = None
        self._responses: Queue = Queue()

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        try:
            self._proc = subprocess.Popen(
                self._cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, bufsize=1,
            )
        except FileNotFoundError as exc:
            raise TerminalGenerationError(f"pi binary not found: {self._cmd[0]}") from exc
        threading.Thread(target=self._pump, daemon=True).start()

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def __enter__(self): self.start(); return self
    def __exit__(self, *a): self.close()

    # -- protocol ----------------------------------------------------------
    def _pump(self) -> None:
        assert self._proc and self._proc.stdout
        for line in self._proc.stdout:  # LF-delimited
            line = line.rstrip("\r\n")
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue  # non-JSON noise: ignore, never crash the pump
            if msg.get("type") == "response":
                self._responses.put(msg)
            # events (message_update etc.) intentionally dropped in v1 (YAGNI)

    def _send(self, obj: dict) -> dict:
        if not self._proc or self._proc.poll() is not None:
            raise TerminalGenerationError("pi rpc process not running")
        assert self._proc.stdin
        self._proc.stdin.write(json.dumps(obj) + "\n")
        self._proc.stdin.flush()
        want = obj["id"]
        try:
            while True:
                msg = self._responses.get(timeout=self._timeout)
                if msg.get("id") == want:
                    return msg
        except Empty:
            raise TerminalGenerationError(f"pi rpc timeout waiting for id={want}") from None

    # -- ModelPort ---------------------------------------------------------
    def complete(self, *, prompt: str, system: str | None = None,
                 feedback: str | None = None) -> str:
        full = prompt if system is None else f"{system}\n\n{prompt}"
        if feedback:
            full = f"{full}\n\n{feedback}"
        r = self._send({"type": "prompt", "id": uuid.uuid4().hex, "message": full})
        if r.get("success") is False:
            raise TerminalGenerationError(f"pi rpc prompt failed: {r.get('error')}")
        r2 = self._send({"type": "get_last_assistant_text", "id": uuid.uuid4().hex})
        text = r2.get("data") or r2.get("text") or ""
        if not isinstance(text, str):
            text = json.dumps(text)
        return text
