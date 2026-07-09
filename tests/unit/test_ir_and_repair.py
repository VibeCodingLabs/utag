import pytest
from pydantic import BaseModel, ConfigDict

from utag_core.ir import FieldSpec, ModuleSpec, TypeSpec
from utag_core.repair import RepairExhausted, format_validation_errors, repair_loop


class Out(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    count: int


def test_ir_rejects_extra_properties():
    with pytest.raises(Exception):
        ModuleSpec.model_validate({"name": "m", "bogus": 1})


def test_ir_rejects_bad_field_name():
    with pytest.raises(Exception):
        FieldSpec(name="not a name!", type="string")


def test_repair_loop_succeeds_after_feedback():
    calls = []
    def call(feedback):
        calls.append(feedback)
        return '{"name": "x"}' if feedback is None else '{"name": "x", "count": 2}'
    out, attempts = repair_loop(call, Out, max_attempts=3)
    assert out.count == 2 and attempts == 2
    assert calls[0] is None and "count" in calls[1]  # feedback names the missing field


def test_repair_loop_bounded_and_exhausts():
    def call(feedback):
        return '{"name": "x"}'  # always missing count
    with pytest.raises(RepairExhausted) as ei:
        repair_loop(call, Out, max_attempts=4)
    # identical output + identical errors -> early stop at attempt 2, not 4
    assert ei.value.attempts == 2


def test_repair_never_unbounded():
    with pytest.raises(ValueError):
        repair_loop(lambda f: "{}", Out, max_attempts=99)


def test_feedback_format_actionable():
    msg = format_validation_errors([{"loc": ("count",), "msg": "Field required", "type": "missing"}])
    assert "count" in msg and "Field required" in msg
