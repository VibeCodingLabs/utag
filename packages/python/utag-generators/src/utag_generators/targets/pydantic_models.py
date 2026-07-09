"""IR -> Pydantic v2 module source (deterministic, strict, compile-validated downstream)."""
from __future__ import annotations

from utag_core.ir import ModuleSpec, ScalarKind
from utag_core.registry import register_generator
from utag_generators._codegen import HEADER, py_constraints, py_field_type, snake


@register_generator("pydantic-models")
class PydanticModelsGenerator:
    def generate(self, module: ModuleSpec) -> dict[str, str]:
        needs_dt = any(f.type == ScalarKind.datetime for t in module.types for f in t.fields)
        needs_any = any(f.type == ScalarKind.any for t in module.types for f in t.fields)
        lines = [HEADER, "from __future__ import annotations", ""]
        if needs_dt:
            lines.append("from datetime import datetime")
        if needs_any:
            lines.append("from typing import Any")
        lines += ["", "from pydantic import BaseModel, ConfigDict, Field", "", ""]
        for t in module.types:
            lines.append(f"class {t.name}(BaseModel):")
            if t.description:
                lines.append(f'    """{t.description}"""')
            lines.append('    model_config = ConfigDict(extra="forbid")')
            if not t.fields:
                lines.append("    pass")
            for f in t.fields:
                ann = py_field_type(f)
                kw = py_constraints(f.constraints)
                desc = f'description={f.description!r}' if f.description else ""
                extras = ", ".join(x for x in (kw, desc) if x)
                if not f.required:
                    default = "None" if f.default is None else repr(f.default)
                    rhs = f"Field(default={default}, {extras})" if extras else f"Field(default={default})"
                elif extras:
                    rhs = f"Field({extras})"
                else:
                    rhs = None
                lines.append(f"    {snake(f.name)}: {ann}" + (f" = {rhs}" if rhs else ""))
            lines += ["", ""]
        return {f"{snake(module.name)}.py": "\n".join(lines).rstrip() + "\n"}
