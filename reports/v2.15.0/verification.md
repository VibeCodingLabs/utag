# v2.15.0 verification report

Date: 2026-07-15 · Branch: `feat/v2.15.0` (from `90d9e8a`, the v2.14.0 merge)

## Final state

```
uv run pytest                                → 775 passed, 17 skipped, 0 failed (792 collected)
python scripts/run_quality_gate.py --release v2.15.0
  → PASS: pytest, entrypoints, schemas, schema-fixtures, schema-extensions,
          design, generated-ui, accessibility, registry-doctor,
          automation-doctor, observability, ai-doctor,
          ui-typecheck, ui-build            (14 required gates)
  → WARN: ruff (optional; pre-existing findings in legacy modules)
python scripts/release.py                    → RELEASE golden=df6c2bbfbc0d6db8 (double-hash identical)
npm --prefix packages/ui run typecheck       → clean (strict tsc, full @types/react)
npm --prefix packages/ui run build           → vite production build, 95 modules
```

The 17 skips are the known environment-gated set (Go control-plane binary,
postgres, live provider key), each with an explicit reason.

## Implemented (tested, gated)

- **Self-generated console** — `design.yaml` → tokens/tailwind CSS, TS contract
  types, schema-valid fixtures, data-rendering typed components
  (`card|table|matrix|panel|timeline|chart|board|graph|nav`), generated
  interactions (select-run → inspector), route pages with region placement, and
  a generated route table. Hand-written frontend: `main.tsx` (17 lines) + build
  config only. Bundle verified to contain components, fixtures, interaction
  keys, and token variables.
- **Real `utag openapi`** — normalize (cycle-safe ref inlining), bundle
  (external-file refs), diff (operations + schemas, added/removed/changed),
  overlay apply (Overlay 1.0 subset), lint (5 rules, error exit), agent-readiness
  (5 weighted checks). Petstore fixtures; the old stub-asserting tests replaced.
- **Live AI call path** — router-chosen ports behind `RoutedStructuredAdapter`:
  spans + `prompt-run`/`model-call-trace` evidence, latency/cost budgets
  (breach = error finding + event + failed call), sha-keyed cache, credential
  refusal for non-local providers, `utag ai call` CLI. Offline proof includes
  pydantic-ai `FunctionModel` behind the real `PydanticAIPort`.

## Experimental

- `FakeStructuredPort` (returns schema examples) powers the offline `ai call`
  path — clearly labeled, never routes implicitly to live providers.
- Timeline/chart/board/graph renderers are deliberately minimal first versions
  (bars, grouped columns, node chains) — real data, small visual vocabulary.

## Planned (tracked in TODO — not shipped as stubs)

- Embedding/Rerank/Vision/ToolPlanning/PromptEnhancement/Verifier adapter slots.
- Live token/cost usage capture inside `PydanticAIPort`/`InstructorPort`
  (`last_usage` is the contract; the ports don't populate it yet, so telemetry
  records nulls — never invented numbers).
- Console data beyond fixtures (loading real run-evidence JSONL into the UI).
- shadcn-registry generator.

## Known limitations

- ruff optional gate: pre-existing findings in legacy modules (warn-only).
- Live-provider smoke remains credential-gated in `tests/smoke/`.
