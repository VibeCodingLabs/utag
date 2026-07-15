from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def test_multi_language_sdk_generators():
    targets = [
        "python-sdk",
        "go-sdk",
        "java-sdk",
        "kotlin-sdk",
        "csharp-sdk",
        "php-sdk",
        "ruby-sdk",
        "swift-sdk",
        "rust-sdk",
    ]
    module = ModuleSpec(
        name="multimod",
        types=[TypeSpec(name="User", fields=[FieldSpec(name="id", type=ScalarKind.string)])],
        operations=[
            OperationSpec(
                name="getUser",
                method="GET",
                path="/users/{id}",
                request=RequestSpec(path_params=[FieldSpec(name="id", type=ScalarKind.string)]),
                responses=[ResponseSpec(status_code=200, body_type="User")]
            )
        ]
    )
    for t in targets:
        gen = get_generator(t)
        assert gen is not None, f"Generator {t} not found"
        out = gen.generate(module)
        assert len(out) > 0
