import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, ScalarKind, Constraint

def test_zod_generator():
    gen = get_generator("zod-schemas")
    
    module = ModuleSpec(
        name="zodmod",
        types=[
            TypeSpec(
                name="User",
                fields=[
                    FieldSpec(name="id", type=ScalarKind.string),
                    FieldSpec(name="age", type=ScalarKind.integer, required=False),
                    FieldSpec(name="email", type=ScalarKind.string, constraints=[Constraint(kind="format", value="email")])
                ]
            )
        ]
    )
    
    out = gen.generate(module)
    assert "zodmod.ts" in out
    content = out["zodmod.ts"]
    assert 'import { z } from "zod/v4";' in content
    assert "export const UserSchema = z.strictObject({" in content
    assert "id: z.string()," in content
    assert "age: z.number().int().optional()," in content
    assert "email: z.email()," in content
    assert "export type User = z.infer<typeof UserSchema>;" in content
