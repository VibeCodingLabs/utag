#!/usr/bin/env bash
# UTAG autoresearch harness.
#   --strict   run the suite; exit non-zero if pytest fails (CI default)
#   --compare  run the suite for metrics only; never fails the run
# PYTEST_CMD overrides the test command (used by tests/unit/test_autoresearch_harness.py).
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:---strict}"
PYTEST_CMD="${PYTEST_CMD:-uv run pytest}"

run_metrics() {
  local out rc=0
  out=$(mktemp)
  $PYTEST_CMD >"$out" 2>&1 || rc=$?
  local passed failed
  passed=$(grep -oE '[0-9]+ passed' "$out" | tail -1 | grep -oE '[0-9]+' || true)
  failed=$(grep -oE '[0-9]+ failed' "$out" | tail -1 | grep -oE '[0-9]+' || true)
  echo "METRIC passed_tests=${passed:-0}"
  echo "METRIC failed_tests=${failed:-0}"
  return $rc
}

case "$MODE" in
  --strict)
    run_metrics
    ;;
  --compare)
    rc=0
    run_metrics || rc=$?
    if [ "$rc" -ne 0 ]; then
      echo "WARN pytest exited $rc — comparison-only mode, not failing the run"
    fi
    # ponytail: historical-zip replay not implemented; old release zips carry no
    # stored test output, so replaying them means a full unzip+uv sync per zip.
    # Add here when cross-version metric trends are actually needed.
    exit 0
    ;;
  *)
    echo "usage: autoresearch.sh [--strict|--compare]" >&2
    exit 2
    ;;
esac
