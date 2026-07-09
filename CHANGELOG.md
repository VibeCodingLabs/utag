# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- Fixed a path traversal vulnerability in `utag_cli` output path generation.
- Fixed a code injection vulnerability in `utag_generators` TypeScript/Zod regex serialization.

### Fixed
- Fixed silent error swallowing during `ModuleSpec` JSON validation.
- Enforced strict alphanumeric validation for `ModuleSpec.name` and `TypeSpec.name` to prevent malformed output paths and syntax errors.
- Fixed an `AttributeError` crash when ingesting JSON arrays instead of objects.
- Fixed potential JSON corruption during LLM fence stripping in `ports.py`.

## [2.0.0] - 2026-07-09

### Added
- Initial release of the `utag` Universal Typed Artifact Generator.
- Added provider-agnostic model ports with built-in validation and repair loops.
- Added normalized Intermediate Representation (IR) (`ModuleSpec`, `TypeSpec`, `FieldSpec`).
- Added generator registries for Pydantic models, Zod schemas, OpenAPI 3.1 docs, and others.
- Added `utag` CLI for generating and validating artifacts.
