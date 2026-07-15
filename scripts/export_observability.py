#!/usr/bin/env python3
"""Export all stored run evidence to reports/observability/events.jsonl (validated)."""
import sys

from utag_cli.main import main as cli_main

if __name__ == "__main__":
    sys.exit(cli_main(["observe", "export", "--format", "jsonl",
                       "--out", "reports/observability/events.jsonl"]))
