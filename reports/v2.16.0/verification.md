# v2.16.0 verification report

Date: 2026-07-15 · Branch: `feat/v2.16.0-factory` (from `90d9e8a`)

## What shipped

`utag-factory` — an internal automation factory built on UTAG's own substrate,
driven by the operator's autoscaling template (now canonical).

## Final state

```
uv run pytest                                → 835 passed, 17 skipped, 0 failed (852 collected; +76 factory tests)
python scripts/run_quality_gate.py --release v2.16.0
  → 14/14 required gates PASS (WARN ruff optional)
python scripts/release.py                    → RELEASE golden=df6c2bbfbc0d6db8 (unchanged: factory adds no generators)
```

## Implemented (tested, offline)

- **F0 contracts** — `AutoscalingProfile`/`ResourceContract`/`FactoryJob`/
  `DeadLetterEntry`; the operator's `policies/autoscaling.yaml` validated and
  promoted to canonical (gated in `validate_schemas`).
- **F1 substrate** — sqlite WAL job store + sqlite-vec vector store; Redis
  Streams queue (consumer groups, at-least-once, XAUTOCLAIM recovery, DLQ,
  scaling signals); exact + semantic caches; template retry taxonomy.
- **F2 execution** — bwrap/process sandboxes (verified: home invisible, network
  down under bwrap); worker claim→execute→retry→DLQ; run-python +
  generate-artifact; evidence to observe store + `utag:events`.
- **F3 supervisor** — AST-safe desired_workers formula, guardrails, step limits,
  scale-to-zero, systemd-run/subprocess daemonization.
- **F4/F5 agents + surfaces** — NL→JobRequest via the router; Typer CLI, FastAPI
  (jobs + SSE firehose), FastMCP tools.
- **F6 Flash burst** — run-python/embed/batch-generate tool catalog sized from
  the cloud_burst profile, scale-to-zero Endpoints, capability-gated on
  `RUNPOD_API_KEY` + the `flash` extra.

## Experimental

- `FeatureHashEmbedder` for the semantic cache is a deterministic *lexical*
  placeholder (honest ceiling shown in tests) — real semantics come from the
  Flash `embed` tool.
- The NL agent's offline path uses `FakeStructuredPort` (valid but stub
  JobRequest); live planning needs a provider credential.

## Planned (tracked — not stubbed)

- Model serving: weights NetworkVolume + vLLM OpenAI-compatible streaming
  endpoint (the "download weights + stream execution" fast-follow).
- Live Flash provisioning tests (need RUNPOD_API_KEY + GPU quota).
- Postgres/pgvector store providers (ports exist; sqlite is the v1 default).
- Firecracker isolation tier (declared in the template, not yet implemented).
- Go supervisor adapter target.

## Known limitations

- The factory needs a running Redis for the live surfaces; all tests use
  fakeredis + tmp sqlite, so the suite stays offline.
- ruff optional gate: pre-existing legacy findings (warn-only).
