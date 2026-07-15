#!/usr/bin/env python3
"""Score receipts under reports/autoresearch/: gate pass ratio per task + overall."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    receipts = sorted((ROOT / "reports/autoresearch").glob("*.receipt.json"))
    if not receipts:
        print("autoresearch_score: no receipts found")
        sys.exit(0)
    total = passed = 0
    for path in receipts:
        receipt = json.loads(path.read_text())
        gates = receipt.get("gates", [])
        ok = sum(1 for g in gates if g["passed"])
        total += len(gates)
        passed += ok
        print(f"{receipt['task_id']}: {ok}/{len(gates)} gates passed")
    print(f"METRIC autoresearch_gate_pass_ratio={passed / total:.3f}" if total else "no gates")
    sys.exit(0)
