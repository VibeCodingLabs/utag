"""Conformance: the user's 4 real prompt YAMLs -> IR -> every target -> validator green."""
import json
from pathlib import Path

import pytest

import utag_generators  # noqa: F401
from utag_core.registry import get_generator, get_validator
from utag_generators.ingest import ingest_prompt_yaml
from utag_generators.targets.prompt_yaml import PromptFile

FIXTURES = Path(__file__).parents[2] / "fixtures" / "prompts"
PROMPTS = sorted(FIXTURES.glob("*.prompt.yaml"))
TARGET_VALIDATOR = {
    "pydantic-models": "python-source", "zod-schemas": "typescript",
    "agent-skill": "skill-md", "prompt-yaml": "yaml", "openapi-3.1": "openapi-3.1",
    "design-md": "design-md", "go-harness": "go-source",
}


def test_fixtures_present():
    assert len(PROMPTS) == 4, [p.name for p in PROMPTS]


@pytest.mark.parametrize("fixture", PROMPTS, ids=lambda p: p.stem)
def test_prompt_yaml_roundtrip(fixture):
    pf = PromptFile.parse(fixture.read_text())
    again = PromptFile.parse(pf.to_yaml())
    assert again == pf  # lossless round-trip


@pytest.mark.parametrize("fixture", PROMPTS, ids=lambda p: p.stem)
@pytest.mark.parametrize("target", sorted(TARGET_VALIDATOR))
def test_every_fixture_through_every_target(fixture, target):
    module = ingest_prompt_yaml(fixture.read_text(), str(fixture))
    assert module.provenance["sha256"]  # provenance preserved (spec: IR preservation)
    gen = get_generator(target)
    files = gen.generate(module)
    assert files
    v = get_validator(TARGET_VALIDATOR[target])
    for rel, content in files.items():
        report = v(rel, content)
        assert report.valid, report.to_json()


def test_openapi_operation_ids_unique():
    module = ingest_prompt_yaml(PROMPTS[0].read_text())
    doc = json.loads(next(iter(get_generator("openapi-3.1").generate(module).values())))
    ids = [op["operationId"] for p in doc["paths"].values() for op in p.values()]
    assert len(ids) == len(set(ids))
