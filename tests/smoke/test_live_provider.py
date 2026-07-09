"""The one untested seam: a real LLM through the harness. Gated on a real key —
skips cleanly everywhere else; runs on CI push when the secret exists."""
import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"),
                                reason="ANTHROPIC_API_KEY not set")


def test_instructor_port_extracts_module_spec():
    from utag_core.ir import ModuleSpec
    from utag_generators.backends import InstructorPort

    port = InstructorPort("anthropic/claude-sonnet-4-6")
    module = port.generate(
        prompt=("Extract a data model: a Task has a title (string, required, max 200 chars), "
                "done (boolean), and priority (integer 1-5)."),
        response_model=ModuleSpec, max_attempts=3,
        system="You are a schema extraction engine.")
    assert module.types and module.types[0].fields
