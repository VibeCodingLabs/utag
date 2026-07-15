"""The utag session — run it like Claude Code / pi / omp.

Token economy (the whole point):
  ALWAYS loaded : expert system prompt + rules/*.md + one index line per skill
  ON DEMAND     : skill bodies ($SKILL_DIR-injected) via the load_skill tool,
                  slash-command templates, harness tools (opt-in per session)
Slash commands: /skill-name, /commands from commands/*.md, built-ins
(/help /skills /models /targets). Hooks fire around the loop (pre-prompt,
post-response) via UtagHome.run_hooks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent, Tool
from pydantic_ai.usage import UsageLimits

from .home import UtagHome

EXPERT_PROMPT = """You are utag — the Universal Typed Artifact Generator's resident expert.
You help with anything, and you generate everything: typed models (Pydantic/Zod), CLIs
(cobra+viper), APIs (FastAPI/OpenAPI 3.1), Agent Skills, DESIGN.md/UDC design systems,
subagents, jobs, workflows — all validated, deterministic, provenance-tracked.
Doctrine: never fabricate; validate before claiming; prefer generating a typed artifact
over describing one; state assumptions; small verified steps over grand unverified ones.
When a listed skill clearly applies, call load_skill first and follow it."""


def skill_loader_tool(home: UtagHome) -> Tool:
    def load_skill(name: str) -> str:
        """Load the full body of a skill from the index by exact name."""
        ref = home.find_skill(name)
        if ref is None:
            return f"ERROR: no skill named {name!r}. Index:\n{home.skills_index()}"
        return f"[skill {ref.name} @ {ref.path.parent}]\n\n{ref.load()}"
    return Tool(load_skill, name="load_skill", takes_ctx=False,
                description="Load a skill's full instructions by name (bodies are lazy; "
                            "only the index is preloaded).")


@dataclass
class Session:
    home: UtagHome
    model: Any
    extra_tools: list[Tool] = field(default_factory=list)
    request_limit: int = 50
    _agent: Agent | None = None
    transcript: list[dict] = field(default_factory=list)

    def system_prompt(self) -> str:
        parts = [EXPERT_PROMPT]
        rules = self.home.rules_text()
        if rules:
            parts.append("## Rules (always in force)\n" + rules)
        idx = self.home.skills_index()
        if idx:
            parts.append("## Skill index (bodies load on demand via load_skill)\n" + idx)
        return "\n\n".join(parts)

    def agent(self) -> Agent:
        if self._agent is None:
            self._agent = Agent(self.model, instructions=self.system_prompt(),
                                tools=[skill_loader_tool(self.home), *self.extra_tools])
        return self._agent

    # ---------------------------------------------------------------- input routing
    def route(self, raw: str) -> tuple[str, str]:
        """-> (kind, payload). kind: 'prompt' | 'local' (handled without the model)."""
        text = raw.strip()
        if not text.startswith("/"):
            hits = self.home.match_skills(text)
            if hits:  # NL trigger: preload matched bodies into the prompt
                inject = "\n\n".join(f"[skill {h.name}]\n{h.load()}" for h in hits)
                return "prompt", f"{text}\n\n<relevant-skills>\n{inject}\n</relevant-skills>"
            return "prompt", text
        name, _, args = text[1:].partition(" ")
        if name == "help":
            builtins = "/help /skills /models /targets /clarify /enhance"
            customs = " ".join(f"/{c}" for c in self.home.commands)
            skills = " ".join(f"/{s.name}" for s in self.home.skills)
            return "local", f"built-ins: {builtins}\ncommands: {customs or '—'}\nskills: {skills or '—'}"
        if name == "skills":
            return "local", self.home.skills_index() or "no skills installed"
        if name == "targets":
            try:
                import utag_generators  # noqa: F401
                from utag_core.registry import GENERATORS
                return "local", "\n".join(sorted(GENERATORS))
            except Exception as exc:
                return "local", f"registry unavailable: {exc}"
        if name == "models":
            from .models_catalog import load_catalog, models
            try:
                cat = load_catalog(self.home.global_dir / "cache")
                rows = models(cat, provider=args.strip(), tool_call_only=True, limit=15)
                return "local", "\n".join(
                    f"{m.provider}/{m.id}  ctx {m.context//1000}k  ${m.cost_in}/{m.cost_out}"
                    + ("  [R]" if m.reasoning else "") for m in rows) or "no matches"
            except Exception as exc:
                return "local", f"catalog unavailable: {exc}"
        if name == "clarify":
            from .veriforge_bridge import HeuristicScorer
            from veriforge.core.schemas import TaskSpec
            if not args.strip():
                return "local", "usage: /clarify <goal>"
            r = HeuristicScorer().score(TaskSpec(goal=args.strip()), {})
            lines = [f"overall {r.overall:.2f} (gate 0.85) — " +
                     ", ".join(f"{d.value}={v:.1f}" for d, v in r.scores.items())]
            lines += [f"? [{q.dimension.value}] {q.question}  ({' | '.join(q.options)})"
                      for q in r.open_questions]
            return "local", "\n".join(lines)
        if name == "enhance":
            from .veriforge_bridge import enhance
            if not args.strip():
                return "local", "usage: /enhance <goal>"
            ep = enhance(args.strip())
            return "local", (f"techniques: {', '.join(ep.techniques_applied)}\n"
                             f"cove_verified: {ep.cove_verified}\n--- system ---\n{ep.system}"
                             f"\n--- user ---\n{ep.user}")
        if cmd := self.home.commands.get(name):
            return "prompt", cmd.expand(args)
        if ref := self.home.find_skill(name):
            return "prompt", f"{args or 'Apply this skill.'}\n\n[skill {ref.name}]\n{ref.load()}"
        return "local", f"unknown command /{name} — try /help"

    async def turn(self, raw: str) -> str:
        self.home.run_hooks("pre-prompt", env={"UTAG_PROMPT": raw[:1000]})
        kind, payload = self.route(raw)
        self.transcript.append({"role": "user", "content": raw})
        if kind == "local":
            self.transcript.append({"role": "system", "content": payload})
            return payload
        result = await self.agent().run(payload,
                                        usage_limits=UsageLimits(request_limit=self.request_limit))
        out = str(result.output)
        self.transcript.append({"role": "assistant", "content": out})
        self.home.run_hooks("post-response", env={"UTAG_RESPONSE": out[:1000]})
        return out
