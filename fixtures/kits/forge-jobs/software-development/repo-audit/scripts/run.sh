#!/usr/bin/env bash
# lib.sh contract: REPORT="$FJ_STATE/output/$JOB_ID/$(date +%F)/report.md"
set -euo pipefail
FJ_STATE="${FORGE_JOBS_STATE:-$HOME/.local/share/forge-jobs}"
OUT="$FJ_STATE/output/repo-audit/$(date +%F)"
mkdir -p "$OUT"
printf '# repo audit report\n\nrepo state: fixture-clean\n' > "$OUT/report.md"
echo "wrote $OUT/report.md"
