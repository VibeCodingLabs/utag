#!/usr/bin/env python3
"""Execute an autoresearch task: python scripts/autoresearch_task.py task.yaml [--mode dry-run]"""
import sys

from utag_cli.main import main as cli_main

if __name__ == "__main__":
    args = sys.argv[1:]
    task = args[0] if args else "task.yaml"
    mode = args[args.index("--mode") + 1] if "--mode" in args else "local"
    sys.exit(cli_main(["autoresearch", "execute", "--task", task, "--mode", mode]))
