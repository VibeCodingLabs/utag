"""~/.utag conventions — same shape as Claude Code / pi / omp home dirs.

Resolution order: project .utag/ (walk up from cwd) OVERRIDES global ~/.utag/.
Layout (both scopes):
  skills/<industry>/<domain>/<service>/<workflow>/SKILL.md  (+ references/assets/scripts/templates/evals)
  commands/<name>.md        slash commands (frontmatter + body; $ARGUMENTS substitution)
  hooks.yaml                {pre-prompt: [...], post-generate: [...], pre-job: [...]}
  rules/*.md                concatenated into the session system prompt
  config.yaml               provider/model defaults
  credentials.json          api keys, chmod 0600 (global scope only)
Skills are LAZY: only frontmatter is indexed (name, description, triggers);
the body is read at invoke time with $SKILL_DIR substituted.
"""
from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SCAFFOLD = ["skills", "commands", "rules", "cache"]


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n") and "\n---\n" in text[4:]:
        fm, body = text[4:].split("\n---\n", 1)
        try:
            return (yaml.safe_load(fm) or {}), body
        except yaml.YAMLError:
            return {}, text
    return {}, text


@dataclass
class SkillRef:
    """Frontmatter-only handle. ~1 index line of tokens until invoked."""
    name: str
    description: str
    triggers: list[str]
    path: Path  # SKILL.md
    scope: str  # global | project

    def index_line(self) -> str:
        return f"/{self.name} — {self.description}"

    def load(self) -> str:
        """Invoke-time body load with $SKILL_DIR injection."""
        _, body = _split_frontmatter(self.path.read_text())
        return body.replace("$SKILL_DIR", str(self.path.parent)).strip()


@dataclass
class SlashCommand:
    name: str
    description: str
    template: str
    path: Path

    def expand(self, arguments: str) -> str:
        return self.template.replace("$ARGUMENTS", arguments).strip()


@dataclass
class UtagHome:
    global_dir: Path
    project_dir: Path | None = None
    _skills: list[SkillRef] = field(default_factory=list)
    _commands: dict[str, SlashCommand] = field(default_factory=dict)

    # ---------------------------------------------------------------- setup
    @classmethod
    def resolve(cls, cwd: Path | None = None, global_dir: Path | None = None) -> "UtagHome":
        g = Path(global_dir or os.environ.get("UTAG_HOME", Path.home() / ".utag"))
        p = None
        cur = Path(cwd or Path.cwd()).resolve()
        for parent in (cur, *cur.parents):
            if (parent / ".utag").is_dir():
                p = parent / ".utag"
                break
        home = cls(global_dir=g, project_dir=p)
        home.reindex()
        return home

    def init_scaffold(self) -> None:
        for d in SCAFFOLD:
            (self.global_dir / d).mkdir(parents=True, exist_ok=True)
        cfg = self.global_dir / "config.yaml"
        if not cfg.exists():
            cfg.write_text("provider: anthropic\nmodel: claude-sonnet-4-6\n")

    def _scopes(self) -> list[tuple[str, Path]]:
        scopes = [("global", self.global_dir)]
        if self.project_dir:
            scopes.append(("project", self.project_dir))  # later wins = overrides
        return scopes

    # ---------------------------------------------------------------- skills
    def reindex(self) -> None:
        by_name: dict[str, SkillRef] = {}
        cmds: dict[str, SlashCommand] = {}
        for scope, root in self._scopes():
            for sk in sorted((root / "skills").rglob("SKILL.md")) if (root / "skills").is_dir() else []:
                fm, _ = _split_frontmatter(sk.read_text())
                name = str(fm.get("name") or sk.parent.name).strip()
                if not name:
                    continue
                triggers = fm.get("triggers") or []
                if isinstance(triggers, str):
                    triggers = [t.strip() for t in triggers.split(",")]
                meta = fm.get("metadata") or {}
                triggers = [str(t).lower() for t in triggers] or \
                           [str(x).lower() for x in (meta.get("workflow") or [])]
                by_name[name] = SkillRef(name=name, description=str(fm.get("description", ""))[:200],
                                         triggers=triggers, path=sk, scope=scope)
            cdir = root / "commands"
            if cdir.is_dir():
                for c in sorted(cdir.glob("*.md")):
                    fm, body = _split_frontmatter(c.read_text())
                    cmds[c.stem] = SlashCommand(name=c.stem,
                                                description=str(fm.get("description", "")),
                                                template=body, path=c)
        self._skills = sorted(by_name.values(), key=lambda s: s.name)
        self._commands = cmds

    @property
    def skills(self) -> list[SkillRef]:
        return self._skills

    @property
    def commands(self) -> dict[str, SlashCommand]:
        return self._commands

    def skills_index(self) -> str:
        """The always-loaded part: one line per skill (lazy-load economy)."""
        return "\n".join(s.index_line() for s in self._skills)

    def match_skills(self, prompt: str, limit: int = 3) -> list[SkillRef]:
        """NL trigger matching: frontmatter triggers or the name appearing in the prompt."""
        p = prompt.lower()
        hits = [s for s in self._skills
                if s.name.lower() in p or any(t and t in p for t in s.triggers)]
        return hits[:limit]

    def find_skill(self, name: str) -> SkillRef | None:
        return next((s for s in self._skills if s.name == name), None)

    # ---------------------------------------------------------------- rules
    def rules_text(self) -> str:
        parts = []
        for _, root in self._scopes():
            rdir = root / "rules"
            if rdir.is_dir():
                parts += [f.read_text().strip() for f in sorted(rdir.glob("*.md"))]
        return "\n\n".join(p for p in parts if p)

    # ---------------------------------------------------------------- hooks
    def hooks(self, event: str) -> list[str]:
        out: list[str] = []
        for _, root in self._scopes():
            hf = root / "hooks.yaml"
            if hf.is_file():
                data = yaml.safe_load(hf.read_text()) or {}
                for c in (data.get(event) or []):
                    if isinstance(c, str):
                        out.append(c)
                    else:  # YAML mapping (unquoted colon) — surface, don't mangle
                        out.append(f"false # invalid hook entry (quote it): {c!r}")
        return out

    def run_hooks(self, event: str, env: dict | None = None,
                  timeout: int = 30) -> list[dict]:
        results = []
        for cmd in self.hooks(event):
            try:
                p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                   timeout=timeout, env={**os.environ, **(env or {})})
                results.append({"cmd": cmd, "exit": p.returncode,
                                "out": p.stdout[-2000:], "err": p.stderr[-500:]})
            except subprocess.TimeoutExpired:
                results.append({"cmd": cmd, "exit": -1, "out": "", "err": "hook timeout"})
        return results

    # ---------------------------------------------------------------- config + credentials
    def config(self) -> dict:
        out: dict = {}
        for _, root in self._scopes():
            c = root / "config.yaml"
            if c.is_file():
                out.update(yaml.safe_load(c.read_text()) or {})
        return out

    def credentials_path(self) -> Path:
        return self.global_dir / "credentials.json"

    def set_credential(self, provider: str, key: str) -> None:
        p = self.credentials_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(p.read_text()) if p.is_file() else {}
        data[provider] = {"api_key": key}
        p.write_text(json.dumps(data, indent=2))
        p.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600

    def get_credential(self, provider: str) -> str:
        p = self.credentials_path()
        if p.is_file():
            return (json.loads(p.read_text()).get(provider) or {}).get("api_key", "")
        return ""
