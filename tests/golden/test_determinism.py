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
UDC_DIR = Path(__file__).parents[2] / "fixtures" / "kits" / "udc"
TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")


def _module(target: str):
    """Each generator gets its contractual input shape (udc-* consume a UDC doc)."""
    if target == "taxonomy-skill":
        from utag_core.ir import ModuleSpec
        tax = (Path(__file__).parents[2] / "fixtures/kits/taxonomies/master_mapped_taxonomy.md").read_text()
        return ModuleSpec(name="tax", provenance={"taxonomy_md": tax, "tools": "job_repo_audit"})
    if target.startswith("udc-"):
        import json
        from utag_core.ir import ModuleSpec
        from utag_generators.targets.udc import assemble
        return ModuleSpec(name="acme_design", description="UDC-derived",
                          provenance={"udc_json": json.dumps(assemble(UDC_DIR), sort_keys=True)})
    return ingest_prompt_yaml(FIXTURE)


@pytest.mark.parametrize("target", sorted(t for t in GENERATORS if t != "generator"))
def test_double_generation_identical(target):
    a = get_generator(target).generate(_module(target))
    b = get_generator(target).generate(_module(target))
    ha = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in a.items()}
    hb = {k: hashlib.sha256(v.encode()).hexdigest() for k, v in b.items()}
    assert ha == hb


@pytest.mark.parametrize("target", sorted(t for t in GENERATORS if t != "generator"))
def test_no_timestamps_in_artifacts(target):
    for content in get_generator(target).generate(_module(target)).values():
        assert not TS_RE.search(content), "deterministic artifacts must not embed timestamps"
