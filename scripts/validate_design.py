#!/usr/bin/env python3
"""Validate a design.yaml against the strict DesignYaml contract."""
import sys
from pathlib import Path

from utag_core.schemas.tools import validate_file

if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "design.yaml")
    errs = validate_file("design-yaml", path)
    for e in errs:
        print(f"FAIL {e}", file=sys.stderr)
    print(f"validate_design: {path} — {'INVALID' if errs else 'valid'}")
    sys.exit(1 if errs else 0)
