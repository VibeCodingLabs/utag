# UTAG User Guide

Welcome to the Universal Typed Artifact Generator (UTAG). This guide provides instructions on how to set up, configure, and use UTAG to generate typed artifacts from OpenAPI specifications and other source formats.

## Prerequisites
- Python 3.12+
- `uv` (for workspace and dependency management)
- Node.js (for frontend-related artifact generators)

## Installation
1. Clone the repository: `git clone <repo-url>`
2. Install dependencies: `uv sync`

## Usage

### CLI Overview
The UTAG CLI provides a set of subcommands to interact with the artifact generation and validation pipeline.

```bash
uv run utag --help
```

### 1. Registry & Intelligence
Import OpenAPI tools and analyze gaps in coverage:
```bash
uv run utag intel import-openapi-tools --csv openapi-tools.csv --out data/openapi-tools.json
uv run utag intel gaps --against utag --out reports/gap.md
```

### 2. Generating Artifacts
Generate typed artifacts from an input specification:
```bash
uv run utag generate --input <path-to-spec> --target <generator-key> --out <output-dir>
```

Available targets can be listed via:
```bash
uv run utag targets
```

### 3. Pipeline Tools
Manage the OpenAPI canonical pipeline:
```bash
uv run utag openapi normalize --input <path>
uv run utag openapi bundle --input <path>
```

### 4. Verification
Run the integrated test suite:
```bash
uv run pytest tests/unit/
uv run pytest tests/integration/
```

## Contributing
See `CONTRIBUTING.md` for guidelines on adding new generator targets.
