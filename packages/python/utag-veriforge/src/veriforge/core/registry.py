"""One generic registry; six instantiations: Agents, Tools, Skills, Hooks, Commands, Jobs."""
from __future__ import annotations
from typing import Callable, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class Registry(Generic[T]):
    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._items: dict[str, T] = {}

    def register(self, name: str, item: T) -> None:
        if name in self._items:
            raise ValueError(f"{self.kind} '{name}' already registered")
        self._items[name] = item

    def get(self, name: str) -> T:
        return self._items[name]

    def list(self) -> list[str]:
        return sorted(self._items)


class ToolSpec(BaseModel):
    """Pydantic-typed callable: schema is the contract the LLM sees."""
    model_config = {"arbitrary_types_allowed": True}
    name: str
    description: str                                 # the LLM's UX — write for the model
    input_schema: type[BaseModel]
    fn: Callable


class SkillSpec(BaseModel):
    name: str
    path: str                                        # folder: SKILL.md + assets
    triggers: list[str] = Field(default_factory=list)


class CommandSpec(BaseModel):
    name: str                                        # user-invocable: /audit, /ship ...
    description: str
    entrypoint: str


class JobSpec(BaseModel):
    name: str
    schedule: str                                    # cron expr or event name
    task_ref: str
