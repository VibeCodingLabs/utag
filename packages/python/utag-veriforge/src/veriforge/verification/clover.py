"""Clover-style consistency checks (Sun et al.): correctness ~ pairwise consistency of
code <-> tests <-> docstring <-> spec. Formal-verifier slot optional (Dafny/Verus adapter)."""
from __future__ import annotations
from typing import Protocol
from pydantic import BaseModel, Field
from ..core.schemas import ExecutionResult


class ConsistencyEdge(BaseModel):
    edge: str                # e.g. "code<->tests", "code->docstring"
    passed: bool
    evidence: str = ""


class ConsistencyReport(BaseModel):
    edges: list[ConsistencyEdge] = Field(min_length=1)

    @property
    def accepted(self) -> bool:              # Clover: accept only if ALL edges pass
        return all(e.passed for e in self.edges)


class FormalVerifier(Protocol):
    """Adapter slot: Dafny / Verus / property-based fallback. Optional per language."""
    def verify(self, workdir: str) -> ExecutionResult: ...


def code_tests_edge(result: ExecutionResult) -> ConsistencyEdge:
    """Strongest edge: actual execution — code satisfies tests (Clover 'anno-sound' analog)."""
    return ConsistencyEdge(edge="code<->tests", passed=result.passed,
                           evidence=(result.stdout or result.stderr)[-500:])
