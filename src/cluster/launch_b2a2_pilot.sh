#!/bin/bash
# Guarded launcher for the B2-A2 12-cell pilot.
#
# Usage (interactive Unicorn login prompt, in src/):
#   bash cluster/launch_b2a2_pilot.sh
#
# Guards: sbatch present; GRB backend via unicorn_env.sh; the driver's
# --list must report EXACTLY 12 cells (never hard-code silently); array is
# derived from that count with concurrency capped at %12. Writes a manifest
# under runs/b2a2_pilot/. Never `sbatch --wrap`.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run from an interactive Unicorn login prompt." >&2
    exit 127
fi
source "${SRC_DIR}/cluster/unicorn_env.sh"

N="$(python experiments/run_b2a2_pilot.py --list | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "12" ]]; then
    echo "ERROR: pilot --list reports ${N} cells; expected exactly 12. Refusing to submit." >&2
    exit 1
fi
CONC=12  # spec: concurrency no higher than %12

JOB="$(sbatch --parsable --array="0-$((N - 1))%${CONC}" cluster/submit_b2a2_pilot.sub)"
mkdir -p runs/b2a2_pilot
MANIFEST="runs/b2a2_pilot/MANIFEST-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
    printf 'campaign=b2a2-pilot\n'
    printf 'cells=%s (verified from --list)\n' "${N}"
    printf 'array=0-%s%%%s\n' "$((N - 1))" "${CONC}"
    printf 'method=A2; epsilon=1e-2; budget=240 exact pricing calls\n'
    printf 'grid=seeds{0,11,15} x n{8,12} x b{0.01,0.05}\n'
    printf 'job_id=%s\n' "${JOB}"
    printf 'git_commit=%s\n' "$(git -C "${REPO_DIR}" rev-parse HEAD)"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${MANIFEST}"
echo "[submitted] b2a2 pilot: ${N} cells as job ${JOB} (manifest: ${MANIFEST})"
squeue --jobs="${JOB}"
