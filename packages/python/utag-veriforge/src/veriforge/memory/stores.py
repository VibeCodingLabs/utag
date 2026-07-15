"""Memory protocols only — backend chosen by first real retrieval need (YAGNI).
Dual retrieval per AgentForge §III.C: episodic (cross-task) + repo index (intra-task)."""
from __future__ import annotations
from typing import Protocol
from pydantic import BaseModel


class Episode(BaseModel):
    task_goal: str
    patch_diff: str


class MemoryStore(Protocol):
    def store(self, episode: Episode) -> None: ...
    def top_k(self, query: str, k: int = 5) -> list[Episode]: ...


class RepoIndex(Protocol):
    def top_k_files(self, query: str, k: int = 5) -> list[str]: ...
