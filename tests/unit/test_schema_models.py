"""Schema strictness: every kind rejects unknown props, accepts `extensions`."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from utag_core.schemas import EXAMPLES, SCHEMAS


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_example_validates(kind):
    SCHEMAS[kind].model_validate(EXAMPLES[kind])


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_unknown_property_rejected(kind):
    payload = dict(EXAMPLES[kind])
    payload["__unknown_property__"] = True
    with pytest.raises(ValidationError):
        SCHEMAS[kind].model_validate(payload)


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_extensions_escape_hatch_accepted(kind):
    payload = dict(EXAMPLES[kind])
    payload["extensions"] = {"vendor": {"private": True}}
    SCHEMAS[kind].model_validate(payload)


def test_every_schema_has_example():
    assert set(SCHEMAS) == set(EXAMPLES)
