# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added an animated SVG banner to README.md to improve the UI/UX with accessibility considerations (reduced motion via CSS and slow animation default). Utilized relative responsive scaling with a taller aspect ratio (800x240) and absolute-edge corner alignments to ensure perfect README framing, while significantly reducing internal text size for a balanced final render.
- Added .Jules/palette.md to document critical UI/UX and accessibility learnings regarding Markdown SVG renders.

## [2.4.0] - 2026-07-09

### Added
- Slack adapter: v0-signature-verified slash command (`/utag generate <target> <repo> <path>`, `/utag status <id>`); 5-minute replay guard; async result (status + PR link) posted to `response_url`.
- Routines: in-binary interval scheduler from viper config (`routines:` list) — enqueues jobs with zero external trigger.
- Delivery generalized: one async path handles GitHub PR + Slack notify per job metadata.
- Deploy kit: distroless control-plane + slim worker Dockerfiles; k8s Deployments/Service with probes and resource limits; KEDA ScaledObject autoscaling.

## [2.3.0] - 2026-07-09

### Added
- GitHub App adapter: HMAC-SHA256-verified webhook (`POST /v1/integrations/github/webhook`); `/utag generate <target> <path>` comment command; control-plane fetches the source file with an App installation token.
- PR delivery on job success (async): git data API (blobs -> tree -> commit -> ref -> pull request); PR body embeds every ValidationReport as collapsible review evidence; PR link commented back on the triggering issue; `pr_opened`/`delivery_failed` job events.
- Job.Metadata field threaded through memory + Postgres stores and the API.
- E2E against a fake GitHub API server: bad-signature rejection + the full webhook->job->worker->PR->comment loop.

## [2.2.0] - 2026-07-09

### Added
- control-plane: Go `serve` daemon — job API (`POST /v1/jobs`, claim/complete, artifacts, SSE events), bearer auth, rate limiting, trace-id structured JSON logs, graceful shutdown.
- stores: memory (dev) + Postgres (`FOR UPDATE SKIP LOCKED` queue); race-tested with concurrent workers.
- utag-worker: stdlib-HTTP Python worker consuming the job API through existing registries.
- Stage 0: GitHub Actions CI (pytest + go vet/build + release gate + PG service), goreleaser multi-arch config, committed `uv.lock`, key-gated live-provider smoke test.

## [2.1.0] - 2026-07-09

### Added
- go-harness target: cobra+viper single-struct Settings, twelve-factor precedence, go:embed control-plane; go-source validator; real-pinned cobra v1.10.2 / viper v1.21.0 / mapstructure v2.5.0.

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
