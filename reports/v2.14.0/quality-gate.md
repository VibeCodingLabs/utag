# Quality gate — v2.14.0

- PASS: pytest — `uv run --with pytest pytest`
- PASS: entrypoints — `uv run python scripts/check_entrypoints.py`
- PASS: schemas — `uv run python scripts/validate_schemas.py`
- PASS: schema-fixtures — `uv run python scripts/check_schema_fixtures.py`
- PASS: schema-extensions — `uv run python scripts/check_no_unknown_schema_extensions.py`
- PASS: design — `uv run python scripts/validate_design.py design.yaml`
- PASS: generated-ui — `uv run python scripts/check_generated_ui.py`
- PASS: accessibility — `uv run python scripts/check_accessibility_contracts.py`
- PASS: registry-doctor — `uv run utag registry doctor`
- PASS: automation-doctor — `uv run utag automation doctor`
- PASS: observability — `uv run python scripts/check_observability_schema.py`
- PASS: ai-doctor — `uv run utag ai doctor`
- WARN (optional gate failed): ruff
