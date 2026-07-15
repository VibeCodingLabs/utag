"""AskUserQuestions in the TUI: ClarifyScreen shows one clarifying question at a time
(2-4 tap-able options + free-text escape, <=3 per round), and tui_clarify runs the
ambiguity-gate loop against it — same semantics/constants as veriforge's clarify_loop
(score -> ask -> merge -> re-score until threshold/max_rounds; residual gaps become
explicit assumptions), awaited instead of blocking. Parity is pinned by test."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Static

from veriforge.core.schemas import ClarifiedTask, ClarifyingQuestion, TaskSpec
from veriforge.intake.ambiguity import (DEFAULT_THRESHOLD, MAX_ROUNDS,
                                        QUESTIONS_PER_ROUND, Scorer)


class ClarifyScreen(ModalScreen[dict]):
    """One round of AskUserQuestions: wizard over <=3 questions; option tap or typed
    answer advances; Esc skips the remaining questions (they become assumptions)."""

    BINDINGS = [("escape", "dismiss({})", "Skip")]
    CSS = """
    ClarifyScreen { align: center middle; }
    #panel { width: 80; height: 20; border: thick $primary; background: $surface; padding: 1; }
    #question { height: 3; color: $accent; }
    #options { height: 1fr; }
    #free { border: tall $accent; }
    """

    def __init__(self, questions: list[ClarifyingQuestion]):
        super().__init__()
        self.questions = questions
        self.qidx = 0
        self.answers: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="panel"):
            yield Static(id="question")
            yield OptionList(id="options")
            yield Input(placeholder="or type an answer — enter submits, esc skips all", id="free")

    def on_mount(self) -> None:
        self._show_question()

    def _show_question(self) -> None:
        q = self.questions[self.qidx]
        n = len(self.questions)
        self.query_one("#question", Static).update(
            f"[{self.qidx + 1}/{n}] ({q.dimension.value}) {q.question}")
        opts = self.query_one("#options", OptionList)
        opts.clear_options()
        opts.add_options(q.options or ["(no options — type below)"])
        opts.highlighted = 0                       # deterministic: enter selects first option
        self.query_one("#free", Input).value = ""
        opts.focus()

    def _record(self, answer: str) -> None:
        if answer.strip():
            self.answers[self.questions[self.qidx].question] = answer.strip()
        self.qidx += 1
        if self.qidx >= len(self.questions):
            self.dismiss(self.answers)
        else:
            self._show_question()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self._record(str(event.option.prompt))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._record(event.value)


async def tui_clarify(screen, task: TaskSpec, scorer: Scorer,
                      threshold: float = DEFAULT_THRESHOLD,
                      max_rounds: int = MAX_ROUNDS) -> ClarifiedTask:
    """Async mirror of veriforge.intake.ambiguity.clarify_loop with ClarifyScreen as
    the Asker. Must stay behaviour-identical to the sync loop (parity test pins it)."""
    answers: dict[str, str] = {}
    report = scorer.score(task, answers)
    rounds = 0
    while report.overall < threshold and rounds < max_rounds and report.open_questions:
        batch = report.open_questions[:QUESTIONS_PER_ROUND]
        got = await screen.app.push_screen_wait(ClarifyScreen(batch))
        answers.update(got or {})
        report = scorer.score(task, answers)
        rounds += 1
        if not got:               # user skipped the whole round: stop asking, log gaps
            break
    assumptions = ([f"UNRESOLVED[{q.dimension.value}]: {q.question} — proceeding with default"
                    for q in report.open_questions] if report.overall < threshold else [])
    return ClarifiedTask(task=task, answers=answers,
                         assumptions=assumptions, final_ambiguity=report.overall)
