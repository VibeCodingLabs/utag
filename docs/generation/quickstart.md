# Quickstart

1. Install: `uv sync` (or editable pip installs of the three member packages).
2. First generation: `utag generate --input fixtures/prompts/normalize-tool.prompt.yaml --target zod-schemas --out out/`.
3. First validation: every `generate` prints a `ValidationReport` JSON (`valid`, `findings[]`, `attempt`); non-zero exit on failure.
4. Reading reports: `findings[].severity` ∈ error|warning|info; `repairable=false` means terminal — do not retry.
5. Export: artifacts land in `--out`; hash-gate a release with `python scripts/release.py`.
