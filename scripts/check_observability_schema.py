#!/usr/bin/env python3
"""Every stored run-evidence record must validate against its observability schema."""
import sys

from utag_core import observe

if __name__ == "__main__":
    runs = observe.load_runs()
    problems = [f"{rid}: {p}" for rid, text in runs.items() for p in observe.validate_jsonl(text)]
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    print(f"check_observability_schema: {len(runs)} run(s), {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
