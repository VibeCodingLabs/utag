#!/usr/bin/env python3
"""Validate all schema fixtures, emitted-schema freshness, and design.yaml."""
import argparse
import sys
from pathlib import Path

from utag_core.schemas import SCHEMAS, tools

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    problems = tools.validate_all(Path(a.root))
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    print(f"validate_schemas: {len(SCHEMAS)} kinds, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
