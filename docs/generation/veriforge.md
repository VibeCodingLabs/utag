# VeriForge in utag — clarify, enhance, verify

Merged from VeriForge 0.1.0 (vendored: `packages/python/utag-veriforge`, module `veriforge`).
Bridge: `agent_harness.veriforge_bridge` — runs the whole thing on utag's provider stack
(pydantic-ai models, catalog, credentials). Instructor optional: `pip install utag-veriforge[instructor]`.

## Session surface
- `/clarify <goal>` — 6-dimension ambiguity scores (weakest link gates at 0.85) + clarifying
  questions with tap-able options. Deterministic heuristic scorer; instant, no model call.
- `/enhance <goal>` — PEE: technique selection from the Prompt Report taxonomy (49/58 seeded,
  loader warns until reconciled), phase-ordered composition, CoVe always last, structural
  anti-fabrication gate. Preview of system+user prompts.
- Tools (auto-mounted): `clarify_task`, `enhance_prompt`; `run_pipeline` when the session has
  a model — full clarify -> enhance -> plan -> code -> test -> sandbox -> debug -> critic run.
- TUI: type a goal in the prompt bar, press `c` — AskUserQuestions modal rounds (<=3 questions,
  2-4 options each, free-text escape, Esc = proceed with logged assumptions).

## Programmatic
```python
from pydantic_ai.models.test import TestModel
from agent_harness import build_agents, enhance, HeuristicScorer, NullAsker
from veriforge.agents.orchestrator import Orchestrator
from veriforge.core.schemas import TaskSpec
from veriforge.pee.techniques import load_registry
from veriforge.verification.sandbox import LocalSandbox  # DockerSandbox in prod

orch = Orchestrator(agents=build_agents(model),          # any pydantic-ai model
                    sandbox=LocalSandbox(),               # Docker: 512MB/0.5cpu/no-net/30s
                    techniques=load_registry(),
                    scorer=HeuristicScorer(), asker=NullAsker())
result = orch.run(TaskSpec(goal="...", constraints=[...], acceptance_criteria=[...]))
```
Critic decorrelation (AgentForge Eq.19): `build_agents(model, per_role_models={"critic": other})`.

## Invariants kept from upstream
- Nothing reaches the Critic without surviving the sandbox; unpassed patches never propagate.
- CoVe is non-negotiable: budget reserved first, composed last; untraceable constraints stripped + logged.
- Flaky tests quarantine (never a fix cycle); security errors always human-flag.
- Residual ambiguity becomes explicit assumptions — never silent.
- Registry honesty: 49/58 techniques seeded; WARN fires until reconciled against arXiv 2406.06608 §2.2.

## Known limits (honest)
- `HeuristicScorer` scores information *presence*, not quality — swap `LLMScorer(model)` for semantics.
- `run_pipeline` uses `LocalSandbox` (no isolation) in-session; wire `DockerSandbox` for prod.
- `run_cove` (LLM-backed factored CoVe, `veriforge.verification.cove`) is available programmatically;
  not mounted as a session tool yet.
