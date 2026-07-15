"""Harness tool catalog as strict MCPToolContracts.

Turns the agent harness's built-in tools (read, bash, edit, …) into governed
`MCPToolContract` records: typed input schema, side-effect classification,
auth-scope hints, and a policy status the MCP gateway can enforce. Contract
`name` is a slug (underscores → hyphens); the original harness name is kept
under `extensions.harness_name`.
"""
from __future__ import annotations

from utag_core.schemas.mcp import MCPToolContract, PolicyStatus, SideEffect

# side_effect drives the default policy: read/none auto-allowed, write allowed,
# network/destructive default to review (a human/gateway must sanction them).
_DEFAULT_POLICY = {
    SideEffect.none: PolicyStatus.allowed,
    SideEffect.read: PolicyStatus.allowed,
    SideEffect.write: PolicyStatus.allowed,
    SideEffect.network: PolicyStatus.review,
    SideEffect.destructive: PolicyStatus.review,
}


def _obj(props: dict[str, dict], required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required,
            "additionalProperties": False}


def _s(desc: str) -> dict:
    return {"type": "string", "description": desc}


# (harness_name, description, side_effect, auth_scopes, input_schema, output_schema|None)
_TOOLS: list[tuple] = [
    ("read", "Read files, directories, archives, SQLite, images, documents, internal resources, and web URLs via one path.",
     SideEffect.read, ["fs:read", "net:read"],
     _obj({"path": _s("local path, internal URI, or URL; append :<sel> for ranges/modes")}, ["path"]),
     None),
    ("bash", "Run a single binary or short pipeline in a shell session (git, bun, cargo, python).",
     SideEffect.destructive, ["exec"],
     _obj({"command": _s("the command to run"),
           "cwd": _s("working directory"),
           "timeout": {"type": "integer", "description": "wall-clock cap (seconds)"},
           "async": {"type": "boolean", "description": "run in background"}}, ["command"]),
     _obj({"stdout": _s("merged stdout+stderr"), "exit_code": {"type": "integer"}}, ["stdout"])),
    ("edit", "Line/block-addressed patch: replace, delete, or insert content in an existing file.",
     SideEffect.write, ["fs:write"],
     _obj({"patch": _s("edit ops (SWAP/DEL/INS) with [PATH#TAG] headers and +body rows")}, ["patch"]),
     None),
    ("ast_grep", "Structural code search via ast-grep (syntax shape, not text).",
     SideEffect.read, ["fs:read"],
     _obj({"pat": _s("one AST pattern with $META vars"), "path": _s("scoped search path"),
           "lang": _s("language")}, ["pat", "path"]),
     None),
    ("ast_edit", "Structural AST-aware rewrite via ast-grep (safe codemods).",
     SideEffect.write, ["fs:write"],
     _obj({"pat": _s("AST match pattern"), "out": _s("rewrite template ('' deletes)"),
           "path": _s("scoped path"), "lang": _s("language")}, ["pat", "out", "path"]),
     None),
    ("ask", "Ask the user to clarify or choose between approaches.",
     SideEffect.none, ["user:prompt"],
     _obj({"questions": {"type": "array", "description": "questions with options",
                         "items": {"type": "object"}}}, ["questions"]),
     _obj({"answers": {"type": "object"}}, ["answers"])),
    ("debug", "Debugger access: launch/attach, breakpoints, stepping, inspection.",
     SideEffect.write, ["exec", "process:control"],
     _obj({"action": _s("launch|attach|continue|step_over|…"), "program": _s("target"),
           "adapter": _s("debugpy|gdb|lldb-dap|dlv dap")}, ["action"]),
     None),
    ("eval", "Run one step of code in a persistent kernel (py or js).",
     SideEffect.destructive, ["exec"],
     _obj({"language": {"type": "string", "enum": ["py", "js"]},
           "code": _s("cell body, verbatim"), "title": _s("transcript label"),
           "reset": {"type": "boolean", "description": "wipe the kernel first"}},
          ["language", "code"]),
     _obj({"result": _s("cell output")}, [])),
    ("github", "Op-based gh wrapper: repos, PRs, search, checkout, push, Actions watch.",
     SideEffect.network, ["repo", "net:write"],
     _obj({"op": _s("repo_view|pr_create|pr_checkout|pr_push|search_*|run_watch"),
           "repo": _s("owner/repo (defaults to checkout)")}, ["op"]),
     None),
    ("glob", "Glob files and directories via fast pattern matching.",
     SideEffect.read, ["fs:read"],
     _obj({"path": _s("glob, file, or directory; ';'-delimited for many"),
           "gitignore": {"type": "boolean"}, "hidden": {"type": "boolean"}}, ["path"]),
     None),
    ("grep", "Grep files using RE2-style regex.",
     SideEffect.read, ["fs:read"],
     _obj({"pattern": _s("Rust regex; no lookaround/backrefs"),
           "path": _s("scoped path(s)")}, ["pattern"]),
     None),
    ("lsp", "Symbol-aware code intelligence: definition, references, rename, diagnostics.",
     SideEffect.write, ["fs:read", "fs:write"],
     _obj({"operation": _s("definition|references|rename|diagnostics|symbols|…"),
           "file": _s("target file"), "line": {"type": "integer"},
           "symbol": _s("substring on that line"), "new_name": _s("for rename")},
          ["operation"]),
     None),
    ("browser", "Drive a real Chromium tab; full puppeteer access via JS.",
     SideEffect.network, ["net:read", "net:write", "exec"],
     _obj({"action": {"type": "string", "enum": ["open", "close", "run"]},
           "name": _s("tab name (default 'main')"), "url": _s("navigate on open"),
           "code": _s("async JS body for run")}, ["action"]),
     None),
    ("task", "Delegate work to background subagents via a tasks[] batch.",
     SideEffect.write, ["agent:spawn", "exec"],
     _obj({"context": _s("shared Goal/Constraints/Contract"),
           "tasks": {"type": "array", "description": "subagent assignments",
                     "items": {"type": "object"}},
           "agent": _s("base agent type")}, ["tasks"]),
     _obj({"agent_ids": {"type": "array", "items": {"type": "string"}}}, [])),
    ("job", "Manage async background tasks: poll, cancel, list.",
     SideEffect.write, ["process:control"],
     _obj({"poll": {"type": "array", "items": {"type": "string"}},
           "cancel": {"type": "array", "items": {"type": "string"}},
           "list": {"type": "boolean"}}, []),
     None),
    ("irc", "Send/receive short messages between agents in this process.",
     SideEffect.none, ["agent:message"],
     _obj({"op": {"type": "string", "enum": ["send", "wait", "inbox", "list"]},
           "to": _s("peer id or 'all'"), "message": _s("plain prose"),
           "replyTo": _s("correlate a reply")}, ["op"]),
     None),
    ("todo", "Manage the phased task list (init/start/done/drop/append/view).",
     SideEffect.write, ["session:state"],
     _obj({"op": _s("init|start|done|drop|rm|append|view"),
           "task": _s("verbatim task content"),
           "items": {"type": "array", "items": {"type": "string"}}}, ["op"]),
     None),
    ("web_search", "Search the web for up-to-date information beyond the knowledge cutoff.",
     SideEffect.network, ["net:read"],
     _obj({"query": _s("search query")}, ["query"]),
     _obj({"results": {"type": "array", "items": {"type": "object"}}}, ["results"])),
    ("write", "Create or overwrite a file at a path (also archive/SQLite entries).",
     SideEffect.write, ["fs:write"],
     _obj({"path": _s("destination path"), "content": _s("full file contents")},
          ["path", "content"]),
     None),
    ("learn", "Capture a reusable lesson into long-term memory; optionally mint/enhance a managed skill.",
     SideEffect.write, ["memory:write", "skill:write"],
     _obj({"lesson": _s("the reusable insight"),
           "skill": {"type": "object", "description": "optional managed-skill spec"}},
          ["lesson"]),
     None),
    ("manage_skill", "Create, update, or delete a managed SKILL.md in the isolated skills dir.",
     SideEffect.write, ["skill:write"],
     _obj({"action": {"type": "string", "enum": ["create", "update", "delete"]},
           "name": _s("kebab-case skill name"), "description": _s("discovery text"),
           "body": _s("skill body, no frontmatter")}, ["action", "name"]),
     None),
    ("resolve", "Resolve a pending action — apply or discard.",
     SideEffect.write, ["session:state"],
     _obj({"action": {"type": "string", "enum": ["apply", "discard"]},
           "reason": _s("one-sentence why"), "extra": {"type": "object"}},
          ["action", "reason"]),
     None),
    ("generate_image", "Generate or edit images from a detailed subject prompt.",
     SideEffect.write, ["media:write"],
     _obj({"subject": _s("detailed image prompt")}, ["subject"]),
     _obj({"image_path": _s("path to the generated image")}, ["image_path"])),
]


def _slug(name: str) -> str:
    return name.replace("_", "-")


def build_catalog() -> list[MCPToolContract]:
    out = []
    for name, desc, effect, scopes, input_schema, output_schema in _TOOLS:
        out.append(MCPToolContract(
            name=_slug(name), description=desc, input_schema=input_schema,
            output_schema=output_schema, side_effect=effect,
            auth_scopes=scopes, policy_status=_DEFAULT_POLICY[effect],
            extensions={"harness_name": name}))
    return out


#: harness_name -> MCPToolContract
CATALOG: dict[str, MCPToolContract] = {c.extensions["harness_name"]: c for c in build_catalog()}
