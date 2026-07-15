#!/usr/bin/env python3
"""Assert every registered generator/importer/validator is reachable.

Reachable means: exposed through a generic CLI route (`utag generate --target`,
`utag validate --kind`) or documented as public API in README/AGENTS/docs.
Exits 1 listing every unreachable entry.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_CLI_COMMANDS = ("generate", "validate", "targets", "intel", "openapi", "schema", "registry")


def cli_help_text() -> str:
    from utag_cli.main import main as cli_main

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.suppress(SystemExit):
        cli_main(["--help"])
    return buf.getvalue()


def docs_text() -> str:
    files = [ROOT / "README.md", ROOT / "AGENTS.md"]
    files += sorted((ROOT / "docs").rglob("*.md"))
    return "\n".join(p.read_text() for p in files if p.is_file())


def main() -> int:
    import utag_generators  # noqa: F401  registers everything

    from utag_core.registry import GENERATORS, IMPORTERS, VALIDATORS

    problems: list[str] = []

    help_text = cli_help_text()
    for cmd in REQUIRED_CLI_COMMANDS:
        if cmd not in help_text:
            problems.append(f"CLI: `utag {cmd}` missing from --help")

    for target, gen in sorted(GENERATORS.items()):
        if not callable(getattr(gen, "generate", None)):
            problems.append(f"generator {target}: no callable generate()")

    for kind, fn in sorted(VALIDATORS.items()):
        if not callable(fn):
            problems.append(f"validator {kind}: not callable")

    # Importers have no generic CLI route yet; they must be documented public API.
    docs = docs_text()
    for fmt, imp in sorted(IMPORTERS.items()):
        if not callable(getattr(imp, "ingest", None)):
            problems.append(f"importer {fmt}: no callable ingest()")
        elif fmt not in docs:
            problems.append(f"importer {fmt}: no CLI route and not documented in README/AGENTS/docs")

    if problems:
        print(f"check_entrypoints: {len(problems)} unreachable entrypoint(s):")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(
        f"check_entrypoints: OK — {len(GENERATORS)} generators, "
        f"{len(VALIDATORS)} validators, {len(IMPORTERS)} importers reachable"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
