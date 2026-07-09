# Changelog

## 2.4.0
- Slack adapter: v0-signature-verified slash command (`/utag generate <target> <repo> <path>`, `/utag status <id>`); 5-minute replay guard; async result (status + PR link) posted to `response_url`; composes with the GitHub deliverer via a shared metadata schema.
- Routines: in-binary interval scheduler from viper config (`routines:` list) — enqueues jobs with zero external trigger; interval-based by design, k8s CronJob manifest provided for cron-precision schedules.
- Delivery generalized: one async path handles GitHub PR + Slack notify per job metadata.
- Deploy kit: distroless control-plane + slim worker Dockerfiles; k8s Deployments/Service with probes and resource limits; KEDA ScaledObject autoscaling workers on live Postgres queue depth (queued-jobs query); CronJob routine template.

## 2.3.0
- GitHub App adapter: HMAC-SHA256-verified webhook (`POST /v1/integrations/github/webhook`); `/utag generate <target> <path>` comment command; control-plane fetches the source file with an App installation token (stdlib RS256 App JWT, signature unit-verified against the public key); worker stays GitHub-agnostic.
- PR delivery on job success (async): git data API (blobs -> tree -> commit -> ref -> pull request); PR body embeds every ValidationReport as collapsible review evidence; PR link commented back on the triggering issue; `pr_opened`/`delivery_failed` job events.
- Job.Metadata field threaded through memory + Postgres stores and the API.
- E2E against a fake GitHub API server: bad-signature rejection + the full webhook->job->worker->PR->comment loop.

## 2.2.0
- control-plane: Go `serve` daemon — job API (`POST /v1/jobs`, claim/complete, artifacts, SSE events), bearer auth, rate limiting, trace-id structured JSON logs, graceful shutdown.
- stores: memory (dev) + Postgres (`FOR UPDATE SKIP LOCKED` queue); race-tested with concurrent workers.
- utag-worker: stdlib-HTTP Python worker consuming the job API through existing registries.
- Stage 0: GitHub Actions CI (pytest + go vet/build + release gate + PG service), goreleaser multi-arch config, committed `uv.lock`, key-gated live-provider smoke test.

## 2.1.0
- go-harness target: cobra+viper single-struct Settings, twelve-factor precedence, go:embed control-plane; go-source validator; real-pinned cobra v1.10.2 / viper v1.21.0 / mapstructure v2.5.0.

## 2.0.0
- Initial harness: IR, registries, bounded repair loop, 3 backends (instructor / pydantic-ai / pi-RPC), 6 targets, meta-generation, deterministic release gate, live-pinned source manifest.
