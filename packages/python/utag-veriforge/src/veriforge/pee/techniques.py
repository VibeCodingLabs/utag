"""Technique registry loader with honest completeness gate (WARN until 58/58)."""
from __future__ import annotations
import logging
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

log = logging.getLogger("veriforge.pee")

PHASE_ORDER = ["framing", "context", "reasoning", "decomposition", "ensembling", "self_criticism"]


class TechniqueSpec(BaseModel):
    id: str
    category: str
    phase: str
    trigger: dict = Field(default_factory=dict)
    cost: float = 1.0                                 # token/latency multiplier vs plain prompt


class TechniqueRegistry(BaseModel):
    expected_count: int
    techniques: list[TechniqueSpec]

    @property
    def complete(self) -> bool:
        return len(self.techniques) >= self.expected_count


def load_registry(path: str | Path | None = None) -> TechniqueRegistry:
    path = Path(path) if path else Path(__file__).parent / "taxonomy.yaml"
    data = yaml.safe_load(path.read_text())
    reg = TechniqueRegistry(expected_count=data["expected_count"],
                            techniques=[TechniqueSpec(**t) for t in data["techniques"]])
    if not reg.complete:
        gap = reg.expected_count - len(reg.techniques)
        log.warning("technique registry %d/%d — reconcile %d entries against arXiv 2406.06608 §2.2",
                    len(reg.techniques), reg.expected_count, gap)
    return reg
