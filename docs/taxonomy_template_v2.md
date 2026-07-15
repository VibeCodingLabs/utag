# Taxonomy Template v2 — Faceted, Machine-Readable, Agent-Ready

Supersedes taxonomy_template.md (v1: bare L1–L9 directory tree, no metadata contract,
no naming rules, no machine surface). v2 keeps the tree, adds the contracts that make
it generatable and validatable by utag.

## 1. The tree (unchanged levels, explicit names)

```
<taxonomy-root>/
├── _index.yaml                      ← machine-readable index (see §4)
├── INDEX.md                         ← human overview
└── <industry>/                      ← L1  e.g. aiml/
    ├── INDUSTRY.md
    └── <domain>/                    ← L2  e.g. agent-orchestration/
        ├── DOMAIN.md
        └── <category>/              ← L3
            └── <sub-category>/      ← L4
                └── <service-type>/  ← L5  facet: service_type
                    └── <platform>/  ← L6  facet: platforms[]
                        └── <niche>/ ← L7  facet: niche[]
                            └── <workflow>/   ← L8  facet: workflow[]
                                └── <task>/   ← L9
                                    ├── TASK.md
                                    └── AGENT.md   ← SubAgentSpec source (§5)
```

## 2. Naming rules (v1 had none)
- Every directory + `id`: lowercase, hyphen-separated, `[a-z0-9-]`, ≤60 chars.
- One concept per level; plurals only for collection dirs. No dates in names (dates live in frontmatter).
- `File_ID`-style identifiers are kept verbatim as `id`; display naming uses the normalized slug.

## 3. Frontmatter contract (every .md at every level)
Master facets (master_mapped_taxonomy.md), all values normalized lowercase-hyphen:

```yaml
---
id: <verbatim identifier>
title: <display title>
summary: <1-3 sentence purpose>          # becomes SKILL.md description
version: 1.0.0
industry: aiml                            # single
domain: agent-orchestration               # single
service_type: [platform]                  # multi
niche: [coding-agents]                    # multi
workflow: [incident-response]             # multi
brand: <owner>
artifact_type: taxonomy|spec|runbook|code|config|agent
stack_layer: [harness, tool-execution]    # from the 27-layer pipeline vocabulary
interface_type: [cli, mcp, web-application]
api_kind: [rest, mcp, sdk]
maturity: idea|draft|alpha|beta|ga|deprecated
tags: []                                  # governed, lowercase-hyphen
tools: []                                 # concrete tool identifiers
platforms: []
apis: []
---
```
Parser: `agent_harness.parse_taxonomy_file` (accepts `---…---`, `---…***`, leading
```` ```yaml ````, and fences nested inside `---` blocks — all four dialects observed in the corpus).

## 4. `_index.yaml` (new)
Flat list of every node: `{path, id, artifact_type, maturity}` — one glob-free read for
agents and GraphRAG ingestion. Regenerate on change; CI diff-checks it.

## 5. AGENT.md contract (v1 left it as an emoji)
AGENT.md frontmatter IS the facet record; utag derives from it:
- `subagent_spec_from_facets()` → SubAgentSpec (scope = facet path; stack_layer → instructions)
- `taxonomy-skill` generator → SKILL.md (name=slug, description=summary+workflows,
  facets preserved under `metadata`) — must pass the agentskills validator
- planned: job manifest + Arazzo workflow derivations for L8/L9 nodes

## 6. Validation gates
1. frontmatter parses (`parse_taxonomy_file`) 2. slug/dir name match 3. facet values in
catalog vocabularies 4. `_index.yaml` fresh 5. every AGENT.md derives a valid SubAgentSpec
6. every generated SKILL.md passes skill-md lint.
