#!/usr/bin/env python3
"""Print the completion receipt for a task: python scripts/autoresearch_receipt.py task.yaml"""
import sys

from utag_cli.main import main as cli_main

if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "task.yaml"
    sys.exit(cli_main(["autoresearch", "receipt", "--task", task]))
