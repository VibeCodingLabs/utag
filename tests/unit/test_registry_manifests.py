"""Every registered generator/validator/importer must carry a valid manifest."""
from __future__ import annotations

from pathlib import Path

import pytest

import utag_generators  # noqa: F401  registers everything
from utag_core.registry import (
    GENERATORS, IMPORTERS, MANIFESTS, VALIDATORS,
    get_manifest, register_generator, registry_problems,
)
from utag_core.schemas.core import GeneratorManifest, RegistryKind

ROOT = Path(__file__).resolve().parents[2]


def test_every_registration_has_manifest():
    for target in GENERATORS:
        assert get_manifest("generator", target).kind == RegistryKind.generator
    for kind in VALIDATORS:
        assert get_manifest("validator", kind).kind == RegistryKind.validator
    for fmt in IMPORTERS:
        assert get_manifest("importer", fmt).kind == RegistryKind.importer


def test_manifests_list_entrypoints_and_existing_tests():
    for (kind, id_), m in MANIFESTS.items():
        assert m.entrypoints, f"{kind} {id_}: no entrypoints"
        assert m.test_files, f"{kind} {id_}: no test files"
        for tf in m.test_files:
            assert (ROOT / tf).is_file(), f"{kind} {id_}: missing test file {tf}"


def test_registry_doctor_clean():
    assert registry_problems(ROOT) == []


def test_explicit_manifest_overrides_derived():
    manifest = GeneratorManifest(
        id="tmp-explicit", name="Temp", version="0.0.1",
        entrypoints=["utag generate --target tmp-explicit"],
        test_files=["tests/unit/test_registry_manifests.py"],
        validation_gates=["unit"])

    @register_generator("tmp-explicit", manifest=manifest)
    class TmpGen:
        def generate(self, module):
            return {}

    try:
        assert get_manifest("generator", "tmp-explicit") is manifest
    finally:
        GENERATORS.pop("tmp-explicit")
        MANIFESTS.pop(("generator", "tmp-explicit"))


def test_unknown_manifest_raises():
    with pytest.raises(KeyError):
        get_manifest("generator", "does-not-exist")
