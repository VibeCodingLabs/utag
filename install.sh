#!/usr/bin/env bash
# utag one-liner install:  curl -fsSL <raw-url>/install.sh | bash
# Installs the workspace (uv preferred, pip fallback), scaffolds ~/.utag, builds
# the control-plane when Go exists. Idempotent; no sudo.
set -euo pipefail
REPO="${UTAG_REPO:-.}"
if [ ! -f "$REPO/pyproject.toml" ]; then
  echo "utag: run from a checkout or set UTAG_REPO"; exit 1
fi
cd "$REPO"
if command -v uv >/dev/null 2>&1; then
  uv sync
  BIN="uv run"
else
  pip install --user -e packages/python/utag-core -e packages/python/utag-adapters \
    -e packages/python/utag-generators -e packages/python/utag-worker \
    -e packages/python/utag-cli -e packages/python/utag-tui -e packages/python/utag-veriforge
  BIN=""
fi
$BIN utag init
command -v go >/dev/null 2>&1 && (cd control-plane && CGO_ENABLED=0 go build -o utag-control-plane . \
  && echo "control-plane built: control-plane/utag-control-plane") || \
  echo "go not found — skipping control-plane build (TUI session works without it)"
echo "done. start:  utag-tui   |   utag models --provider anthropic   |   utag login <provider>"
