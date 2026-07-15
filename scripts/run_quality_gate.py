#!/usr/bin/env python3
"""Release quality gate: run every gate, write a report, fail on any failure.

Usage: python scripts/run_quality_gate.py [--release vX.Y.Z]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (name, command, required) — optional gates are skipped with a note when the
# tool is absent, never silently.
GATES: list[tuple[str, list[str], bool]] = [
    ("pytest", ["uv", "run", "pytest"], True),
    ("entrypoints", ["uv", "run", "python", "scripts/check_entrypoints.py"], True),
    ("schemas", ["uv", "run", "python", "scripts/validate_schemas.py"], True),
    ("schema-fixtures", ["uv", "run", "python", "scripts/check_schema_fixtures.py"], True),
    ("schema-extensions", ["uv", "run", "python", "scripts/check_no_unknown_schema_extensions.py"], True),
    ("design", ["uv", "run", "python", "scripts/validate_design.py", "design.yaml"], True),
    ("generated-ui", ["uv", "run", "python", "scripts/check_generated_ui.py"], True),
    ("accessibility", ["uv", "run", "python", "scripts/check_accessibility_contracts.py"], True),
    ("registry-doctor", ["uv", "run", "utag", "registry", "doctor"], True),
    ("automation-doctor", ["uv", "run", "utag", "automation", "doctor"], True),
    ("observability", ["uv", "run", "python", "scripts/check_observability_schema.py"], True),
    ("ai-doctor", ["uv", "run", "utag", "ai", "doctor"], True),
    ("ruff", ["uv", "run", "--with", "ruff", "ruff", "check", "."], False),
]

# gates that are REQUIRED whenever their toolchain is present, and an explicit
# SKIP note otherwise (never silent): (name, command, availability probe)
CONDITIONAL_GATES: list[tuple[str, list[str], "object"]] = [
    ("ui-typecheck", ["npm", "--prefix", "packages/ui", "run", "typecheck"],
     lambda: shutil.which("npm") and (ROOT / "packages/ui/node_modules").is_dir()),
    ("ui-build", ["npm", "--prefix", "packages/ui", "run", "build"],
     lambda: shutil.which("npm") and (ROOT / "packages/ui/node_modules").is_dir()),
]


def run_gate(name: str, cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-5:])
    return proc.returncode == 0, tail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default="unversioned")
    a = ap.parse_args()

    lines = [f"# Quality gate — {a.release}", ""]
    failed = False
    for name, cmd, required in GATES:
        if not required and shutil.which(cmd[0]) is None:
            lines.append(f"- SKIPPED (optional, `{cmd[0]}` unavailable): {name}")
            print(f"SKIP {name}: {cmd[0]} unavailable")
            continue
        ok, tail = run_gate(name, cmd)
        status = "PASS" if ok else "FAIL"
        if not ok and required:
            failed = True
        if not ok and not required:
            lines.append(f"- WARN (optional gate failed): {name}")
            print(f"WARN {name} (optional)\n{tail}")
            continue
        lines.append(f"- {status}: {name} — `{' '.join(cmd)}`")
        print(f"{status} {name}")
        if not ok:
            print(tail)

    for name, cmd, available in CONDITIONAL_GATES:
        if not available():
            lines.append(f"- SKIPPED (toolchain absent — install node + `npm --prefix packages/ui install`): {name}")
            print(f"SKIP {name}: toolchain absent")
            continue
        ok, tail = run_gate(name, cmd)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed = True
            print(tail)
        lines.append(f"- {status}: {name} — `{' '.join(cmd)}` (required: toolchain present)")
        print(f"{status} {name}")

    report_dir = ROOT / "reports" / a.release
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "quality-gate.md").write_text("\n".join(lines) + "\n")
    print(f"report: reports/{a.release}/quality-gate.md")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
