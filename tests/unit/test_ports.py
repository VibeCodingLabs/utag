from pydantic import BaseModel, ConfigDict

from utag_core.ports import ModelPort, StructuredPort, TextPortStructuredAdapter


class Out(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: int


class FlakyTextPort:
    """Returns fenced garbage first, valid JSON after feedback (simulates real LLM)."""
    name = "flaky"
    def __init__(self): self.calls = 0
    def complete(self, *, prompt, system=None, feedback=None):
        self.calls += 1
        return '```json\n{"value": "NaN"}\n```' if self.calls == 1 else '{"value": 7}'


def test_adapter_lifts_text_port_to_structured():
    port = FlakyTextPort()
    adapter = TextPortStructuredAdapter(port)
    assert isinstance(port, ModelPort) and isinstance(adapter, StructuredPort)
    out = adapter.generate(prompt="give value", response_model=Out, max_attempts=3)
    assert out.value == 7 and port.calls == 2


def test_backend_ports_satisfy_protocols_without_network():
    # class-shape checks only; construction requires provider creds/binaries
    from utag_generators.backends import InstructorPort, PiRpcPort, PydanticAIPort
    assert hasattr(InstructorPort, "generate")
    assert hasattr(PydanticAIPort, "generate")
    assert hasattr(PiRpcPort, "complete")
