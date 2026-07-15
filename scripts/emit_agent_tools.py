#!/usr/bin/env python3
"""Emit the harness tool catalog as validated MCPToolContracts.

Writes:
  fixtures/agent-tools/<name>.json   one contract per tool
  fixtures/agent-tools/catalog.json  a single MCP tools array (server manifest)
"""
import json
import sys
from pathlib import Path

from utag_core.agent_tools import build_catalog

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures" / "agent-tools"

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = build_catalog()
    for contract in catalog:
        name = contract.extensions["harness_name"]
        (OUT / f"{name}.json").write_text(
            contract.model_dump_json(indent=2, exclude_none=True) + "\n")
    manifest = {"tools": [json.loads(c.model_dump_json(exclude_none=True)) for c in catalog]}
    (OUT / "catalog.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"emit_agent_tools: {len(catalog)} tools -> {OUT}")
    sys.exit(0)
