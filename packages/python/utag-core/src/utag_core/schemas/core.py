"""Core artifact schemas: manifests, provenance, validation reports."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field

from utag_core.schemas import SHA256, SLUG, StrictSchema


class RegistryKind(str, Enum):
    generator = "generator"
    adapter = "adapter"
    importer = "importer"
    validator = "validator"
    automation = "automation"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ManifestStatus(str, Enum):
    implemented = "implemented"
    experimental = "experimental"
    planned = "planned"
    deprecated = "deprecated"


class Severity(str, Enum):
    info = "info"
    warn = "warn"
    error = "error"


class FileDigest(StrictSchema):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=SHA256)
    bytes: int = Field(ge=0)


class ArtifactProvenance(StrictSchema):
    generator_id: str = Field(pattern=SLUG)
    utag_version: str
    source_paths: list[str]
    inputs_sha256: str = Field(pattern=SHA256)


class ArtifactManifest(StrictSchema):
    id: str = Field(pattern=SLUG)
    target: str = Field(pattern=SLUG)
    files: list[FileDigest]
    provenance: ArtifactProvenance
    deterministic: bool = True


class ValidationFinding(StrictSchema):
    severity: Severity
    code: str = Field(pattern=SLUG)
    message: str = Field(min_length=1)
    path: str | None = None
    pointer: str | None = None


class ValidationReport(StrictSchema):
    artifact_id: str = Field(pattern=SLUG)
    valid: bool
    findings: list[ValidationFinding] = []
    run_id: str | None = None
    span_id: str | None = None


class RegistryManifest(StrictSchema):
    """Shared shape for generator/adapter/importer/validator/automation manifests."""
    id: str = Field(pattern=SLUG)
    name: str
    version: str
    kind: RegistryKind
    input_schema: str | None = None
    output_schema: str | None = None
    output_files: list[str] = []
    required_capabilities: list[str] = []
    optional_capabilities: list[str] = []
    side_effects: list[str] = []
    risk_level: RiskLevel = RiskLevel.low
    deterministic: bool = True
    validation_gates: list[str] = []
    test_files: list[str] = []
    entrypoints: list[str] = []
    owner: str = "utag"
    status: ManifestStatus = ManifestStatus.implemented


class GeneratorManifest(RegistryManifest):
    kind: Literal[RegistryKind.generator] = RegistryKind.generator


class AdapterManifest(RegistryManifest):
    kind: Literal[RegistryKind.adapter] = RegistryKind.adapter


class ImporterManifest(RegistryManifest):
    kind: Literal[RegistryKind.importer] = RegistryKind.importer


class ValidatorManifest(RegistryManifest):
    kind: Literal[RegistryKind.validator] = RegistryKind.validator


class AutomationManifest(RegistryManifest):
    kind: Literal[RegistryKind.automation] = RegistryKind.automation


class PrimitiveManifest(StrictSchema):
    id: str = Field(pattern=SLUG)
    name: str
    description: str
    category: str = Field(pattern=SLUG)


class CapabilityManifest(StrictSchema):
    id: str = Field(pattern=SLUG)
    name: str
    provided_by: list[str] = []
    required_tools: list[str] = []


class TestSummary(StrictSchema):
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    skipped: int = Field(ge=0)


class ReleaseManifest(StrictSchema):
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    commit_sha: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    artifacts: list[str] = []
    test_summary: TestSummary
    gates: list[str] = []


TOP_LEVEL = [
    ArtifactManifest, ArtifactProvenance, ValidationReport, ValidationFinding,
    GeneratorManifest, AdapterManifest, ImporterManifest, ValidatorManifest,
    AutomationManifest, PrimitiveManifest, CapabilityManifest, ReleaseManifest,
]

_SHA = "a" * 64
EXAMPLES = {
    "ArtifactManifest": {
        "id": "pydantic-models-demo", "target": "pydantic-models",
        "files": [{"path": "models.py", "sha256": _SHA, "bytes": 120}],
        "provenance": {"generator_id": "pydantic-models", "utag_version": "2.11.0",
                       "source_paths": ["fixtures/demo.yaml"], "inputs_sha256": _SHA},
        "deterministic": True,
    },
    "ArtifactProvenance": {"generator_id": "pydantic-models", "utag_version": "2.11.0",
                           "source_paths": ["fixtures/demo.yaml"], "inputs_sha256": _SHA},
    "ValidationReport": {"artifact_id": "pydantic-models-demo", "valid": False,
                         "findings": [{"severity": "error", "code": "syntax", "message": "bad indent", "path": "models.py"}]},
    "ValidationFinding": {"severity": "warn", "code": "optional-check-skipped",
                          "message": "tsc unavailable; typescript validation skipped"},
    "GeneratorManifest": {"id": "design-tokens-css", "name": "Design tokens CSS", "version": "1.0.0",
                          "kind": "generator", "input_schema": "design-yaml", "output_schema": "css-variable-manifest",
                          "output_files": ["theme.css"], "validation_gates": ["schema", "golden"],
                          "test_files": ["tests/unit/test_design_tokens.py"], "entrypoints": ["utag design tokens"]},
    "AdapterManifest": {"id": "instructor-port", "name": "Instructor port", "version": "1.0.0", "kind": "adapter"},
    "ImporterManifest": {"id": "fastapi-importer", "name": "FastAPI importer", "version": "1.0.0", "kind": "importer"},
    "ValidatorManifest": {"id": "python-source", "name": "Python source validator", "version": "1.0.0", "kind": "validator"},
    "AutomationManifest": {"id": "schema-drift", "name": "Schema drift check", "version": "1.0.0", "kind": "automation"},
    "PrimitiveManifest": {"id": "sdk-generation", "name": "SDK generation", "description": "Emit typed SDKs", "category": "codegen"},
    "CapabilityManifest": {"id": "node", "name": "Node.js runtime", "provided_by": ["environment"], "required_tools": ["npx"]},
    "ReleaseManifest": {"version": "2.14.0", "commit_sha": "77017ba", "artifacts": ["dist/utag-2.14.0.tar.gz"],
                        "test_summary": {"passed": 380, "failed": 0, "skipped": 17}, "gates": ["pytest", "entrypoints"]},
}
