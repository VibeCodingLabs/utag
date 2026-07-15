#!/usr/bin/env python3
"""Generated-UI gate: regeneration is byte-identical to what's on disk (or absent),
and no hardcoded colors leak outside the token/theme files."""
import re
import sys
from pathlib import Path

from utag_core.ir import ModuleSpec
from utag_core.registry import get_generator

import utag_generators  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
UI_SRC = ROOT / "packages/ui/src"
DESIGN_TARGETS = ("design-tokens-css", "tailwind-v4-theme", "react-component-library")
TOKEN_FILES = {"styles/tokens.css", "styles/theme.css", "styles/dark.css",
               "styles/tokens.json", "styles/css-variables.manifest.json"}
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")

if __name__ == "__main__":
    module = ModuleSpec(name="design", description="design.yaml",
                        provenance={"design_yaml": (ROOT / "design.yaml").read_text()})
    problems = []
    for target in DESIGN_TARGETS:
        for rel, content in sorted(get_generator(target).generate(module).items()):
            if rel not in TOKEN_FILES and HEX_COLOR.search(content):
                problems.append(f"{rel}: hardcoded color outside token files")
            on_disk = UI_SRC / rel
            if on_disk.is_file() and on_disk.read_text() != content:
                problems.append(f"{rel}: stale on disk vs design.yaml (run scripts/generate_ui.py)")
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    print(f"check_generated_ui: {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
