"""Session screen — run utag like Claude Code: transcript + prompt bar.

Model selection: config.yaml provider/model + stored credential exported to the
provider's env var (from the catalog) -> pydantic-ai infers the client. Falls
back to an offline notice when no credential exists. `model` may be injected
for tests (TestModel)."""
from __future__ import annotations

import os
from typing import Any

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog

from agent_harness import Session, UtagHome, load_catalog, provider_env, session_toolset


def build_model(home: UtagHome) -> Any | None:
    cfg = home.config()
    provider, model_id = cfg.get("provider", "anthropic"), cfg.get("model", "claude-sonnet-4-6")
    key = home.get_credential(provider)
    if not key:
        return None
    try:
        for env in provider_env(load_catalog(home.global_dir / "cache"), provider) or []:
            os.environ.setdefault(env, key)
    except Exception:
        pass
    return f"{provider}:{model_id}"  # pydantic-ai provider:model string


class SessionScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Dashboard"), ("m", "pick_model", "Model"), ("c", "clarify", "Clarify")]
    CSS = """
    #transcript { height: 1fr; border: round $primary; padding: 0 1; }
    #prompt { dock: bottom; border: tall $accent; }
    """

    def __init__(self, home: UtagHome | None = None, model: Any = None):
        super().__init__()
        self.home = home or UtagHome.resolve()
        self.home.init_scaffold()
        self._model = model or build_model(self.home)
        self.session: Session | None = None
        self._tools, self._cp = session_toolset(self.home, model=self._model)
        self._watching: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(id="transcript", markup=True, wrap=True, max_lines=2000)
        yield Input(placeholder="talk to utag — /help for commands, /skills for the index, Esc for dashboard",
                    id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#transcript", RichLog)
        log.write("[b]utag session[/b] — expert harness. Skills lazy-load; /help lists everything.")
        if self._model is None:
            log.write("[yellow]no credential for the configured provider — run:[/yellow] "
                      "utag login <provider>   (session commands like /help, /skills, /models still work)")
        else:
            self.session = Session(home=self.home, model=self._model, extra_tools=self._tools)
        if self.session is None:  # local-only session still routes slash commands
            from pydantic_ai.models.test import TestModel
            self.session = Session(home=self.home, model=TestModel(
                custom_output_text="(no provider credential — model calls disabled; /help works)"),
                extra_tools=self._tools)
            self.session_local_only = True
        self.query_one("#prompt", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        event.input.value = ""
        if not raw:
            return
        log = self.query_one("#transcript", RichLog)
        log.write(f"[b cyan]you[/b cyan] {raw}")
        try:
            out = await self.session.turn(raw)
            log.write(f"[b green]utag[/b green] {out}")
            self._watch_new_jobs(log)
        except Exception as exc:
            log.write(f"[red]error:[/red] {exc}")

    # -- live observability: any job the session created gets a watcher --------
    def _watch_new_jobs(self, log) -> None:
        if self._cp is None:
            return
        import re
        blob = " ".join(str(m.get("content", "")) for m in self.session.transcript[-4:])
        for jid in set(re.findall(r"job_id['\"]?[:=]\s*['\"]([0-9a-f-]{8,})", blob)):
            if jid not in self._watching:
                self._watching.add(jid)
                self.run_worker(self._watch_job(jid), exclusive=False)

    async def _watch_job(self, job_id: str) -> None:
        import asyncio
        log = self.query_one("#transcript", RichLog)
        log.write(f"[dim]watching job {job_id[:8]}…[/dim]")
        last = ""
        for _ in range(240):  # <= 2 min at 0.5s
            await asyncio.sleep(0.5)
            try:
                j = self._cp._req("GET", f"/v1/jobs/{job_id}")
            except Exception:
                continue
            if j["status"] != last:
                last = j["status"]
                log.write(f"[dim]job {job_id[:8]} → {last}[/dim]")
            if last in ("succeeded", "failed"):
                arts = self._cp._req("GET", f"/v1/jobs/{job_id}/artifacts") or []
                verdicts = sum(1 for a in arts if a.get("report") and '"valid": true' in a["report"])
                colour = "green" if last == "succeeded" else "red"
                log.write(f"[{colour}]job {job_id[:8]} {last}[/{colour}] — "
                          f"{len(arts)} artifacts, {verdicts} valid" +
                          (f" — {j.get('error')}" if j.get("error") else ""))
                return


    def action_pick_model(self) -> None:
        from utag_tui.model_picker import ModelPicker

        def _chosen(choice: str) -> None:
            if choice:
                log = self.query_one("#transcript", RichLog)
                log.write(f"[b]model set:[/b] {choice} — restart session screen to apply")
        self.app.push_screen(ModelPicker(home=self.home), _chosen)


    def action_clarify(self) -> None:
        """AskUserQuestions over the current prompt-bar text: ambiguity gate -> modal
        rounds -> ClarifiedTask summary into the transcript."""
        goal = self.query_one("#prompt", Input).value.strip()
        log = self.query_one("#transcript", RichLog)
        if not goal:
            log.write("[dim]type a goal in the prompt bar, then press c to clarify[/dim]")
            return
        self.run_worker(self._clarify(goal), exclusive=False)

    async def _clarify(self, goal: str) -> None:
        from agent_harness.veriforge_bridge import HeuristicScorer
        from utag_tui.clarify_screen import tui_clarify
        from veriforge.core.schemas import TaskSpec
        log = self.query_one("#transcript", RichLog)
        clarified = await tui_clarify(self, TaskSpec(goal=goal), HeuristicScorer())
        log.write(f"[b]clarified[/b] ambiguity={clarified.final_ambiguity:.2f}")
        for q, a in clarified.answers.items():
            log.write(f"  [green]A[/green] {q} -> {a}")
        for s in clarified.assumptions:
            log.write(f"  [yellow]![/yellow] {s}")
