---
File_ID: master_mapped_taxonomy_graphrag_agentic_systems
Title: Master Mapped Taxonomy for GraphRAG and Agentic Systems
Date: 2026-05-10
Version: 1.0 (Polyglot Standard)
Authored_By: Deep Research Architect
Tags: taxonomy,knowledge-graph,GraphRAG,metadata,frontmatter,agent-pipelines,automation,api-taxonomy
Summary: Defines a master mapped taxonomy and frontmatter schema that unifies industry, domain, stack layer, artifact type, and workflow facets for GraphRAG-ready knowledge graphs in agentic and automation systems.
***
## Table of Contents
- [Conceptual Foundations](#conceptual-foundations)
- [Top-Level Facets and Their Roles](#top-level-facets-and-their-roles)
- [Core Category and Tag Schema](#core-category-and-tag-schema)
- [Frontmatter Specification for Files](#frontmatter-specification-for-files)
- [Backlinks and Graph Edges](#backlinks-and-graph-edges)
- [Facet Value Catalogs](#facet-value-catalogs)
- [Integration with GraphRAG and Metadata Filters](#integration-with-graphrag-and-metadata-filters)
- [Application Patterns for Agentic and Automation Stacks](#application-patterns-for-agentic-and-automation-stacks)
- [User Query Anchors](#user-query-anchors)
- [Semantic Keywords](#semantic-keywords)
### Conceptual Foundations
A master taxonomy for GraphRAG must reconcile two worlds: content-oriented taxonomies (categories, tags, frontmatter) and graph-oriented ontologies (nodes, edges, properties). Taxonomies provide controlled vocabularies for consistent labeling, while knowledge graphs add explicit relationships and instance-level connections. A metadata knowledge graph focuses on metadata about assets—types, attributes, relationships, provenance—rather than raw content, enabling enterprise-wide discovery, traceability, and governance.[^1][^2][^3][^4]

Information-architecture practice distinguishes hierarchical categories (for navigation and major groupings) from flat tags (for faceted filtering and cross-cutting attributes). Categories are few and structured; tags are numerous and descriptive, often acting as filters rather than exclusive groupings. GraphRAG implementations such as Amazon Neptune Analytics and NVIDIA’s RAG stack emphasize explicit categorical properties and compact metadata schemas to support low-latency filtering over vector search results.[^5][^6][^7][^8][^9][^10]
### Top-Level Facets and Their Roles
The master taxonomy organizes each file or node along multiple orthogonal facets rather than a single tree. Each facet is a controlled vocabulary with constrained values, optimized for categorical filtering and combination in GraphRAG queries.[^7][^9]

| Facet | Purpose | Nature | Examples |
|-------|---------|--------|----------|
| `industry` | Business vertical context | Single categorical | `finance`, `devops`, `aiml`, `media` |
| `domain` | Problem domain or discipline | Single categorical | `agent-orchestration`, `automation`, `security` |
| `service_type` | Value offering or productized service | Multi-valued categorical | `saas`, `managed-service`, `consulting` |
| `niche` | Granular sub-focus within industry+domain | Multi-valued categorical | `coding-agents`, `social-content-automation` |
| `workflow` | Business or technical workflow being automated | Multi-valued categorical | `lead-intake`, `incident-response`, `rag-pipeline` |
| `brand` | Internal or external brand ownership | Single categorical | Product or org names |
| `artifact_type` | Kind of asset for IA and ingestion | Single categorical | `spec`, `taxonomy`, `runbook`, `code`, `config` |
| `tool` | Concrete tools, libraries, CLIs, SaaS | Multi-valued categorical | `n8n`, `Temporal`, `LangGraph` |
| `platform` | Execution or integration platform | Multi-valued categorical | `aws`, `azure`, `gcp`, `kubernetes` |
| `stack_layer` | Position in agent/automation stack | Multi-valued categorical | `frontend`, `middleware`, `auth`, `backend`, `agentic`, `runtime` |
| `interface_type` | Interaction surface | Multi-valued categorical | `web-application`, `desktop-application`, `cli`, `tui`, `mcp`, `ide` |
| `api_kind` | API modality | Multi-valued categorical | `rest`, `websocket`, `sdk`, `plugin`, `mcp` |
| `library_framework` | Library vs framework distinction | Multi-valued categorical | `library`, `framework` |
| `maturity` | Lifecycle stage | Single categorical | `idea`, `draft`, `alpha`, `beta`, `ga`, `deprecated` |

This facet design reflects best practice to separate hierarchical organization from facets and to allow multiple classification axes so that users can approach content by topic, audience, or task simultaneously.[^8][^11]
### Core Category and Tag Schema
The master taxonomy uses a small set of primary "category"-like fields plus flexible tag arrays. Categories act as backbone IA; tags enrich retrieval and graph connectivity.[^5][^6]

#### Primary category-like fields

- `industry`: One value per asset, chosen from an enterprise industry list (e.g., social media content, e‑commerce, devops, hr, aiml) adapted from automation verticals.[^12]
- `domain`: One value that captures conceptual domain, such as `agent-pipeline`, `automation-frameworks`, `api-taxonomy`, `security-cwe`, or `deep-research`.
- `stack_layer`: One or more values aligned to a canonical agent/automation stack: interface, trigger, guardrail, harness, planning, memory, inference, gateway, tool execution, sandbox, orchestration, multi-agent, registry, governance, observability, evaluation, infrastructure.[^13][^14]
- `artifact_type`: Single value describing what the file is (taxonomy, spec, design, runbook, code, dataset, benchmark, notes). This supports filtering by documentation type in GraphRAG.

#### Tag arrays

- `tags`: Free-form but governed keywords, including many of the given terms (`agentic`, `runtime`, `library`, `framework`, `web-application`, `cli`, `mcp`, `ide`, `tui`). Tags operate as multi-valued facets and should be normalized to lowercase hyphenated strings.
- `tools`: Normalized identifiers of specific tools or platforms present in the document (`n8n`, `Zapier`, `LangGraph`, `OpenClaw`, `Claude-Code`, `Composio`).[^13][^12]
- `apis`: Specific API surfaces or products (`OpenAI-chat-completions`, `Neptune-GraphRAG`, `Bedrock-KnowledgeBase`, `MCP`, `A2A`, `AG-UI`).[^7][^9][^13]

This division allows categorical fields to remain compact and indexable, while tags capture the long tail of domain concepts and cross-links.[^9][^7]
### Frontmatter Specification for Files
Each Markdown or text file should embed a YAML frontmatter block implementing the taxonomy. Binary artifacts use adjacent sidecar metadata files following the same schema. This mirrors publishing practice where frontmatter carries IA metadata and supports graph indexing.[^5][^8]

```yaml
---
id: ai_agent_pipelines_27_layers
version: 1.0
created_at: 2026-04-13T00:00:00Z
updated_at: 2026-05-10T00:00:00Z

# High-level identity
title: Canonical Taxonomy of a Production AI Agent Orchestration Pipeline
summary: Complete layer-by-layer taxonomy of a production AI agent pipeline.
slug: ai-agent-pipeline-taxonomy-27-layers

# Core facets
industry: aiml
domain: agent-orchestration
service_type: platform-taxonomy
niche:
  - production-agent-stacks
  - orchestration-pipelines
workflow:
  - research
  - architecture-design
brand: phantom-digital
artifact_type: taxonomy

# Stack and interface positioning
stack_layer:
  - agent-harness
  - planning
  - context-memory
  - inference
  - gateway
  - tool-execution
  - sandbox
  - orchestration
interface_type:
  - web-application
  - cli
  - mcp

# Implementation details
api_kind:
  - rest
  - websocket
library_framework:
  - framework

# Tooling and platforms
tools:
  - langgraph
  - pydanticai
  - n8n
  - composio
platforms:
  - aws
  - azure
  - gcp
  - kubernetes

# Graph connectivity
backlinks:
  - ai_build_layers_extended_taxonomy_2026
  - automation_taxonomy_phantom_tv
aliases:
  - ai-agent-pipeline-taxonomy
  - agent-orchestration-stack
---
```

This schema combines controlled categorical properties (industry, domain, artifact_type) with multi-valued lists that function as GraphRAG metadata arrays (`tags`, `tools`, `platforms`, `stack_layer`, `interface_type`). Such arrays map directly to RAG metadata schemas where tag arrays can be filtered using efficient `array_contains` semantics.[^9][^10]
### Backlinks and Graph Edges
To support GraphRAG and graph traversal, taxonomy metadata must explicitly encode relationships between documents. This is modeled as a lightweight link vocabulary in frontmatter plus typed edges in the graph store.[^1][^2]

#### Backlink fields

- `backlinks`: List of `id` values for parent or related documents; ingestion code reciprocally populates reverse edges.
- `aliases`: Alternative titles or slugs to support entity resolution.
- `see_also`: Optional list of ids for lateral navigation.

During ingestion, each file becomes a `Document` node with properties from frontmatter. For each `backlinks` entry, the pipeline creates a `LINKS_TO` or typed edge (`REFINES`, `EXTENDS`, `IMPLEMENTS`) between source and target nodes. This aligns with knowledge-graph guidance that a taxonomy (controlled vocabularies) plus ontology (relation types) together form a graph suitable for enterprise search and analytics.[^3][^4]
### Facet Value Catalogs
The master taxonomy requires curated value lists to avoid tag explosion and maintain consistent GraphRAG filters. These catalogs are maintained centrally and referenced in frontmatter.

#### Industry and domain

Industry verticals can draw from the automation taxonomy’s L1 verticals such as `social-media-content`, `ecommerce-payments`, `marketing-growth`, `devops-engineering`, `communication-messaging`, `crm-sales`, `iot-home-automation`, `aiml`. Domains refine these into conceptual areas like `agent-pipeline`, `automation-platforms`, `api-features`, `deep-research`, `cwe-security`.[^12]

#### Stack layers and runtime roles

Agent-pipeline and build-layer taxonomies define canonical layers such as `interface-surface`, `automation-trigger`, `input-normalization`, `input-guardrail`, `agent-harness`, `planning`, `context-injection`, `short-term-memory`, `long-term-memory`, `llm-inference`, `inference-optimization`, `gateway-routing`, `output-guardrail`, `tool-dispatch`, `protocol-connectivity`, `tool-execution`, `security-sandbox`, `orchestration`, `multi-agent-coordination`, `agent-registry`, `governance`, `integration-connectors`, `hitl`, `observability`, `evaluation`, `notification`, `infrastructure`. Each file may map to multiple layers, but one or two `primary_layer` values should be designated for summarization.[^13][^14]

For runtime classification, additional tags distinguish `agentic` (multi-step or multi-agent orchestration), `runtime` (long-lived execution environments like vLLM, Ollama, Kubernetes), `library` (imported code with no lifecycle of its own), and `framework` (opinionated combination of libraries and patterns such as LangGraph or OpenClaw).[^13]

#### Interface and application type

Interface facets cover `web-application`, `desktop-application`, `cli`, `tui` (terminal UI), `mcp` (Model Context Protocol server), `ide` (plugins or extensions), and `api` (headless services). These map to patterns observed in automation and agentic stacks where bots, APIs, and UIs coexist.[^12][^13]
### Integration with GraphRAG and Metadata Filters
GraphRAG systems typically store node attributes as scalar and array metadata fields and support filtering by equality, inclusion, and numeric range. Best-practice guidance for GraphRAG filtering recommends using explicit categorical properties, numeric timestamps, and separate attributes for each hierarchy level instead of path-encoded strings.[^7][^9][^10]

Ingested frontmatter should be transformed into a metadata schema such as:

```json
{
  "id": "ai_agent_pipelines_27_layers",
  "text": "hunked document text>",
  "metadata": {
    "industry": "aiml",
    "domain": "agent-orchestration",
    "artifact_type": "taxonomy",
    "service_type": "platform-taxonomy",
    "niche": ["production-agent-stacks", "orchestration-pipelines"],
    "workflow": ["research", "architecture-design"],
    "brand": "phantom-digital",
    "stack_layer": ["agent-harness", "planning", "context-memory", "orchestration"],
    "interface_type": ["web-application", "cli"],
    "api_kind": ["rest"],
    "library_framework": ["framework"],
    "tools": ["langgraph", "pydanticai"],
    "platforms": ["aws", "kubernetes"],
    "created_at": 1775750400,
    "updated_at": 1778428800
  }
}
```

Here timestamps are normalized to numeric epoch values so range filters (`created_at > X`) can be evaluated efficiently. Arrays like `tags`, `stack_layer`, and `tools` can be queried with `in`/`array_contains` semantics for faceted discovery.[^9][^10][^7]
### Application Patterns for Agentic and Automation Stacks
With this taxonomy and metadata schema, GraphRAG applications can implement powerful discovery patterns:

- **By industry and workflow**: "Find all automation blueprints for devops-engineering targeting incident-response workflows" → filter `industry = devops-engineering AND workflow CONTAINS incident-response`.
- **By stack layer**: "Show specs that touch the security-sandbox or tool-execution layers" → filter `stack_layer IN ["security-sandbox", "tool-execution"]`.[^13][^14]
- **By interface and API style**: "List all MCP servers and IDE extensions" → filter `interface_type CONTAINS mcp OR interface_type CONTAINS ide`.[^13]
- **By maturity**: "Exclude deprecated frameworks" → filter `maturity != deprecated`.

Because taxonomies from agent pipelines, build layers, automation verticals, and API feature catalogs are all normalized into the same facet system, GraphRAG queries can seamlessly traverse from high-level conceptual docs down to code-level specs and API schemas. This implements the principle that multiple classification schemes (topic, audience, workflow, layer) should coexist to support diverse navigation strategies.[^8][^11]
### User Query Anchors
- How should frontmatter be structured to support GraphRAG over agentic and automation documents?
- Which facets best capture industry, domain, workflow, and stack layer for AI-agent and automation taxonomies?
- How can categories and tags be combined with backlinks to create a navigable knowledge graph?
- What metadata schema should be used for GraphRAG filtering on industries, tools, platforms, and stack layers?
- How do existing agent pipeline and automation taxonomies map into a unified facet structure?
- How should interface types like CLI, TUI, IDE, MCP, and web-application be represented in metadata?
- How can maturity and lifecycle metadata like alpha, beta, GA, deprecated improve retrieval and governance?
### Semantic Keywords
taxonomy, master taxonomy, mapped taxonomy, knowledge graph, GraphRAG, metadata schema, frontmatter, backlinks, information architecture, categories, tags, facets, industry verticals, automation taxonomy, AI agent pipeline, agent orchestration, harness, guardrails, RAG, vector store, observability, evaluation, security sandbox, MCP, A2A, AG-UI, web application, desktop application, CLI, TUI, IDE, runtime, framework, library, platform, API, REST, WebSocket, governance, HITL, DevOps automation, social media automation, IAM, n8n, Zapier, Temporal, LangGraph, OpenClaw, Bedrock, Neptune Analytics.

---


