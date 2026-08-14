#!/bin/bash
# Collect run records into result/ and push them back to GitHub for analysis.
#
# Usage (from src/ on the cluster, inside the repo clone):
#   bash cluster/sync_results.sh phase1        # collects runs/phase1
#   bash cluster/sync_results.sh phase2 mylabel
#
# What it does:
#   1. aggregates runs/<exp>/**/*.jsonl into result/<exp>/<stamp>/records.csv
#   2. copies loop/sweep checkpoint summaries (outcomes, switches) alongside
#   3. git add + commit + push (current branch)
# Raw runs/ stays on the cluster (gitignored); only distilled results travel.
set -euo pipefail

EXP="${1:?usage: sync_results.sh <experiment> [label]}"
LABEL="${2:-$(date -u +%Y%m%dT%H%M%SZ)}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
RUNS="${SRC_DIR}/runs/${EXP}"
OUT="${REPO_DIR}/result/${EXP}/${LABEL}"

[ -d "${RUNS}" ] || { echo "no runs at ${RUNS}"; exit 1; }
mkdir -p "${OUT}"

cd "${SRC_DIR}"
python -m egglab.collect "${RUNS}" -o "${OUT}/records.csv"

# summaries: every checkpoint json (small) for outcomes/switch lists
find "${RUNS}" -name '*.ckpt.json' | while read -r f; do
  rel="${f#"${RUNS}"/}"
  mkdir -p "${OUT}/checkpoints/$(dirname "${rel}")"
  cp "${f}" "${OUT}/checkpoints/${rel}"
done

cd "${REPO_DIR}"
git add "result/${EXP}/${LABEL}"
git commit -m "results: ${EXP} ${LABEL} ($(hostname))"
git push
echo "synced to result/${EXP}/${LABEL} and pushed"
