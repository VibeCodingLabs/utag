"""Error taxonomy + routing — table transcribed from 20_error_taxonomy_routing.md."""
from __future__ import annotations
import re
from .schemas import ErrorClass, ExecutionResult, RoutedError

ROUTING: dict[ErrorClass, RoutedError] = {
    ErrorClass.syntax_type: RoutedError(
        error_class=ErrorClass.syntax_type,
        context_strategy="error message + offending file + types",
        handler="deterministic fast path (no LLM)",
        escalation="only if fast path fails"),
    ErrorClass.logic: RoutedError(
        error_class=ErrorClass.logic,
        context_strategy="failing test (expected vs actual) + implementation + spec",
        handler="LLM medium focused context",
        escalation="after 3 attempts"),
    ErrorClass.design: RoutedError(
        error_class=ErrorClass.design,
        context_strategy="original spec + architecture + interface contracts + implementation",
        handler="LLM broad context",
        escalation="often needs human input"),
    ErrorClass.performance: RoutedError(
        error_class=ErrorClass.performance,
        context_strategy="profiling data + benchmarks + code",
        handler="specialist optimization agent",
        escalation="if regression >2x"),
    ErrorClass.security: RoutedError(
        error_class=ErrorClass.security,
        context_strategy="static analysis results + secure pattern reference",
        handler="conservative fix prompt",
        escalation="ALWAYS flag for review"),
    ErrorClass.environment: RoutedError(
        error_class=ErrorClass.environment,
        context_strategy="environment config + recent dep changes + error output",
        handler="specialized env context",
        escalation="if not auto-resolved"),
    ErrorClass.flaky_test: RoutedError(
        error_class=ErrorClass.flaky_test,
        context_strategy="run test multiple times to confirm flakiness",
        handler="QUARANTINE — never trigger a fix cycle",
        escalation="infrastructure agent"),
}

_SYNTAX = re.compile(r"\b(SyntaxError|IndentationError|TypeError|NameError|ImportError|ModuleNotFoundError)\b")
_ENV = re.compile(r"\b(No such file|Connection refused|pip|EnvironmentError|version conflict|command not found)\b", re.I)


def classify(result: ExecutionResult, *, phase: str = "test", reruns_inconsistent: bool = False) -> RoutedError:
    """Classify → route. Deterministic; LLM never classifies its own failures."""
    if reruns_inconsistent:
        return ROUTING[ErrorClass.flaky_test]
    blob = result.stderr + result.stdout
    if phase in ("build", "startup") and _ENV.search(blob):     # env errors surface pre-test
        return ROUTING[ErrorClass.environment]
    if _SYNTAX.search(blob):
        return ROUTING[ErrorClass.syntax_type]
    return ROUTING[ErrorClass.logic]                             # default: failing test = logic
