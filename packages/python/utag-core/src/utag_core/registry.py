"""Generator + validator registries (spec: generator-registry / validator-registry).

Generation and validation are separate composable stages: a Generator only emits
artifacts; validators only judge them. Registration is decorator-based so external
packages extend UTAG without touching core (DoD dod-arch-003).
"""
from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from utag_core.ir import ModuleSpec
from utag_core.report import ValidationReport


@runtime_checkable
class Generator(Protocol):
    target: str

    def generate(self, module: ModuleSpec) -> dict[str, str]:
        """Return {relative_path: file_content}. Pure + deterministic."""
        ...


@runtime_checkable
class Importer(Protocol):
    source_format: str

    def ingest(self, content: str, source: str = "<inline>") -> ModuleSpec:
        """Return ModuleSpec parsed from the input content."""
        ...


GENERATORS: dict[str, Generator] = {}
VALIDATORS: dict[str, Callable[[str, str], ValidationReport]] = {}  # (artifact_path, content) -> report
IMPORTERS: dict[str, Importer] = {}

def register_importer(source_format: str) -> Callable[[type], type]:
    def deco(cls: type) -> type:
        inst = cls()
        inst.source_format = source_format
        if source_format in IMPORTERS:
            raise ValueError(f"duplicate importer format: {source_format}")
        IMPORTERS[source_format] = inst
        return cls
    return deco

def get_importer(source_format: str) -> Importer:
    try:
        return IMPORTERS[source_format]
    except KeyError:
        raise KeyError(f"no importer registered for format {source_format!r}; known: {sorted(IMPORTERS)}") from None



def register_generator(target: str) -> Callable[[type], type]:
    def deco(cls: type) -> type:
        inst = cls()
        inst.target = target
        if target in GENERATORS:
            raise ValueError(f"duplicate generator target: {target}")
        GENERATORS[target] = inst
        return cls
    return deco


def register_validator(kind: str) -> Callable[[Callable], Callable]:
    def deco(fn: Callable) -> Callable:
        if kind in VALIDATORS:
            raise ValueError(f"duplicate validator kind: {kind}")
        VALIDATORS[kind] = fn
        return fn
    return deco


def get_generator(target: str) -> Generator:
    try:
        return GENERATORS[target]
    except KeyError:
        raise KeyError(f"no generator registered for target {target!r}; known: {sorted(GENERATORS)}") from None


def get_validator(kind: str) -> Callable[[str, str], ValidationReport]:
    try:
        return VALIDATORS[kind]
    except KeyError:
        raise KeyError(f"no validator registered for kind {kind!r}; known: {sorted(VALIDATORS)}") from None
