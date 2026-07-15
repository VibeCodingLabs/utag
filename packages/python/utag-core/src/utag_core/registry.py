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

#: (kind, id) -> manifest (utag_core.schemas.core.RegistryManifest subclass).
#: Populated at registration: explicit `manifest=` wins, else derived — generators
#: and validators are covered by the golden/conformance suites that parametrize
#: over every registered id, so derived manifests cite those suites.
MANIFESTS: dict[tuple[str, str], object] = {}


def _derived_manifest(kind: str, id_: str):
    from utag_core.schemas.core import (
        GeneratorManifest, ImporterManifest, ValidatorManifest,
    )
    if kind == "generator":
        return GeneratorManifest(
            id=id_, name=id_, version="1.0.0", input_schema="module-spec",
            entrypoints=[f"utag generate --target {id_}"],
            test_files=["tests/golden/test_determinism.py",
                        "tests/conformance/test_fixture_pipeline.py"],
            validation_gates=["golden", "conformance"])
    if kind == "validator":
        return ValidatorManifest(
            id=id_, name=id_, version="1.0.0",
            entrypoints=[f"utag validate --kind {id_}"],
            test_files=["tests/conformance/test_fixture_pipeline.py"],
            validation_gates=["conformance"])
    return ImporterManifest(
        id=id_, name=id_, version="1.0.0", output_schema="module-spec",
        entrypoints=[f"utag_core.registry.get_importer({id_!r}).ingest(...)"],
        test_files=["tests/unit/test_p2_importers.py"],
        validation_gates=["unit"])


def _record_manifest(kind: str, id_: str, manifest: object | None) -> None:
    MANIFESTS[(kind, id_)] = manifest if manifest is not None else _derived_manifest(kind, id_)


def register_importer(source_format: str, manifest: object | None = None) -> Callable[[type], type]:
    def deco(cls: type) -> type:
        inst = cls()
        inst.source_format = source_format
        if source_format in IMPORTERS:
            raise ValueError(f"duplicate importer format: {source_format}")
        IMPORTERS[source_format] = inst
        _record_manifest("importer", source_format, manifest)
        return cls
    return deco

def get_importer(source_format: str) -> Importer:
    try:
        return IMPORTERS[source_format]
    except KeyError:
        raise KeyError(f"no importer registered for format {source_format!r}; known: {sorted(IMPORTERS)}") from None



def register_generator(target: str, manifest: object | None = None) -> Callable[[type], type]:
    def deco(cls: type) -> type:
        inst = cls()
        inst.target = target
        if target in GENERATORS:
            raise ValueError(f"duplicate generator target: {target}")
        GENERATORS[target] = inst
        _record_manifest("generator", target, manifest)
        return cls
    return deco


def register_validator(kind: str, manifest: object | None = None) -> Callable[[Callable], Callable]:
    def deco(fn: Callable) -> Callable:
        if kind in VALIDATORS:
            raise ValueError(f"duplicate validator kind: {kind}")
        VALIDATORS[kind] = fn
        _record_manifest("validator", kind, manifest)
        return fn
    return deco


def get_manifest(kind: str, id_: str):
    try:
        return MANIFESTS[(kind, id_)]
    except KeyError:
        raise KeyError(f"no manifest for {kind} {id_!r}") from None


def registry_problems(root) -> list[str]:
    """Doctor: every registered id needs a manifest with entrypoints and existing test files."""
    from pathlib import Path
    root = Path(root)
    problems = []
    registered = ([("generator", t) for t in GENERATORS] +
                  [("validator", k) for k in VALIDATORS] +
                  [("importer", f) for f in IMPORTERS])
    for kind, id_ in sorted(registered):
        m = MANIFESTS.get((kind, id_))
        if m is None:
            problems.append(f"{kind} {id_}: no manifest")
            continue
        if not m.entrypoints:
            problems.append(f"{kind} {id_}: manifest lists no entrypoints")
        if not m.test_files:
            problems.append(f"{kind} {id_}: manifest lists no test files")
        problems += [f"{kind} {id_}: test file missing: {tf}"
                     for tf in m.test_files if not (root / tf).is_file()]
    return problems


def coverage_report() -> str:
    """Deterministic markdown coverage matrix over all registered manifests."""
    lines = ["# Registry coverage", "",
             "| kind | id | status | entrypoints | test files | gates |",
             "|---|---|---|---|---|---|"]
    for (kind, id_), m in sorted(MANIFESTS.items()):
        lines.append(f"| {kind} | {id_} | {m.status.value} | {len(m.entrypoints)} "
                     f"| {len(m.test_files)} | {', '.join(m.validation_gates)} |")
    counts = {}
    for kind, _ in MANIFESTS:
        counts[kind] = counts.get(kind, 0) + 1
    totals = ", ".join(f"{v} {k}s" for k, v in sorted(counts.items()))
    lines += ["", f"Total: {totals}."]
    return "\n".join(lines) + "\n"


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
