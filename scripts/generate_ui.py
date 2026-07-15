#!/usr/bin/env python3
"""Generate the full UI (tokens + tailwind + components/layouts/routes) from design.yaml."""
import argparse
import sys

from utag_cli.main import main as cli_main

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="design.yaml")
    ap.add_argument("--out", default="packages/ui/src/")
    a = ap.parse_args()
    sys.exit(cli_main(["design", "app", "--input", a.design, "--out", a.out]))
