# Repository Guidelines

## Project Overview
**utag** (Universal Typed Artifact Generator) is a provider-agnostic agent harness and typed artifact generator. It takes knowledge inputs (like prompt YAMLs or JSON records) and transforms them into a normalized Pydantic-based Intermediate Representation (IR). This IR is then consumed by pluggable generators to reliably emit strongly-typed artifacts (such as Zod schemas, OpenAPI specs, and Pydantic models).

## Architecture & Data Flow
The system enforces strict decoupling between data input, processing, and output:
1. **utag-core**: The foundation containing the IR schemas, registry plugin system, LLM ports, and bounded validation-feedback loops.
2. **utag-generators**: Extensible targets and backends that consume the IR to generate raw artifacts.
3. **utag-cli**: The primary orchestration entry point mapping inputs to targets.

**Data Flow**: `Input Knowledge` -> `Ingestion/LLM Port` -> `Normalized IR (ModuleSpec)` -> `Target Generator` -> `Raw Artifact` -> `Target Validator`.

## Keep a Changelog Requirement
**It is MANDATORY to fill out all changes made in this repository in the `CHANGELOG.md` file.**
The format strictly adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The format required is:
```markdown
# Changelog
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- New features.
### Changed
- Changes in existing functionality.
### Deprecated
- Soon-to-be removed features.
### Removed
- Removed features.
### Fixed
- Any bug fixes.
### Security
- In case of vulnerabilities.
```

## Key Directories
- `packages/python/utag-core/`: Core IR models, registry definition, error handling, and LLM port abstractions.
- `packages/python/utag-generators/`: Code generation implementations and parsers.
- `packages/python/utag-cli/`: Command-line interface and parsing logic.
- `tests/`: Workspace-aware test suites categorized into unit, integration, and conformance.
- `docs/` & `scripts/`: Development workflow definitions, Quickstarts, deterministic build guards (`sources.py`, `release.py`).

## Development Commands
- **Dependency Install**: `uv sync`
- **Generate Artifacts**: `uv run utag generate --input <path> --target <target> --out <dir>`
- **Validate Artifact**: `uv run utag validate --kind <kind> --path <path>`
- **Test Suite**: `pytest`
- **Release Verification**: `python scripts/release.py` (Runs full test suite and checks artifact determinism).

## Code Conventions & Common Patterns
- **Best Practices & Validation**: You MUST use best practices. NEVER fabricate information or push unvalidated code changes. Always ground code against the current file state.
- **Strict Data Modeling**: Pydantic models MUST use `model_config = ConfigDict(extra="forbid")` to ensure strict schema enforcement.
- **Extensibility via Decorators**: Use `@register_generator("<target>")` or `@register_validator("<kind>")` to dynamically attach capabilities without modifying core files.
- **Provider-Agnostic Ports**: Abstractions like `ModelPort` and `TextPortStructuredAdapter` handle LLM differences natively.
- **Functional Generation**: Generators must be pure and deterministic, returning `dict[str, str]` (relative path to file content) without causing side effects.
- **Resilient Repair Loops**: The `repair_loop` utilizes SHA-256 state tracking to prevent identical LLM retry failures.

## Important Files
- `pyproject.toml` (root & packages): Contains workspace definitions, `pytest` configs, and `hatchling` build directives.
- `packages/python/utag-core/src/utag_core/ir.py`: The single source of truth for the type system (`ModuleSpec`, `TypeSpec`, `FieldSpec`).
- `packages/python/utag-cli/src/utag_cli/main.py`: The orchestrator and CLI parser.
- `sources.lock.toml`: Ensures absolute deterministic builds by pinning exact upstream commit SHAs.

## Runtime/Tooling Preferences
- **Runtime**: Python `>=3.12`
- **Package Manager**: `uv` workspaces ONLY. (Avoid standard `pip` when working locally).
- **Build System**: `hatchling`

## Testing & QA
- **Framework**: `pytest`
- **Execution**: Run via `uv run pytest` or `python scripts/release.py`.
- **Quality Expectations**: All generation outputs must pass golden determinism checks. Regressions in hash generation will cause the CI/Release gate (`scripts/release.py`) to fail immediately.
