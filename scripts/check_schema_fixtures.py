#!/usr/bin/env python3
"""Every schema kind must have a passing valid fixture and a rejected invalid fixture."""
import sys
from pathlib import Path

from utag_core.schemas import SCHEMAS, tools

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    fdir = ROOT / tools.FIXTURES_DIR
    problems = []
    for kind in sorted(SCHEMAS):
        valid, invalid = fdir / f"{kind}.valid.json", fdir / f"{kind}.invalid.json"
        if not valid.is_file() or not invalid.is_file():
            problems.append(f"{kind}: fixture pair missing")
            continue
        if tools.validate_file(kind, valid):
            problems.append(f"{kind}: valid fixture rejected")
        if not tools.validate_file(kind, invalid):
            problems.append(f"{kind}: invalid fixture accepted")
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    print(f"check_schema_fixtures: {len(SCHEMAS)} kinds, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
