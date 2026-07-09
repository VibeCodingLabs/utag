"""Golden: identical inputs -> byte-identical artifacts, stable hashes, no timestamps."""
import hashlib
import re
from pathlib import Path

import pytest

import utag_generators  # noqa: F401
from utag_core.registry import GENERATORS, get_generator
from utag_generators.ingest import ingest_prompt_yaml

FIXTURES = Path(__file__).parents[2] / "fixtures" / "prompts"
FIXTURE = (FIXTURES / "normalize-tool.prompt.yaml").read_text()
TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")


@pytest.mark.parametrize("target", sorted(t for t in GENERATORS if t != "generator"))
def test_double_generation_identical(target):
    m1 = ingest_prompt_yaml(FIXTURE)
    m2 = ingest_prompt_yaml(FIXTURE)
    a = get_generator(target).generate(m1)
    b = get_generator(target).generate(m2)
    ha = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in a.items()}
    hb = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in b.items()}
    assert ha == hb


@pytest.mark.parametrize("target", sorted(t for t in GENERATORS if t != "generator"))
def test_no_timestamps_in_artifacts(target):
    module = ingest_prompt_yaml(FIXTURE)
    for content in get_generator(target).generate(module).values():
        assert not TS_RE.search(content), "deterministic artifacts must not embed timestamps"
