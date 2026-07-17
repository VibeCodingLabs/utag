# utag — Universal Typed Artifact Generator

Provider-agnostic agent harness + typed artifact generator. Any knowledge in (prompt YAMLs, NL, KB records, transcripts) → normalized Pydantic IR → validated typed artifacts out (Pydantic models, Zod v4, Agent Skills, OpenAPI 3.1, DESIGN.md, prompt YAML) — including **generators that generate generators**.

## Install (uv workspace)

```bash
uv sync                       # or: pip install -e packages/python/utag-{core,generators,cli}
```

## Use

```bash
utag targets                                                        # list generators
utag generate --input fixtures/prompts/categorize-file.prompt.yaml \
              --target pydantic-models --out out/                   # ingest -> generate -> validate
utag validate --kind skill-md --path out/my-skill/SKILL.md          # standalone validation stage
python scripts/sources.py                                           # pin upstream SHAs (real, live)
python scripts/release.py                                           # tests + determinism gate
```

## Architecture (moats)

| Layer | What | Why it's a moat |
|---|---|---|
| `utag_core.ports` | `ModelPort` (text) / `StructuredPort` (typed) protocols + `TextPortStructuredAdapter` | One repair contract, N backends — swap providers without touching generators |
| `utag_core.repair` | Bounded validation-feedback loop: `ValidationError.errors()` → model feedback; early-stop on identical failure; hard cap 10 | Identical retry semantics across instructor, pydantic-ai, and raw-text RPC agents |
| `utag_generators.backends` | InstructorPort (`from_provider`), PydanticAIPort (`Agent`/`output_type`/`retries`), PiRpcPort (JSONL-over-stdio to `pi --mode rpc`, earendil-works/pi) | Provider-agnostic incl. full agent processes, not just chat APIs |
| `utag_core.registry` | Decorator registries for generators + validators; generation and validation are separate stages | External packages extend without core changes |
| `utag_generators.meta` | `GeneratorSpec` (strict Pydantic) → emits a new registered generator module **and its test** | Generators that generate generators; LLM-mintable via any StructuredPort |
| `targets/go_harness.py` | IR → single-binary Go control-plane: cobra CLI, ONE viper-filled `Settings` struct (defaults<config<env `UTAG_*`<flags, mapstructure/v2), `go:embed`-baked sibling-generator artifacts | Twelve-factor static deploy; the generator generates its own control-plane |
| `sources.lock.toml` | Live-resolved upstream commit SHAs + installed versions/licenses | Nothing fabricated; release fails visibly on unresolved sources |

## Guarantees

- Deterministic: identical inputs → byte-identical artifacts; golden double-hash gate in `scripts/release.py`; zero timestamps in artifacts.
- Strict: every IR/contract model is `extra="forbid"`.
- Bounded: repairable failures retry ≤ N (hard cap 10); terminal failures (`TerminalGenerationError`) never retry.
- Capability-gated: `tsc` validation runs when Node/npx exists, degrades to info-level skip otherwise.
- Tested: 852 tests (835 pass, 17 environment-gated skips) — unit / integration / conformance (your 4 prompt fixtures × every target × its validator) / golden. `./autoresearch.sh --strict` runs the suite and fails on any test failure.

## Importers (public API)

Existing API specs and route schemas import into the IR via `utag_core.registry.get_importer(fmt).ingest(content)`. Registered formats: `fastapi-importer`, `springdoc-importer`, `express-nest-importer`, `aspnet-importer`, `django-drf-importer`, `fastify-importer`, `laravel-importer`, `rails-importer`. `python scripts/check_entrypoints.py` asserts every registered generator/validator/importer stays reachable or documented.

## Backends

```python
from utag_core.ports import TextPortStructuredAdapter
from utag_generators.backends import InstructorPort, PydanticAIPort, PiRpcPort

port = InstructorPort("anthropic/claude-sonnet-4-6")          # native structured
port = PydanticAIPort("anthropic:claude-sonnet-4-6")          # native structured
port = TextPortStructuredAdapter(PiRpcPort())                 # pi agent, shared repair loop
module = port.generate(prompt=..., response_model=ModuleSpec, max_attempts=3)
```

pi RPC notes: JSONL, LF-delimited, `{"type": "prompt"|"get_last_assistant_text", "id": ...}` → `{"type": "response", "id": ...}`. Text-generation bridge only (current pi exposes no host-tools RPC); structured output comes from the shared repair loop.

## Meta-generation

```python
from utag_generators.meta import GeneratorSpec, OutputRule, emit_generator
spec = GeneratorSpec(target="csv-manifest", class_name="CsvManifestGenerator",
                     doc="Emit a CSV manifest per module.",
                     output=OutputRule(filename_template="{module}.csv",
                                       line_template="{type_name},{field_names}",
                                       header="type,fields"))
files = emit_generator(spec)   # new generator module + its unit test, both source-validated
```

`GeneratorSpec` is itself a strict Pydantic model — any backend can produce it through the repair loop: the harness mints its own tools.

## GitHub App (autonomous DevOps surface)

Comment on any issue/PR in an installed repo:

```
/utag generate pydantic-models prompts/service.prompt.yaml
```

Control-plane verifies the webhook (HMAC-SHA256), fetches the file with an installation token, queues a job; a worker generates + validates; the control-plane opens a PR containing the artifacts under `utag/<target>/` — with every ValidationReport embedded in the PR body — and comments the link back. Config (env): `UTAG_GITHUB_WEBHOOK_SECRET`, `UTAG_GITHUB_APP_ID`, `UTAG_GITHUB_PRIVATE_KEY_FILE`, `UTAG_GITHUB_API_BASE` (GHE-ready). App permissions needed: Contents RW, Pull requests RW, Issues RW; subscribe to Issue comment events.

## Slack

`/utag generate <target> <owner/repo> <path>` (queues; result + PR link posted back to the channel) and `/utag status <job-id>`. Config: `UTAG_SLACK_SIGNING_SECRET`, `UTAG_GITHUB_INSTALLATION_ID`. Requests verified with Slack v0 signing + replay guard.

## Routines

In-binary interval schedules via config file:

```yaml
routines:
  - {name: nightly-openapi, every: 12h, target: openapi-3.1, input-file: /config/service.prompt.yaml}
```

Cron-precision schedules: `deploy/k8s/routine-cronjob.yaml` (plain `POST /v1/jobs`).

## Deploy (autoscaling)

`deploy/`: distroless control-plane image, slim worker image, k8s manifests, and a KEDA `ScaledObject` scaling workers 1→20 on live queue depth (`SELECT count(*) FROM jobs WHERE status='queued'`, ~5 jobs/worker). Twelve-factor throughout: all config via `UTAG_*` env from one Secret.

## Agent-harness adapters

`utag-adapters` (`from agent_harness import harness_tools`): forge-jobs + audit-kit as pydantic-ai tools; compose with utag backends via `PydanticAIPort(model, tools=harness_tools(...))`. CI runs the suite against fixtures; export `FORGE_JOBS_ROOT` / `AUDIT_KIT_DIR` to run it against the real kits (expects 43 jobs / 34 templates).

## SubAgents

`SubAgentSpec` -> `build_subagent(spec, model)` / `subagent_tool(spec, model)`: ephemeral, provider-agnostic subagents with CLI + Skill + OpenAPI-endpoint + openapi.tools-KB + job + audit + MCP tools. Mutating HTTP verbs are opt-in; CLI argv is fixed unless `allow_extra_args`. `taxonomy_subagents(rows)` maps taxonomy rows to specs.

## UDC (Universal Design Contract)

`assemble(design_dir)` -> validate (`udc` validator: your schema + URI resolution) -> derive: `udc-design-md` (validated DESIGN.md) and `udc-component` (typed TSX). The UDC graph stays canonical; derivations are deterministic.

## TUI

`utag-tui` (Textual): live console over the control-plane. `UTAG_CONTROL_PLANE_URL` + `UTAG_API_TOKEN`, then `utag-tui`. Keys: `r` refresh, `c` command bar, `q` quit. Command bar: `generate <target> <fixture-path>`, `status <job-id>`.

## Install (one-liner)

```bash
curl -fsSL <raw-url>/install.sh | bash   # or: bash install.sh from a checkout
utag login anthropic && utag-tui         # press s for the session, Esc for the dashboard
```

## ~/.utag conventions

`skills/<industry>/<domain>/<service>/<workflow>/SKILL.md` (+references/assets/scripts/templates/evals), `commands/*.md` ($ARGUMENTS), `rules/*.md`, `hooks.yaml`, `config.yaml`, `credentials.json` (0600). Project `.utag/` overrides global. Skills lazy-load: index lines always, bodies (with `$SKILL_DIR` injected) only on `/skill-name` or NL trigger.
