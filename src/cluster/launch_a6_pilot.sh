#!/bin/bash
# Guarded launcher for the A6 burned-seed pilot (EXACTLY 24 cells).
#
# Usage (interactive Unicorn login prompt, in src/):
#   bash cluster/launch_a6_pilot.sh
#
# Guards: sbatch present; GRB backend via unicorn_env.sh; the driver's
# --list must report EXACTLY 24 cells; refuses any holdout seed (>= 16)
# leaking into the grid; array derived from --list with %12 concurrency.
# Writes a manifest under runs/a6_pilot/. Never `sbatch --wrap`.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run from an interactive Unicorn login prompt." >&2
    exit 127
fi
source "${SRC_DIR}/cluster/unicorn_env.sh"

LIST="$(python experiments/run_a6_pilot.py --list)"
N="$(printf '%s\n' "${LIST}" | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "24" ]]; then
    echo "ERROR: pilot --list reports ${N} cells; expected exactly 24. Refusing to submit." >&2
    exit 1
fi
if printf '%s\n' "${LIST}" | grep -E "'seed': (1[6-9]|2[0-9]|3[0-9]|[4-9][0-9])," >/dev/null; then
    echo "ERROR: --list contains holdout-range seeds (>= 16); the pilot must use burned seeds only. Refusing to submit." >&2
    exit 1
fi
CONC=12

JOB="$(sbatch --parsable --array="0-$((N - 1))%${CONC}" cluster/submit_a6_pilot.sub)"
mkdir -p runs/a6_pilot
MANIFEST="runs/a6_pilot/MANIFEST-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
    printf 'campaign=a6-burned-pilot (spec doc/A6_SPARSE_STABILIZATION_SPEC.md Section 7)\n'
    printf 'cells=%s (verified from --list; 12 a6_a4 + 12 a6_a3)\n' "${N}"
    printf 'grid=BURNED seeds {0,11,15} x n{8,12} x b{0.01,0.05}; holdout seeds 16-31 excluded\n'
    printf 'array=0-%s%%%s\n' "$((N - 1))" "${CONC}"
    printf 'epsilon=1e-2; budget=240; scheduler theta_cert=0.1, K_MAX=4, priority T0>T4>T3>T1>T2>default\n'
    printf 'purpose=implementation gates + one-shot arm selection; dev-only, uncitable as evaluation\n'
    printf 'job_id=%s\n' "${JOB}"
    printf 'git_commit=%s\n' "$(git -C "${REPO_DIR}" rev-parse HEAD)"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${MANIFEST}"
echo "[submitted] a6 pilot: ${N} cells as job ${JOB} (manifest: ${MANIFEST})"
squeue --jobs="${JOB}"
