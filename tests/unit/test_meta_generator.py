"""The moat: UTAG generates a generator, registers it, and the new generator generates."""
import pytest

from utag_core.ir import FieldSpec, ModuleSpec, TypeSpec
from utag_core.registry import GENERATORS, get_generator, get_validator
from utag_generators.meta import GeneratorSpec, OutputRule, emit_generator


def _spec(target="csv-manifest"):
    return GeneratorSpec(
        target=target, class_name="CsvManifestGenerator",
        doc="Emit a one-line-per-type CSV manifest of a module.",
        output=OutputRule(filename_template="{module}.csv",
                          line_template="{type_name},{field_names}",
                          header="type,fields"),
    )


def test_spec_rejects_builtin_collision():
    with pytest.raises(Exception):
        _spec(target="pydantic-models")


def test_generated_generator_is_valid_registrable_and_generates(tmp_path):
    files = emit_generator(_spec())
    src = files["utag_gen_csv_manifest.py"]
    # 1) emitted module passes the python-source validator (validation stage decoupled)
    assert get_validator("python-source")("utag_gen_csv_manifest.py", src).valid
    # 2) exec it -> registers itself through the public registry API
    assert "csv-manifest" not in GENERATORS
    exec(compile(src, "utag_gen_csv_manifest.py", "exec"), {})
    assert "csv-manifest" in GENERATORS
    # 3) the freshly minted generator generates, deterministically
    m = ModuleSpec(name="tools", types=[TypeSpec(name="Tool", fields=[
        FieldSpec(name="id", type="string"), FieldSpec(name="slug", type="string")])])
    g = get_generator("csv-manifest")
    out = g.generate(m)
    assert out == g.generate(m)
    assert out["tools.csv"] == "type,fields\nTool,id, slug\n".replace("id, slug", "id, slug")
    assert "Tool" in out["tools.csv"]
    GENERATORS.pop("csv-manifest")  # isolation


def test_meta_emits_its_own_test():
    files = emit_generator(_spec())
    assert any(k.startswith("test_") for k in files)
    test_src = files["test_utag_gen_csv_manifest.py"]
    assert get_validator("python-source")("t.py", test_src).valid
