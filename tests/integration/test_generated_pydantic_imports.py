"""Generated Pydantic source must import and enforce constraints at runtime."""
import importlib.util
import sys

import pytest
from pydantic import ValidationError

from utag_core.ir import Constraint, FieldSpec, ModuleSpec, ScalarKind, TypeSpec
from utag_core.registry import get_generator


def test_generated_model_enforces_constraints(tmp_path):
    module = ModuleSpec(name="users", types=[TypeSpec(name="User", fields=[
        FieldSpec(name="email", type=ScalarKind.string,
                  constraints=[Constraint(kind="pattern", value=r"^[^@]+@[^@]+$")]),
        FieldSpec(name="age", type=ScalarKind.integer,
                  constraints=[Constraint(kind="ge", value=0), Constraint(kind="le", value=150)]),
        FieldSpec(name="tags", type=ScalarKind.string, array=True, required=False),
    ])])
    files = get_generator("pydantic-models").generate(module)
    src_path = tmp_path / "users.py"
    src_path.write_text(files["users.py"])
    spec = importlib.util.spec_from_file_location("users_gen", src_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["users_gen"] = spec.loader.exec_module(mod) or mod
    User = mod.User
    u = User(email="a@b.co", age=30)
    assert u.tags is None
    with pytest.raises(ValidationError):
        User(email="not-an-email", age=30)
    with pytest.raises(ValidationError):
        User(email="a@b.co", age=200)
    with pytest.raises(ValidationError):
        User(email="a@b.co", age=30, extra_field=1)  # strict
