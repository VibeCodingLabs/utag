# Full Software & AI Offering Taxonomy

***

```yaml
File_ID: software_ai_offering_taxonomy
Title: Full Software & AI Offering Taxonomy
Date: 2026-04-11
Version: 1.0 (Polyglot Standard)
Authored_By: Deep Research Architect
Tags: taxonomy, software, AI, product, platform, service, API, SDK, framework, library, wrapper, agent, middleware, monetization, architecture
Summary: Complete classification of software and AI offering types across 16 categories. Covers definition, examples, overlaps, architecture, best practices, pitfalls, constraints, deliverables, strategies, and monetization for each type.
```

***

## Table of Contents

1. [Overview & Overlap Model](#overview--overlap-model)
2. [Product](#1-product)
3. [Service](#2-service)
4. [Platform](#3-platform)
5. [Wrapper / Adapter / Facade](#4-wrapper--adapter--facade)
6. [API](#5-api)
7. [SDK](#6-sdk)
8. [Library](#7-library)
9. [Framework](#8-framework)
10. [Plugin / Extension / Add-on](#9-plugin--extension--add-on)
11. [Middleware](#10-middleware)
12. [Runtime / Engine](#11-runtime--engine)
13. [Protocol / Standard / Spec](#12-protocol--standard--spec)
14. [Agent / Copilot / Bot](#13-agent--copilot--bot)
15. [Microservice](#14-microservice)
16. [Marketplace / Ecosystem](#15-marketplace--ecosystem)
17. [Tool](#16-tool)
18. [Overlap Matrix](#overlap-matrix)
19. [Monetization by Type](#monetization-by-type)
20. [RAG Retrieval Anchors](#rag-retrieval-anchors)

***

## Overview & Overlap Model

These categories are **not mutually exclusive**. Any single offering can occupy multiple slots simultaneously. The axes of differentiation are:[^1]

- **Who consumes it** — end user, developer, or another system
- **Extensibility** — does it let others build on top?
- **Ownership of execution** — does it run itself or does the consumer run it?
- **Abstraction level** — how far removed from the underlying compute?
- **Autonomy** — does it act, or does it wait to be called?[^2]

A useful mental model: delivery model (product vs. service), abstraction level (API vs. platform), and extensibility (tool vs. platform) are **orthogonal axes**, so one thing can score on multiple at once.[^3]

***

## 1. Product

**Definition:** Packaged, versioned software with a defined feature set delivered to an end user. Value is in the software itself, not ongoing provider labor.[^3]

**Examples:** Figma, VS Code, Linear, 1Password, Notion.

### Architecture
- Single deployable unit or SaaS multi-tenant app
- Vertical feature scope; owned UX end to end
- Auth, billing, data isolation baked in[^4]

### Best Practices
- Ship a CLAUDE.md / context file for your own codebase from day one
- Multi-tenancy must be schema-per-tenant or RLS-enforced from day one (retrofitting is costly)
- 12-factor compliance for env parity and horizontal scale

### Deliverables
- Versioned release artifacts, changelogs, runbooks, SLA docs

### Constraints
- You own the full surface area: auth, billing, GDPR/CCPA, uptime SLA
- Feature scope creep is the #1 killer — resist becoming a platform too early

### Pitfalls
- Building for yourself, not your ICP
- Skipping observability until prod breaks
- Pricing too low early and anchoring customers on that price

### Monetization
- SaaS subscription (per-seat, per-workspace, or flat)[^5]
- One-time license (rare now, mostly on-prem enterprise)
- Freemium → paid conversion
- Usage-based if the product has a natural unit of consumption (tokens, API calls, exports)[^6]

***

## 2. Service

**Definition:** Value delivered via ongoing provider activity, expertise, or managed execution — not just software access. The provider does work; the customer pays for outcomes or time.[^3]

**Examples:** AWS Managed Services, Vercel hosting, Stripe Treasury, a dev agency.

### Architecture
- SLA-backed infrastructure the customer never touches
- Often a product with a managed layer on top
- Runbooks, on-call rotations, incident response baked in

### Best Practices
- Explicit SLAs and SLOs before any contract
- Runbook-as-code (Terraform, Pulumi) — never manual provisioning
- Separate data plane from control plane so customers can self-serve monitoring

### Deliverables
- SLA document, incident response plan, monthly health reports, managed runbooks

### Constraints
- Provider bears operational burden — scales human cost with customer count unless heavily automated
- Compliance scope expands (SOC 2, HIPAA, PCI-DSS) because you process customer data[^4]

### Pitfalls
- Underpricing managed work relative to infra cost
- No exit path for customers → regulatory risk and churn amplification
- Conflating "service" with "product" in your pricing and leading to misaligned expectations

### Monetization
- Per-seat or per-org managed fee + infra pass-through
- Outcome-based pricing (% of savings/uplift)
- Retainer + overage
- Enterprise annual contracts with auto-renewal[^7]

***

## 3. Platform

**Definition:** A foundation others build on. Provides APIs, SDKs, data, and runtime infrastructure that enable third parties to create products and services. Platforms exhibit network effects — more builders → more value → more builders.[^8][^9]

**Examples:** Stripe (payments), Shopify (commerce), Snowflake (data), Salesforce (CRM platform), AWS.

### Architecture
- Core product + published API surface + SDK layer + developer portal
- Extensibility hooks: webhooks, event streams, plugin interfaces
- Multi-sided: at least a producer side and consumer side[^7]
- Data layer often the real moat (not the UX)

### Best Practices
- Subsidize the side that drives growth (e.g., free dev tools, charge merchants)[^7]
- Publish an explicit API versioning policy from v1 — breaking changes destroy ecosystem trust
- Build a developer experience (DX) team before a marketing team
- Governance: define what third parties can and can't do in your ToS

### Deliverables
- API reference docs, SDK in 3+ languages, sandbox/test environment, developer portal, webhook catalog, changelog feed

### Constraints
- Platform responsibility: if a third-party app fails, users blame the platform
- You cannot outrun your ecosystem — governance and quality control are ongoing costs
- Extensibility surface = attack surface (OWASP A01–A05 apply to every integration)[^4]

### Pitfalls
- Platformizing before product-market fit
- No rate limiting or quota enforcement → abuse and infra cost explosion
- Letting ecosystem cannibalize your core product margin

### Monetization
- API metering (per-call, per-seat, per-GB)[^10]
- Transaction/revenue share from third-party apps (e.g., App Store 15–30%)[^7]
- Tiered partner programs (free → growth → enterprise)
- Data products sold off the aggregated platform data[^4]

***

## 4. Wrapper / Adapter / Facade

**Definition:** A thin abstraction layer over an existing API, model, or system. Doesn't own the underlying capability — re-exposes it with a modified interface, added guardrails, or simplified UX.[^11][^12]

**Sub-types (intent differs, structure is similar):**

| Sub-type | Intent | Example |
|----------|--------|---------|
| Wrapper | Extends/changes behavior of an object | OpenAI Python client |
| Adapter | Makes incompatible interfaces work together[^13] | LangChain LLM adapters |
| Facade | Simplifies a complex subsystem behind one interface[^13] | boto3 over raw AWS API calls |
| Proxy | Controls access, adds caching/auth/logging | Nginx, API Gateway |

**Examples:** LiteLLM (multi-provider LLM wrapper), Portkey, AWS SDK (facade over REST), any "ChatGPT for X" with zero proprietary model.

### Architecture
- Thin HTTP/gRPC layer; state is usually in the upstream
- Dependency inversion: code against wrapper interface, swap upstream without refactor

### Best Practices
- Version-pin upstream; upstream breaking changes propagate to you instantly
- Add caching at the wrapper layer to reduce upstream cost and latency
- Document what you add vs. what you pass through — users need to know the diff
- Adapters should implement a shared interface, not just wrap directly[^14]

### Deliverables
- Interface spec (OpenAPI, protobuf), migration guides, upstream changelog monitoring

### Constraints
- **You own nothing proprietary** — upstream can kill your business (e.g., OpenAI rate-limit changes)
- Legal: check upstream ToS — many prohibit reselling API access directly
- Margin compression: your COGS is upstream API cost + your overhead

### Pitfalls
- Building a pure wrapper product with no added value beyond the underlying service
- No fallback when upstream goes down — single point of failure
- Leaking upstream errors verbatim to users (breaks abstraction contract)

### Monetization
- Markup over upstream cost (risky, thin margin)
- Freemium access with premium add-ons (routing, caching, guardrails)[^10]
- SaaS seat-based access to a managed version
- Value-add features: fallback routing, observability, spend controls, PII scrubbing

***

## 5. API

**Definition:** An Application Programming Interface — a defined contract specifying how software components communicate. When "API" is the primary offering (not just plumbing), it IS the product.[^15]

**Examples:** Stripe API, Twilio, SendGrid, OpenAI API, Google Maps API.

### Architecture
- REST, GraphQL, gRPC, or WebSocket
- Stateless preferred (12-factor); state lives in DB, not in the server
- Auth: API keys for M2M, OAuth2 for user-delegated access
- Versioning: URL-based (/v1/) or header-based; never break v1

### Best Practices
- Rate limiting per key, per IP, per org — from day one[^10]
- OWASP API Security Top 10: especially A01 (broken object-level auth) and A05 (broken function-level auth)
- Idempotency keys on all mutating endpoints
- OpenAPI spec is the contract — generate SDKs from it, not by hand[^15]
- Observability: latency P50/P95/P99, error rate, usage per key

### Deliverables
- OpenAPI/Swagger spec, Postman collection, sandbox with mock data, API keys dashboard, rate limit documentation, error code reference

### Constraints
- Backward compatibility is a hard constraint — you can add, rarely remove
- Every public endpoint is an attack vector — OWASP A01–A10 on every route
- Documentation quality directly drives developer adoption rate[^15]

### Pitfalls
- Returning 200 OK with error payloads instead of proper HTTP status codes
- No pagination on list endpoints → clients fetching unbounded result sets
- Exposing internal IDs (UUIDs only in public surface)
- Docs written after the fact, not maintained

### Monetization
- Pay-per-call / usage-based billing[^6][^4]
- Tiered monthly quotas (free → growth → scale)
- Per-model pricing if offering multiple AI models[^10]
- Enterprise flat-rate with committed usage minimums[^10]

***

## 6. SDK

**Definition:** A Software Development Kit — a bundled collection of libraries, tools, docs, and sample code that lets developers build for a specific platform or integrate a specific service.[^16][^17]

**Examples:** AWS SDK (Boto3, JS), Stripe iOS SDK, Firebase SDK, Android SDK, Claude SDK.

### Architecture
- Language/platform-specific (one SDK per major language target)[^17]
- Wraps the underlying API with idiomatic code patterns
- Often bundles auth helpers, retry logic, serialization, error handling

### Best Practices
- Generate from OpenAPI spec where possible to stay in sync with the API
- Ship with working code examples and typed interfaces (TypeScript, Pydantic)[^16]
- Semantic versioning; maintain a changelog; deprecate before removing
- Test the SDK in CI against the live sandbox API

### Deliverables
- SDK packages (PyPI, npm, Maven, NuGet), typed interfaces, usage examples, migration guides

### Constraints
- Maintenance burden multiplies with each language target
- Breaking changes in the API require synchronized SDK releases
- Platform-specific limitations (e.g., iOS memory model vs. Node.js)[^17]

### Pitfalls
- Generating SDKs from hand-written specs that drift from actual API behavior
- No retry/backoff logic — developers expect it in the SDK
- Missing TypeScript types → poor DX, runtime errors in consumer code

### Monetization
- SDKs are almost always free (developer acquisition tool)
- Monetize the underlying API/platform the SDK unlocks
- Premium SDK features: offline caching, analytics hooks, enterprise auth modules

***

## 7. Library

**Definition:** Reusable code module(s) providing specific functionality. The calling code controls flow — you call the library. No runtime enforcement; no opinions on architecture.[^18]

**Examples:** NumPy, Pydantic, Lodash, Requests, Zod, Moment.js.

### Architecture
- Imported at build time or runtime; no separate process
- Pure functions preferred; avoid global state
- Typed interfaces (TypeScript, Pydantic) reduce integration friction

### Best Practices
- Keep scope narrow and well-defined — do one thing extremely well
- Zero required peer dependencies where possible
- Tree-shakeable (ESM) for frontend libraries — bundle size matters
- 100% typed public API; never `any` in TypeScript

### Deliverables
- Package on registry (PyPI/npm/crates.io), API reference docs, changelog, test suite

### Constraints
- You own no runtime — errors surface in consumer's process
- Version conflicts in monorepos when multiple packages depend on different versions (dependency hell)
- Can't force consumers to upgrade — breaking changes linger

### Pitfalls
- Mutating consumer data structures in place
- Throwing exceptions without typed error variants
- Shipping without a peer dep check → consumer's build silently fails

### Monetization
- Usually OSS (acquisition/trust-building); monetize via hosted service, support contracts, or commercial license for enterprise use[^1]
- Dual licensing: MIT for OSS, commercial for SaaS usage at scale (Elasticsearch model)
- Sponsorships (GitHub Sponsors, Open Collective)

***

## 8. Framework

**Definition:** An opinionated scaffold defining the structure, flow, and architecture of an application. The framework calls your code (inversion of control) — opposite of a library.[^16]

**Examples:** Django, FastAPI, Next.js, LangChain, Angular, Spring Boot, LangGraph.

### Architecture
- Entry points, lifecycle hooks, and conventions owned by the framework
- Plugin/extension points for customization
- Often bundles a library collection + runtime conventions[^1]

### Best Practices
- Don't fight the framework — work within its conventions or switch frameworks
- Keep business logic in framework-agnostic modules so you can swap the shell
- Pin major versions; major framework upgrades are high-risk migrations
- Use dependency injection for testability

### Deliverables
- Application scaffolds, config files, CI pipeline adapted to framework conventions

### Constraints
- Opinionated by design — limits architectural freedom
- Framework lock-in: migrating off is expensive
- Framework bugs become your bugs[^19]

### Pitfalls
- Over-customizing core framework behavior (monkeypatching)
- Mixing business logic and framework code in the same layer
- Upgrading a major version without a migration branch and regression tests

### Monetization
- Open-source frameworks rarely monetize directly
- Commercial extensions, hosted cloud (e.g., LangSmith for LangChain), enterprise support contracts
- Training and certification programs

***

## 9. Plugin / Extension / Add-on

**Definition:** Augments a host application with additional capability. Cannot run standalone — requires the host.[^20][^21]

**Sub-type distinctions (practical, not hard rules):**

| Term | Typical Scope | Technical Depth |
|------|---------------|-----------------|
| Plugin | Niche, deep integration; often compiled[^20] | High (direct host API access) |
| Extension | Lightweight, browser/editor; web tech[^20] | Low-medium |
| Add-on | Broadest — umbrella term for any host enhancement[^20] | Varies |
| Module | Self-contained functional unit within a larger system | Medium |

**Examples:** VS Code extensions, WordPress plugins, Claude Code plugins, Shopify apps, Chrome extensions.

### Architecture
- Runs in host's process (plugins) or sandboxed iframe/worker (extensions)[^20]
- Communicates via host-provided API surface
- Permissions model enforced by host (Chrome extension manifest v3 restrictions)[^20]

### Best Practices
- Declare minimum required permissions — over-permissioned plugins are a security liability
- Graceful degradation if host API changes
- Test in the host's sandbox environment before release
- Hooks over direct mutation — use the host's event system

### Deliverables
- Manifest/plugin.json, packaged artifact for host marketplace, documentation, update changelog

### Constraints
- Host controls distribution, pricing policy, and can deprecate your plugin's API
- Plugin marketplaces take 15–30% cut if you charge[^7]
- Security: a buggy plugin runs with host-level trust[^20]

### Pitfalls
- Tight coupling to internal host APIs that aren't officially supported
- No version pinning → host update breaks your plugin silently
- Storing sensitive data in plugin without encryption (runs in shared host process)

### Monetization
- Freemium through the host marketplace
- SaaS subscription gated by license key validation
- One-time purchase (AppExchange, VS Code Marketplace)
- White-label for enterprise customers outside the marketplace

***

## 10. Middleware

**Definition:** Reusable software that bridges the gap between applications and underlying infrastructure (OS, network, databases). Handles cross-cutting concerns: routing, translation, logging, auth, transformation.[^19]

**Examples:** Express.js middleware, Redis, RabbitMQ, Kong API Gateway, Kafka, Nginx, OAuth2 proxy.

### Architecture
- Request/response pipeline (web middleware)
- Message broker model (async event middleware)[^22]
- Often invisible to end users — operates between services
- Patterns: broker, pipeline, interceptor, message bus

### Best Practices
- Stateless middleware where possible — state belongs in the data store
- Idempotent message processing (deduplication IDs on queues)
- Circuit breakers and bulkhead patterns to prevent cascade failures[^22]
- Trace IDs injected at entry — propagate through all downstream calls (distributed tracing)

### Deliverables
- Configuration-as-code, topology diagrams, dead-letter queue (DLQ) runbooks, latency dashboards

### Constraints
- Becomes a critical path — downtime is system-wide downtime
- Operational complexity: distributed systems debugging is hard (split-brain, message ordering)
- Data consistency: at-least-once vs. exactly-once delivery tradeoffs[^22]

### Pitfalls
- Putting business logic in middleware (it belongs in services)
- No DLQ for failed messages → silent data loss
- Synchronous calls through "async" middleware defeating the purpose

### Monetization
- Cloud-managed middleware as a service (e.g., Confluent for Kafka, Upstash for Redis)
- Open-source core + enterprise features (SSO, audit logs, compliance)
- Per-message or per-GB throughput pricing

***

## 11. Runtime / Engine

**Definition:** The execution environment that interprets or runs compiled code or managed workloads at runtime.[^23]

**Sub-types:**

| Term | Meaning | Example |
|------|---------|---------|
| Runtime | Full execution environment for a language/platform[^23] | Node.js, JVM, Deno |
| Engine | Component that executes a specific language/logic within a larger system[^23] | V8 (JS), LangGraph (workflow) |
| Container Runtime | Runs containerized workloads via OS primitives[^24] | containerd, Docker Engine |
| Daemon | Background process serving as persistent system component | dockerd, kubelet |

**Examples:** Node.js, JVM, Docker Engine, LangGraph (workflow runtime), Temporal.

### Architecture
- Owns the process model, memory management, and I/O scheduling
- Low-level runtimes interact directly with the OS kernel (namespaces, cgroups)[^24]
- High-level runtimes add GC, module resolution, standard library

### Best Practices
- Never run production workloads as root (especially container runtimes)[^24]
- Pin runtime versions in CI — runtime minor version bumps can change behavior
- Use rootless containers where the runtime supports it (Podman)[^25]
- Resource limits on every container/process (CPU, memory, network egress)

### Deliverables
- Dockerfile / container spec, runtime config, version matrix, security hardening checklist

### Constraints
- Runtime is out of your control — upstream security patches require fast redeployment
- Language/platform lock-in if the runtime is exotic
- Cold start latency for serverless runtimes[^24]

### Pitfalls
- Bundling secrets into container images
- Missing health checks → orchestrator can't recover crashed containers
- Ignoring runtime GC pauses in latency-sensitive services

### Monetization
- Runtimes themselves rarely monetize — they are infrastructure
- Monetize as: managed runtime-as-a-service (Vercel for Node.js), enterprise support, or cloud-native tooling that wraps the runtime

***

## 12. Protocol / Standard / Spec

**Definition:** A formal definition of how systems or components communicate. Not software itself — a contract that software implements.[^26]

**Sub-types:**

| Term | Role |
|------|------|
| Protocol | Rules for data exchange between entities[^26] |
| Standard | Published document specifying a protocol (RFC, ISO, IEEE)[^26] |
| Spec | Formal description of behavior/interface (OpenAPI, protobuf, JSON Schema) |

**Examples:** HTTP, gRPC, MCP (Model Context Protocol), A2A (Agent-to-Agent), OpenAPI, AG-UI, WebSocket, OAuth2.

### Architecture
- Defines message format, transport, error handling, versioning rules
- Often encoded as a schema (protobuf IDL, OpenAPI YAML, JSON Schema)
- Implementations exist in multiple languages from the same spec

### Best Practices
- Version protocols from v1 — never assume backward compatibility
- Publish a conformance test suite so implementations can be validated
- Keep protocol scope narrow; composability beats monolithic specs
- Use existing standards (HTTP, OAuth2, gRPC) as building blocks before inventing new ones

### Deliverables
- Spec document (YAML/protobuf/RFC format), reference implementation, conformance test suite, versioning policy

### Constraints
- Adoption is the only measure of success for a protocol — without implementations it's worthless
- Hard to monetize directly
- Governance: who owns the spec? Who can break it?

### Pitfalls
- Designing a protocol without a working implementation first (spec fiction)
- Versioning strategy absent from v1 — retrofitting is painful
- Coupling transport and business logic in the same spec

### Monetization
- Protocols are rarely monetized directly
- Monetize via: certified implementations, compliance tooling, managed infrastructure that implements the protocol, consulting

***

## 13. Agent / Copilot / Bot

**Definition:** Software that acts with some degree of autonomy to complete goals — uses tools, memory, and reasoning rather than just responding to queries.[^27][^2]

**Autonomy spectrum (each tier builds on the one below):**

| Type | Autonomy | Tool Access | Memory | Example |
|------|----------|-------------|--------|---------|
| Bot/Chatbot | Very low — scripted responses[^28] | None | None/session | FAQ bot |
| AI Assistant | Low-moderate — NLP, contextual[^27] | Limited | Short-term | Siri, Alexa |
| Copilot | Moderate — proactive, inline in workflow[^2] | Context-aware | Cross-session | GitHub Copilot |
| Agent | High — plans, executes, uses tools[^2] | Full tool call loop | Long-term | Claude Code, AutoGPT |
| Digital Employee | Persistent — owns a job function[^2] | Full | Persistent, scoped | SDR agent, Tier-1 support agent |

### Architecture
- ReAct loop: Reason → Act → Observe → Repeat[^2]
- Tool registry, memory layer (short-term, episodic, semantic), orchestration layer
- Human-in-the-loop checkpoints for high-risk actions
- Observability: every tool call logged with inputs/outputs and latency

### Best Practices
- Trust boundary: never let the agent call mutating operations without a confirmation step (for irreversible actions)
- OWASP LLM Top 10: especially prompt injection (LLM01) and excessive agency (LLM08)
- Sandbox all code execution (E2B, Docker)[^29]
- Implement structured output (Pydantic/Zod) on every tool return — never parse free text
- Rate-limit agent tool calls per session to cap cost blowout

### Deliverables
- System prompt (CLAUDE.md or equivalent), tool schema registry, agent eval harness, cost dashboard, human-review queue

### Constraints
- Non-determinism: same input ≠ same output — require eval harnesses not unit tests
- Cost: agentic loops with many tool calls can be expensive at scale
- Latency: multi-step chains add wall-clock time users notice[^2]

### Pitfalls
- No max-steps limit → infinite loop and runaway API cost
- Agent has write access to production systems without a staging/dry-run mode
- Trusting LLM tool selection without validation of tool inputs against schema
- Conflating copilot and agent in product messaging — users expect different autonomy levels[^2]

### Monetization
- Per-task or per-run billing (outcome pricing)[^4]
- Seat-based for copilot tier (human+AI collaboration)
- Usage-based token billing for agent loops
- Enterprise "digital employee" contracts billed per role/FTE equivalent

***

## 14. Microservice

**Definition:** An independently deployable service that owns a single bounded business capability, communicates over network protocols, and maintains its own data store.[^30][^31]

**Examples:** Auth service, payment service, notification service, embedding service.

### Architecture
- Each service: its own codebase, database, deployment pipeline[^31]
- Communication: synchronous (REST/gRPC) or async (Kafka, RabbitMQ)[^30]
- Service mesh (Istio, Linkerd) for observability, mTLS, retries at network layer
- API Gateway at the boundary (Kong, AWS API GW)

### Best Practices
- Each service owns its data store — never share a database between services[^31]
- Circuit breakers on all outbound calls (Resilience4j, Polly)
- Distributed tracing from day one (OpenTelemetry, Jaeger)
- Design for failure: every downstream call can fail; services must degrade gracefully[^30]
- Contract testing (Pact) to catch breaking changes between services before deployment

### Deliverables
- Service catalog, API contracts (OpenAPI/protobuf), runbooks, SLOs per service, architecture diagram

### Constraints
- Operational overhead is significant — requires mature DevOps, CI/CD, and monitoring[^30]
- Data consistency across services: no distributed transactions (use Saga pattern instead)[^30]
- Network partitions are real: design for eventual consistency

### Pitfalls
- Distributed monolith: microservices that are chatty and tightly coupled — worst of both worlds
- No service mesh → no visibility into inter-service latency and failures
- Starting with microservices before understanding domain boundaries (do a modular monolith first)

### Monetization
- Not a customer-facing offering — internal architecture decision
- Enables platforms to expose individual capabilities as APIs (each microservice → one API product)[^32]

***

## 15. Marketplace / Ecosystem

**Definition:** A meta-layer that connects producers (builders, vendors) and consumers (users, buyers) around a core platform. Network effects compound — more producers → more consumers → more producers.[^8][^7]

**Examples:** Shopify App Store, Salesforce AppExchange, AWS Marketplace, VS Code Extension Marketplace, npm registry.

### Architecture
- Multi-sided platform: at minimum a supply side and demand side[^7]
- Discovery engine (search, categories, ratings)
- Trust layer (vetting, reviews, security scanning)
- Transaction rail (purchase, licensing, installs)
- Distribution: webhooks/install hooks so third-party apps integrate with the core platform[^8]

### Best Practices
- Don't monetize the marketplace until it has critical mass — subsidize builders first[^7]
- Vetting pipeline: automated security scans + human review for high-trust categories
- Provide SDKs and reference apps to lower builder on-ramp friction[^4]
- Revenue share model must leave enough margin for builders to build a business[^7]

### Deliverables
- Developer portal, app submission guidelines, review SLA, revenue share documentation, trust and safety policy

### Constraints
- Platform liability: malicious apps harm your brand; you need a rapid takedown process
- Cold start problem: chicken-and-egg between builders and users
- 15–30% take rate creates tension with builders at scale[^7]

### Pitfalls
- Building a marketplace before the core platform has enough engaged users to attract builders
- No quality floor → marketplace fills with low-quality apps and erodes trust
- Competing with your own ecosystem (building first-party apps that crowd out third-party builders)

### Monetization
- Transaction/revenue share (15–30% of each sale)[^7]
- Listing fees or premium placement
- Subscription access tiers (basic vs. verified partner)
- Advertising/featured placement[^4]
- Data products derived from ecosystem activity

***

## 16. Tool

**Definition:** Single-purpose, narrow-scope utility. A product is often a collection of tools. A tool does one job extremely well.[^33]

**Examples:** jq, ripgrep, ffmpeg, Wrangler (Cloudflare CLI), ESLint, Prettier.

### Architecture
- CLI, GUI widget, or in-code utility
- Minimal dependencies; fast startup
- Composable with other tools (Unix philosophy: stdin/stdout, pipes)

### Best Practices
- Exit codes matter — follow Unix conventions (0 = success, non-zero = failure)
- `--dry-run` flag on any destructive tool
- Machine-readable output option (JSON) alongside human-readable default

### Deliverables
- Binary release artifacts, man page / `--help` output, shell completion scripts

### Constraints
- Scope discipline: adding features converts a tool into a product (scope creep)
- Distribution: getting into package managers (Homebrew, apt, winget) requires maintenance

### Pitfalls
- No `--help` or man page → poor discoverability
- Destructive operations with no confirmation prompt
- Hardcoded paths/config instead of respecting XDG/env vars

### Monetization
- Usually free/OSS; monetize via SaaS equivalent, support, or bundling into a larger product
- CLI tools as on-ramps: free CLI → paid hosted service (Vercel, Railway, Fly.io model)

***

## Overlap Matrix

| Type | Can Be a Product | Can Be a Service | Can Be a Platform | Can Wrap Others |
|------|:---:|:---:|:---:|:---:|
| Product | ✓ | ✓ (SaaS) | ✓ (if extensible) | ✓ |
| Service | ✓ | ✓ | ✓ (managed platform) | ✓ |
| Platform | ✓ | ✓ | ✓ | ✓ |
| API | ✓ (API-as-product) | ✓ | ✓ | ✓ |
| SDK | – | – | – | ✓ (wraps API) |
| Library | – | – | – | ✓ |
| Framework | – | – | ✓ (partial) | ✓ |
| Wrapper/Facade | ✓ | ✓ | – | ✓ |
| Plugin | – | – | – | ✓ (extends host) |
| Middleware | – | ✓ | ✓ (partial) | ✓ |
| Runtime | – | ✓ | ✓ | – |
| Protocol | – | – | – | – |
| Agent | ✓ | ✓ | ✓ | ✓ |
| Microservice | – | ✓ | – | ✓ |
| Marketplace | ✓ | ✓ | ✓ | – |
| Tool | ✓ | – | – | ✓ |

***

## Monetization by Type

| Type | Primary Revenue Model | Secondary / Advanced |
|------|-----------------------|----------------------|
| Product | Subscription (per-seat, flat, tiered)[^5] | Usage-based, one-time license |
| Service | Managed fee + infra pass-through | Outcome/success-based |
| Platform | API metering + transaction share[^7] | Data products, partner tiers |
| API | Pay-per-call, tiered quotas[^10] | Hybrid subscription + usage |
| SDK | Free (acquisition) | Paid enterprise SDK modules |
| Library | OSS + dual license[^1] | Hosted service, support contracts |
| Framework | OSS + hosted cloud[^8] | Enterprise support, training |
| Plugin | Freemium marketplace[^7] | White-label, seat license |
| Wrapper | Markup + value-add features[^10] | SaaS access, guardrails tier |
| Middleware | Cloud-managed service | OSS core + enterprise features |
| Runtime | Managed runtime-as-a-service | Enterprise support |
| Protocol | Compliance tooling, consulting | Certified implementations |
| Agent | Per-task / per-run[^4] | Digital employee FTE contracts |
| Microservice | Exposed as individual API product | Part of platform metering |
| Marketplace | Transaction share 15–30%[^7] | Listing fees, advertising, data |
| Tool | Free → paid hosted service | Bundled into larger product |

***

## RAG Retrieval Anchors

### User Query Anchors
- What is the difference between a product, service, and platform in software?
- How does a wrapper differ from an adapter, facade, and proxy?
- What types of software offerings exist beyond products and platforms?
- What are the architecture patterns for each type of software offering?
- What are the best monetization strategies for APIs, platforms, agents, and libraries?
- What are common pitfalls when building each type of software offering?
- How do I decide whether to build a product, platform, API, or agent?
- What is the difference between an agent, copilot, and bot?
- What are the constraints and deliverables for each software offering type?
- How do SDK, library, and framework differ?
- What is middleware and how does it fit in software architecture?
- How does a microservice relate to a platform?
- What is the difference between a protocol, standard, and spec?

### Semantic Keywords
product, service, platform, API, SDK, framework, library, wrapper, adapter, facade, proxy, middleware, runtime, engine, daemon, plugin, extension, add-on, module, microservice, agent, copilot, bot, digital employee, marketplace, ecosystem, protocol, standard, spec, monetization, SaaS, PaaS, IaaS, usage-based pricing, transaction fee, freemium, dual licensing, multi-sided platform, network effects, OWASP, zero-trust, 12-factor, trust boundary, inversion of control, ReAct loop, tool registry, dependency injection, contract testing, circuit breaker, idempotency, distributed tracing, saga pattern, cold start, rate limiting, semantic versioning, OpenAPI, gRPC, REST, event-driven, message broker, plugin marketplace, developer portal, DX

---

## References

1. [A Taxonomy for Open Source Software | Andrew Nesbitt](https://nesbitt.io/2025/11/29/oss-taxonomy.html) - I’m working on a structured taxonomy for classifying open source projects across multiple dimensions...

2. [AI Agents vs Copilots vs Chatbots: 2026 Taxonomy Guide - Taskade](https://www.taskade.com/blog/ai-agents-taxonomy) - A chatbot answers questions in a chat window. A copilot suggests the next action inline inside a wor...

3. [Product, Service, and Platform: Unraveling the Differences and ...](https://www.linkedin.com/pulse/product-service-platform-unraveling-differences-peter-smulovics) - In the realm of business and technology, the terms “product,” “service,” and “platform” are frequent...

4. [How to Monetize AI: Business Models, Pricing, and ROI](https://productschool.com/blog/artificial-intelligence/ai-monetization) - Monetizing AI features into profit isn’t trivial. Here are some clear strategies for capturing and p...

5. [12 software monetization strategies to drive revenue in 2023 - Paddle](https://www.paddle.com/resources/software-monetization) - There are a lot of different monetization strategies. Some of the most common include selling access...

6. [AI monetization in 2025: 4 pricing strategies that drive revenue](https://www.withorb.com/blog/ai-monetization) - Solve your usage-based billing needs with a flexible tool that fits your customers, teams, and stack...

7. [Pricing for Product Platform Strategy: Ecosystem-Based Monetization](https://www.getmonetizely.com/articles/pricing-for-product-platform-strategy-ecosystem-based-monetization) - Ecosystem-based monetization represents not just a revenue model but a strategic framework for creat...

8. [Business Models for Platform Ecosystems | Insights | Scale](https://www.scalevp.com/blog/business-models-for-platform-ecosystems) - The decision here is whether to launch a marketplace and then whether to monetize it. A marketplace ...

9. [Product vs. Platform vs. Feature: Key Differences - ATMECS](https://atmecs.com/product-vs-platform-vs-feature-choosing-the-right-development-strategy-for-scalable-software-solutions/) - Explore the differences in Product vs. Platform vs. Feature for effective software development and l...

10. [What Is AI API Monetization? Challenges and Opportunities](https://metronome.com/blog/what-is-ai-api-monetization-challenges-opportunities) - AI API monetization transforms APIs into revenue streams, but legacy billing systems can't handle mo...

11. [Difference between the Facade, Proxy, Adapter and Decorator ...](https://stackoverflow.com/questions/3489131/difference-between-the-facade-proxy-adapter-and-decorator-design-patterns) - Adapter: for non-compatible interfaces · Facade: for making interfaces simpler · Proxy: for managing...

12. [What are the differences between proxy, wrapper or a façade classes](https://stackoverflow.com/questions/12296299/what-are-the-differences-between-proxy-wrapper-or-a-fa%C3%A7ade-classes) - What are the differences between proxy, wrapper or a façade classes They all seem to be the same to ...

13. [Difference Between the Facade, Proxy, Adapter, and Decorator ...](https://www.geeksforgeeks.org/system-design/difference-between-the-facade-proxy-adapter-and-decorator-design-patterns/) - What is a Facade Design Pattern? The Facade Method Design Pattern provides a unified interface to a ...

14. [Adapters, Facades, or Both (Design Patterns for Architects) - YouTube](https://www.youtube.com/watch?v=2OdxTG4wKTc) - In this video, I discuss how to use facades with adapters to enable swappable design without violati...

15. [API vs. SDK: Choosing the Right Development Tools - XB Software](https://xbsoftware.com/blog/api-vs-sdk/) - This guide will help you understand the roles and differences between APIs and SDKs in software deve...

16. [What is an SDK? SDK Vs Library Vs Framework - GeeksforGeeks](https://www.geeksforgeeks.org/software-engineering/what-is-an-sdk-sdk-vs-library-vs-framework/) - SDKs provide comprehensive resources for building applications on specific platforms, libraries offe...

17. [SDK vs API - Difference Between Developer Tools - AWS](https://aws.amazon.com/compare/the-difference-between-sdk-and-api/) - A software development kit (SDK) is a set of platform-specific building tools like debuggers, compil...

18. [Difference between framework vs Library vs IDE vs API vs SDK vs ...](https://stackoverflow.com/questions/8772746/difference-between-framework-vs-library-vs-ide-vs-api-vs-sdk-vs-toolkits) - A framework is a big library or group of libraries that provides many services (rather than perhaps ...

19. [[PDF] Patterns, Frameworks, and Middleware - Computer Science](https://www.cs.wm.edu/~dcschmidt/PDF/ICSE-03.pdf) - For example, patterns help guide framework design and use, thereby reducing software devel- opment e...

20. [Add-ons vs. Plugins vs. Extensions: The Exact Differences Explained for ...](https://www.codegenes.net/blog/exact-difference-between-add-ons-plugins-and-extensions/) - If you’ve ever tried to enhance your favorite software—whether it’s a web browser, a productivity to...

21. [What Are Plugins and How Do They Work?](https://www.geeksforgeeks.org/techtips/what-are-plugins-and-how-do-they-work/) - Your All-in-One Learning Portal: GeeksforGeeks is a comprehensive educational platform that empowers...

22. [Middleware Patterns for Cloud Platforms](https://www.intechopen.com/chapters/77864) - This chapter explores how traditional system architectures are being affected by the emergence of ‘U...

23. [terminology - What's the difference between a runtime environment ...](https://stackoverflow.com/questions/42950306/whats-the-difference-between-a-runtime-environment-a-runtime-engine-and-a-run) - A runtime system (aka runtime engine) is software that is designed to aid the execution of a compute...

24. [What are Container Runtimes? Types and Popular Runtime Tools](https://www.wiz.io/academy/container-security/container-runtimes) - While a container runtime is responsible for running containers, a container engine is a broader sys...

25. [Most Popular Container Runtimes](https://www.cloudraft.io/blog/container-runtimes) - One key distinction of Podman is that running containers does not require a separate daemon process....

26. [What is the difference between a protocol, a standard, and ... - Reddit](https://www.reddit.com/r/ElectricalEngineering/comments/cuhn9o/what_is_the_difference_between_a_protocol_a/) - A protocol defines the interactions between two or more entities. For example, the dhcp networking p...

27. [Decoding the AI toolbox: Chatbots, assistant, copilots and agents ...](https://www.ataccama.com/blog/decoding-the-ai-toolbox-chatbots-assistant-copilots-and-agents-explained) - One of the most telling ways to differentiate between AI chatbots, assistants, copilots, and agents ...

28. [AI Copilot vs AI agent vs bot: What's the difference? - SalesWings](https://www.saleswingsapp.com/agentforce/ai-copilot-vs-ai-agent-vs-bot/) - A copilot is effectively an agent. But the main difference is, unlike a typical bot, it can generate...

29. [can-you-make-a-list-of-all-the-4JG74L5PTM6Q64TRwaCKDA.md](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_2158916d-7a5d-4f59-a722-e1b9dd6a1a42/f3db3c3b-9107-407e-8a09-7367c89b9b48/can-you-make-a-list-of-all-the-4JG74L5PTM6Q64TRwaCKDA.md?AWSAccessKeyId=ASIA2F3EMEYEX6KCLCJN&Signature=7K8Jv8IRR6jDlW4nNUPUi%2F5HRbo%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEIb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCKDWYkOaGGX6u7X1wAiONtYZz52d%2BGoIl8tgqDbtQvDwIgASPpuDYU2KCH3mtxjvOyfI4utK%2BB%2Bb4P39dJzpMjIXsq8wQIThABGgw2OTk3NTMzMDk3MDUiDMsbzB%2Bfw%2B0RMy1xbirQBNlTa%2BNqwYWDWi5ujUTsH84Nx%2F%2FXmXXsLlLoVmq3gpVkTTIWzW6C3%2B4uQcroIfb4ilVpMv8QM1tjUFGT6jzfnrdnWY4NZMGP5bO%2BjBnZYLQHMpSzcHck1D0jE4PD2eNf4qs%2BbDvxskLNFVduTUvBE3BvdxvHQYAsSrb4a%2F6FJxqbdLQYPWgez1TOLojTHRkZ%2BsmT7rGzjSKutOft5xI81qavJ0xmotG57DCxGnPtG6W7605F%2BZHG3UMRd2x7fpuEfHcjhbWchIzDFLRhtWd3xuQlm%2BoFaX0XU%2Flgrh13V7FZCL37kEMI1o9dxjz%2BlyTCOnU4bPSLfUzp7Ot9U7kYbj25Q3yQKaBch2kYK10pirQC2MONbpQVTbE3rjaCrfCxzkGlqT3GnyBGGAUtnoLd3D90zOxf%2BmnGJv3CTMplRLYxclRwHCtpRkmzhtOCb9Ns2m7nsBJlYzoCIaYiGscyLZxU20sgu8CCWnYLUFy7QGlFW4mtI3UK4DauzGfTKDIWiqKzjOjZGJZZnMeo0%2FvIE1X4762WArC8oUGdQjtUp4cLY64WAz%2FAdzoCNyXkvHELUxOp9a5T9pWVpouiT7SDVf3FNyfuHEA6LkqsSZSZTQE85tQlIXSQO51sFH3zr4NrtXE8tYQ6JjUds9BkO04F%2FE6dsK6QkxtPf0mtm8xDSJaqOVtw7Xrkux9MvdQTX8s5p%2FG6HpVwp9r%2F8aYLE3fav7tDUSqFTOUURLflw68o1Hm%2FkMouIOdsNCy6%2BlMeSrDXDjASjk8NxC1gfn%2BCLSCi6VMwwPTqzgY6mAF00W5qGHSv5xvhAoBX2HEc980kClvZ%2FmaLrajMyzLhSR2k5EdJ9WsuR7aq9qd5e05QWQEKfe3QlOms4WtcrBcyW%2F3TtR3%2BTxjWZBR4vS6uIC8gJa%2BeB5UPnV2NhShPceO46qecsDvW2rbEZnp7WD3wZ1r0JrL5ubtiQlC7unsiOEI1exstovS91Butu7i0yDpAbTii%2F5ZS%2Bw%3D%3D&Expires=1775945747)

30. [Enterprise software architecture patterns: The complete guide](https://vfunction.com/blog/enterprise-software-architecture-patterns/) - Discover the most effective enterprise software architecture patterns, their benefits, comparisons, ...

31. [Difference Between Microservices and Web Services - GeeksforGeeks](https://www.geeksforgeeks.org/software-engineering/difference-between-microservices-and-web-services/) - Your All-in-One Learning Portal: GeeksforGeeks is a comprehensive educational platform that empowers...

32. [How to Monetize APIs: Business Models & AI Integration Guide](https://www.sensedia.com/post/api-monetization-in-the-age-of-ai-from-infrastructure-to-business-model) - Transform your APIs from technical tools into profit centers. Explore Sensedia's monetization models...

33. [Key terms defined: Products, tools, platforms, and ecosystems](https://www.appcues.com/blog/software-product-tool-platform-ecosystem) - A product is a tool or a collection of tools packaged together by a software company. All the tools ...

