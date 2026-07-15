import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec
import json

def _get_module():
    return ModuleSpec(name="test_sdk")

def test_multi_lang_sdk_metadata():
    targets = [
        "java-sdk", "kotlin-sdk", "csharp-sdk", "php-sdk", 
        "ruby-sdk", "swift-sdk", "rust-sdk"
    ]
    for t in targets:
        gen = get_generator(t)
        out = gen.generate(_get_module())
        assert f"test_sdk-sdk-metadata.json" in out
        data = json.loads(out[f"test_sdk-sdk-metadata.json"])
        assert data["target"] == t
        assert data["implemented"] is False
        assert "reason" in data
