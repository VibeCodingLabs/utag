"""Ambiguity Gate: score -> AskUserQuestions -> merge -> re-score, until threshold or max rounds.
Residual gaps become explicit assumptions — never silent."""
from __future__ import annotations
from typing import Protocol
from ..core.schemas import (AmbiguityReport, ClarifiedTask, ClarifyingQuestion, TaskSpec)

DEFAULT_THRESHOLD = 0.85     # weakest dimension must clear this
MAX_ROUNDS = 3
QUESTIONS_PER_ROUND = 3      # respects platform AskUserQuestions ceiling


class Asker(Protocol):
    """Maps to the platform AskUserQuestions / ask_user_input tool; CLI impl below."""
    def ask(self, questions: list[ClarifyingQuestion]) -> dict[str, str]: ...


class Scorer(Protocol):
    """Typed agent in prod (swappable binding); deterministic fake in tests."""
    def score(self, task: TaskSpec, answers: dict[str, str]) -> AmbiguityReport: ...


class CliAsker:
    def ask(self, questions: list[ClarifyingQuestion]) -> dict[str, str]:
        answers: dict[str, str] = {}
        for q in questions:
            opts = f" [{' | '.join(q.options)}]" if q.options else ""
            answers[q.question] = input(f"{q.question}{opts}\n> ").strip()
        return answers


def clarify_loop(task: TaskSpec, scorer: Scorer, asker: Asker,
                 threshold: float = DEFAULT_THRESHOLD,
                 max_rounds: int = MAX_ROUNDS) -> ClarifiedTask:
    answers: dict[str, str] = {}
    report = scorer.score(task, answers)
    rounds = 0
    while report.overall < threshold and rounds < max_rounds and report.open_questions:
        batch = report.open_questions[:QUESTIONS_PER_ROUND]
        answers.update(asker.ask(batch))
        report = scorer.score(task, answers)
        rounds += 1
    assumptions = ([f"UNRESOLVED[{q.dimension.value}]: {q.question} — proceeding with default"
                    for q in report.open_questions] if report.overall < threshold else [])
    return ClarifiedTask(task=task, answers=answers,
                         assumptions=assumptions, final_ambiguity=report.overall)
