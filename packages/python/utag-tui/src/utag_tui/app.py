"""utag TUI — Textual client of the control-plane.

Panels (screenshot-informed): targets navigation | live jobs table | status
panel with queue sparkline | live event log | command bar.
Commands:  generate <target> <path>   status <job-id>   refresh   quit
Config (twelve-factor): UTAG_CONTROL_PLANE_URL, UTAG_API_TOKEN.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, RichLog, Sparkline, Static, Tree

from utag_worker.worker import ControlPlane

from utag_tui.session_screen import SessionScreen

STATUS_ICON = {"queued": "○", "running": "◐", "succeeded": "●", "failed": "✗"}


class UtagTUI(App):
    TITLE = "utag — universal typed artifact generator"
    SUB_TITLE = "control-plane console"
    BINDINGS = [("r", "refresh", "Refresh"), ("c", "focus_command", "Command"),
                ("s", "session", "Session"), ("q", "quit", "Quit")]
    CSS = """
    Screen { layout: vertical; background: $surface; }
    #body { height: 1fr; }
    #nav { width: 24; border: round $primary; }
    #center { width: 1fr; }
    #jobs { height: 1fr; border: round $primary; }
    #log { height: 12; border: round $secondary; }
    #side { width: 34; }
    #status { border: round $success; padding: 0 1; height: auto; }
    #spark { height: 3; border: round $accent; }
    #cmd { dock: bottom; border: tall $primary; }
    DataTable > .datatable--cursor { background: $primary 30%; }
    """

    queue_history: reactive[list[int]] = reactive(list)

    def __init__(self, base_url: str | None = None, token: str | None = None,
                 poll_seconds: float = 1.0):
        super().__init__()
        self.cp = ControlPlane(base_url or os.environ.get("UTAG_CONTROL_PLANE_URL",
                                                          "http://127.0.0.1:8080"),
                               token if token is not None else os.environ.get("UTAG_API_TOKEN", ""))
        self.poll_seconds = poll_seconds
        self._targets: list[str] = []

    # ---------------------------------------------------------------- layout
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            yield Tree("targets", id="nav")
            with Vertical(id="center"):
                yield DataTable(id="jobs", cursor_type="row", zebra_stripes=True)
                yield RichLog(id="log", markup=True, wrap=False, max_lines=500)
            with Vertical(id="side"):
                yield Static("connecting…", id="status")
                yield Sparkline([0], id="spark")
        yield Input(placeholder="generate <target> <fixture-path> | status <id> | refresh | quit",
                    id="cmd")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#jobs", DataTable)
        table.add_columns("id", "target", "status", "backend", "updated")
        self._load_targets()
        self.refresh_jobs()
        self.set_interval(self.poll_seconds, self.refresh_jobs)

    # ---------------------------------------------------------------- data
    def _load_targets(self) -> None:
        try:
            import utag_generators  # noqa: F401
            from utag_core.registry import GENERATORS
            self._targets = sorted(GENERATORS)
        except Exception:
            self._targets = []
        tree = self.query_one("#nav", Tree)
        tree.root.expand()
        for t in self._targets:
            tree.root.add_leaf(t)

    def refresh_jobs(self) -> None:
        log = self.query_one("#log", RichLog)
        try:
            jobs = self.cp._req("GET", "/v1/jobs?limit=100") or []
        except Exception as exc:
            self.query_one("#status", Static).update(
                f"[red]control-plane unreachable[/red]\n{self.cp.base}\n{exc}")
            return
        table = self.query_one("#jobs", DataTable)
        table.clear()
        counts = {"queued": 0, "running": 0, "succeeded": 0, "failed": 0}
        for j in jobs:
            counts[j["status"]] = counts.get(j["status"], 0) + 1
            updated = j["updated_at"][11:19] if len(j.get("updated_at", "")) > 19 else ""
            table.add_row(j["id"][:8], j["target"],
                          f"{STATUS_ICON.get(j['status'], '?')} {j['status']}",
                          j.get("backend", ""), updated, key=j["id"])
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.query_one("#status", Static).update(
            f"[b]utag control-plane[/b]\n{self.cp.base}\n"
            f"── {now} ──\n"
            f"queued     {counts['queued']:>4}\nrunning    {counts['running']:>4}\n"
            f"[green]succeeded[/green]  {counts['succeeded']:>4}\n"
            f"[red]failed[/red]     {counts['failed']:>4}\n"
            f"targets    {len(self._targets):>4}")
        hist = list(self.queue_history) + [counts["queued"] + counts["running"]]
        self.queue_history = hist[-60:]
        self.query_one("#spark", Sparkline).data = self.queue_history or [0]
        if not jobs:
            log.write("[dim]no jobs yet — try: generate pydantic-models fixtures/prompts/normalize-tool.prompt.yaml[/dim]")

    # ---------------------------------------------------------------- actions
    def action_refresh(self) -> None:
        self.refresh_jobs()

    def action_session(self) -> None:
        self.push_screen(SessionScreen())

    def action_focus_command(self) -> None:
        self.query_one("#cmd", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        log = self.query_one("#log", RichLog)
        parts = event.value.strip().split()
        event.input.value = ""
        if not parts:
            return
        cmd = parts[0]
        try:
            if cmd == "quit":
                self.exit()
            elif cmd == "refresh":
                self.refresh_jobs()
            elif cmd == "status" and len(parts) == 2:
                j = self.cp._req("GET", f"/v1/jobs/{parts[1]}")
                log.write(f"[b]{j['id']}[/b] {j['target']} → {j['status']} {j.get('error', '')}")
            elif cmd == "generate" and len(parts) == 3:
                target, path = parts[1], Path(parts[2])
                if target not in self._targets:
                    log.write(f"[red]unknown target[/red] {target} — known: {', '.join(self._targets)}")
                    return
                if not path.is_file():
                    log.write(f"[red]no such input file[/red] {path}")
                    return
                j = self.cp._req("POST", "/v1/jobs", {
                    "target": target, "backend": "tui", "input_kind": "prompt-yaml",
                    "input": path.read_text()})
                log.write(f"[green]queued[/green] {j['id'][:8]} → {target} from {path.name}")
                self.refresh_jobs()
            else:
                log.write("[yellow]usage:[/yellow] generate <target> <path> | status <id> | refresh | quit")
        except Exception as exc:
            log.write(f"[red]error:[/red] {exc}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        job_id = str(event.row_key.value)
        log = self.query_one("#log", RichLog)
        try:
            arts = self.cp._req("GET", f"/v1/jobs/{job_id}/artifacts") or []
            log.write(f"[b]{job_id[:8]}[/b] artifacts: {len(arts)}")
            for a in arts:
                verdict = ""
                if a.get("report"):
                    r = json.loads(a["report"])
                    verdict = "[green]valid[/green]" if r.get("valid") else "[red]invalid[/red]"
                log.write(f"  {a['path']} {verdict}")
        except Exception as exc:
            log.write(f"[red]error:[/red] {exc}")


def main() -> int:
    UtagTUI().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
