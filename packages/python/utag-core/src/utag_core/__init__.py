"""utag-core: normalized IR, registries, ports, repair loop, validation reports."""
from utag_core.ir import ArtifactPlan, Constraint, FieldSpec, ModuleSpec, ProjectSpec, TypeSpec
from utag_core.ports import ModelPort, StructuredPort, TextPortStructuredAdapter
from utag_core.registry import (
    GENERATORS, VALIDATORS, Generator, get_generator, get_validator,
    register_generator, register_validator,
)
from utag_core.repair import RepairExhausted, TerminalGenerationError, format_validation_errors, repair_loop
from utag_core.report import Finding, Severity, ValidationReport

__version__ = "2.0.0"
__all__ = [
    "ArtifactPlan", "Constraint", "FieldSpec", "ModuleSpec", "ProjectSpec", "TypeSpec",
    "ModelPort", "StructuredPort", "TextPortStructuredAdapter",
    "GENERATORS", "VALIDATORS", "Generator", "get_generator", "get_validator",
    "register_generator", "register_validator",
    "RepairExhausted", "TerminalGenerationError", "format_validation_errors", "repair_loop",
    "Finding", "Severity", "ValidationReport",
]
