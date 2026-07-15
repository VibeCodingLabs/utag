#!/usr/bin/env python3
"""Every schema must forbid unknown properties and expose the `extensions` escape hatch."""
import sys

from utag_core.schemas import SCHEMAS
from utag_core.schemas.tools import check_no_unknown_extensions

if __name__ == "__main__":
    problems = check_no_unknown_extensions()
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    print(f"check_no_unknown_schema_extensions: {len(SCHEMAS)} kinds, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
