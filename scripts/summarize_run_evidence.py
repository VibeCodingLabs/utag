#!/usr/bin/env python3
"""Write the observability summary to reports/observability/summary.md."""
import sys

from utag_cli.main import main as cli_main

if __name__ == "__main__":
    sys.exit(cli_main(["observe", "summary", "--out", "reports/observability/summary.md"]))
