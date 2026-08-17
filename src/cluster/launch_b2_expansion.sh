#!/bin/bash
# Guarded launcher for the B2 208-cell matched expansion (Option B).
#
# Usage (interactive Unicorn login prompt, in src/):
#   bash cluster/launch_b2_expansion.sh
#
# Guards: sbatch present; GRB backend via unicorn_env.sh; the driver's
# --list must report EXACTLY 208 cells (never hard-code silently); array is
# derived from that count with concurrency capped at %12 (matches the
# pilots' cluster etiquette; ~18 waves, comfortably overnight). Refuses to
# submit if the pilot instances leaked into the grid (the driver's tests
# enforce disjointness, but the launcher independently rejects any
# {a2,a3,a4,a5}_s0_/s11_/s15_ cell directory pattern in --list output).
# Writes a manifest under runs/b2_expansion/. Never `sbatch --wrap`.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run from an interactive Unicorn login prompt." >&2
    exit 127
fi
source "${SRC_DIR}/cluster/unicorn_env.sh"

LIST="$(python experiments/run_b2_expansion.py --list)"
N="$(printf '%s\n' "${LIST}" | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "208" ]]; then
    echo "ERROR: expansion --list reports ${N} cells; expected exactly 208. Refusing to submit." >&2
    exit 1
fi
if printf '%s\n' "${LIST}" | grep -E "'seed': (0|11|15)," >/dev/null; then
    echo "ERROR: --list contains pilot seeds (0/11/15); the expansion must be disjoint from result/b2_pilot. Refusing to submit." >&2
    exit 1
fi
CONC=12

JOB="$(sbatch --parsable --array="0-$((N - 1))%${CONC}" cluster/submit_b2_expansion.sub)"
mkdir -p runs/b2_expansion
MANIFEST="runs/b2_expansion/MANIFEST-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
    printf 'campaign=b2-208-cell-matched-expansion (Option B, DECISION_LOG 2026-08-17)\n'
    printf 'cells=%s (verified from --list; 52 instances x methods a2,a3,a4,a5)\n' "${N}"
    printf 'grid=seeds 0-15 minus pilot {0,11,15} x n{8,12} x b{0.01,0.05}\n'
    printf 'array=0-%s%%%s\n' "$((N - 1))" "${CONC}"
    printf 'epsilon=1e-2; budget=240 exact oracle calls; settings identical to the pilots\n'
    printf 'purpose=population robustness for the kill decision; NOT a scale test\n'
    printf 'certification is an outcome, not an audit gate (acc-1 tests >= 95%%)\n'
    printf 'job_id=%s\n' "${JOB}"
    printf 'git_commit=%s\n' "$(git -C "${REPO_DIR}" rev-parse HEAD)"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${MANIFEST}"
echo "[submitted] b2 expansion: ${N} cells as job ${JOB} (manifest: ${MANIFEST})"
squeue --jobs="${JOB}"
