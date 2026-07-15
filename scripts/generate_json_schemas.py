#!/usr/bin/env python3
"""Emit every strict schema to schemas/ and regenerate fixtures/schemas/."""
import sys
from pathlib import Path

from utag_core.schemas import tools

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    schemas = tools.emit_all(ROOT / tools.SCHEMAS_DIR)
    fixtures = tools.write_fixtures(ROOT)
    print(f"emitted {len(schemas)} schemas, {len(fixtures)} fixtures")
    sys.exit(0)
