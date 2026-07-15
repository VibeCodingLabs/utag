"""omp-style model picker: provider row (tab cycles), type-to-filter list,
enter selects and persists provider/model to ~/.utag/config.yaml."""
from __future__ import annotations

import yaml
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Static

from agent_harness import UtagHome, load_catalog, models

FEATURED = ["anthropic", "openai", "google", "openrouter", "groq", "deepseek",
            "mistral", "xai", "cerebras", "huggingface"]


class ModelPicker(ModalScreen[str]):
    BINDINGS = [("escape", "dismiss('')", "Close"), ("tab", "cycle", "Provider")]
    CSS = """
    ModelPicker { align: center middle; }
    #box { width: 96; height: 30; border: thick $primary; background: $surface; padding: 1; }
    #providers { height: 2; color: $accent; }
    #filter { border: tall $accent; }
    #list { height: 1fr; }
    """

    def __init__(self, home: UtagHome | None = None):
        super().__init__()
        self.home = home or UtagHome.resolve()
        self.catalog = load_catalog(self.home.global_dir / "cache")
        avail = [p for p in FEATURED if p in self.catalog]
        self.providers = ["all"] + (avail or sorted(self.catalog)[:10])
        self.pidx = 1 if len(self.providers) > 1 else 0

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical
        with Vertical(id="box"):
            yield Static(id="providers")
            yield Input(placeholder="type to filter — tab cycles providers, enter selects", id="filter")
            yield DataTable(id="list", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#list", DataTable)
        table.add_columns("provider", "model", "ctx", "out", "$in/$out", "modalities", "R", "T")
        self._refresh_list()
        self.query_one("#filter", Input).focus()

    def _refresh_list(self, query: str = "") -> None:
        prov = self.providers[self.pidx]
        self.query_one("#providers", Static).update(
            "Models:  " + "  ".join(f"[reverse] {p.upper()} [/reverse]" if i == self.pidx
                                    else p.upper() for i, p in enumerate(self.providers))
            + "   (tab to cycle)")
        table = self.query_one("#list", DataTable)
        table.clear()
        for m in models(self.catalog, provider="" if prov == "all" else prov,
                        query=query, tool_call_only=True, limit=60):
            table.add_row(*m.row(), key=f"{m.provider}:{m.id}")

    def action_cycle(self) -> None:
        self.pidx = (self.pidx + 1) % len(self.providers)
        self._refresh_list(self.query_one("#filter", Input).value)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        table = self.query_one("#list", DataTable)
        if table.row_count:
            table.focus()
            self._select(table.coordinate_to_cell_key((table.cursor_row, 0)).row_key)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._select(event.row_key)

    def _select(self, row_key) -> None:
        choice = str(row_key.value)
        provider, model_id = choice.split(":", 1)
        cfg_path = self.home.global_dir / "config.yaml"
        cfg = yaml.safe_load(cfg_path.read_text()) if cfg_path.is_file() else {}
        cfg = cfg or {}
        cfg["provider"], cfg["model"] = provider, model_id
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        self.dismiss(choice)
