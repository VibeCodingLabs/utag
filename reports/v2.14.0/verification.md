# v2.14.0 verification report

Date: 2026-07-14 · Branch: `feat/v2.14.0-phase0` (local) · Baseline commit: `77017ba`

## Reconciled baseline (Phase 0)

| Fact | Reported before | Measured |
|---|---|---|
| Test pass rate | "294 passed, 100%" | 16 failed, 358 passed, 17 skipped |
| README test count | 64 | 391 collected |
| Version | "ready for v2.13.0" | 2.11.0 |

Root cause of every failure: one missing `import json` (fixed); failures were
hidden because the old harness counted `N passed` and discarded pytest's exit code.

## Final state

```
uv run --with pytest pytest            → 733 passed, 17 skipped, 0 failed
python scripts/run_quality_gate.py --release v2.14.0
  → PASS: pytest, entrypoints, schemas, schema-fixtures, schema-extensions,
          design, generated-ui, accessibility, registry-doctor,
          automation-doctor, observability, ai-doctor
  → WARN: ruff (optional; pre-existing findings in legacy modules)
python scripts/release.py              → RELEASE golden=4de4fce8aa7b01ee (double-hash identical)
```

The 17 skips are environment-gated with explicit reasons: Go control-plane
binary not built (incl. TUI/e2e), postgres unavailable, no live provider key.

## Implemented (tested, gated)

- **Phase 0** — strict `autoresearch.sh` (`--strict`/`--compare`), entrypoint
  audit, `run_quality_gate.py`, reconciled docs.
- **Phase 1** — `utag_core.schemas`: 54 strict contracts, deterministic JSON
  Schema 2020-12 emission, valid+invalid fixture per kind, `utag schema` CLI;
  `utag generate` writes validated `artifact.manifest.json`.
- **Phase 2** — registry manifests for all 79 generators / 9 validators /
  8 importers; `utag registry list|doctor|manifest|coverage`.
- **Phase 3** — `design.yaml` → `design-tokens-css` + `tailwind-v4-theme` +
  `react-component-library` (typed, accessible, token-only colors); `utag design`
  CLI; drift + accessibility gates; 40 generated files in `packages/ui/src/`.
- **Phase 4** — `Recorder` run evidence (schema-validated spans/events/metrics,
  JSONL store), `utag observe run|export|summary|doctor`, validation reports
  linked by run/span id.
- **Phase 5** — policy-enforced `ModelRouter` over checked-in provider
  manifests; explicit-only fallback; decisions logged as evidence;
  offline eval harness; `utag ai` CLI; zero live keys in tests.
- **Phase 6** — autoresearch task engine: lifecycle plans, real subprocess
  gates, receipts, completion impossible with failed gates, auto follow-up
  specs, provably-inert dry-run; `utag autoresearch` CLI.
- **Phase 7** — 7 automation manifests mapped 1:1 to GitHub workflows;
  `utag automation` CLI with secret scanning and run evidence.
- **Phase 8 (partial)** — all 13 console screens declared in `design.yaml` and
  generated as typed components/routes (33 TSX files).

## Experimental

- `FakeProviderAdapter`-backed eval harness (proves plumbing; not a model eval).
- Scratch-dir tsc typecheck (ambient react shim; TS2307 tolerated per repo convention).

## Planned (tracked in TODO/v2.14.0-next-phase.md — not shipped as stubs)

- Interactive UI app build (package.json, npm typecheck/build, mock-data fixtures).
- Live AI provider adapters + call-time cost/latency budget enforcement.
- Remaining named UDC dashboard generators; MCP tool browser data plumbing.
- Historical-zip replay for `autoresearch.sh --compare`.
- `utag openapi` subcommands are **pre-existing stub prints** — flagged, not fixed.

## Known limitations

- Node/Go/Docker legs of the Phase 9 gate run only where those toolchains exist
  (capability-gated, never silently).
- Branch protection applies "PR required" to ~ALL refs with no bypass, freezing
  every pushed branch — phases ship as fresh branches + superseding PRs.
  Recommend re-scoping the ruleset to default/release branches.
