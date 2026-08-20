#!/bin/bash
# Guarded launcher for the B3 internal-uplift factor pilot (60 cells, A2 only).
#
# Usage (interactive Unicorn login prompt, in src/):
#   bash cluster/launch_b3_factor_pilot.sh
#
# Guards:
#   - sbatch present (refuse off-cluster submission);
#   - Gurobi-ONLY backend: unicorn_env.sh + EGGLAB_REQUIRE_GRB=1 so a
#     non-GRB fallback aborts instead of silently using CBC;
#   - the driver's --dry-run must pass (binds every cell to the FROZEN
#     factor-screen artifact SHA, selected levels, and 30 instance hashes;
#     refuses A6/reserved seeds/factor drift);
#   - the driver's --list must report EXACTLY 60 cells (never hard-coded);
#   - a clean tracked tree (the driver refuses a dirty tree per cell too).
# Writes a manifest under runs/b3_factor_pilot/. Never `sbatch --wrap`.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run from an interactive Unicorn login prompt." >&2
    exit 127
fi

# Gurobi-only: force the GRB backend and refuse a non-GRB fallback.
export EGGLAB_REQUIRE_GRB=1
source "${SRC_DIR}/cluster/unicorn_env.sh"

# Refuse a dirty tracked tree before submitting anything.
if [[ -n "$(git -C "${REPO_DIR}" status --porcelain | grep -v '^??' || true)" ]]; then
    echo "ERROR: tracked tree is dirty; commit before launching the pilot." >&2
    exit 1
fi

# Binding + count preflight (fails closed on factor drift / A6 / bad screen).
python experiments/run_b3_factor_pilot.py --dry-run

N="$(python experiments/run_b3_factor_pilot.py --list | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "60" ]]; then
    echo "ERROR: pilot --list reports ${N} cells; expected exactly 60. Refusing to submit." >&2
    exit 1
fi
CONC=60  # full-width concurrency (one task per cell)

JOB="$(sbatch --parsable --array="0-$((N - 1))%${CONC}" cluster/submit_b3_factor_pilot.sub)"
mkdir -p runs/b3_factor_pilot
MANIFEST="runs/b3_factor_pilot/MANIFEST-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
    printf 'campaign=b3-factor-pilot\n'
    printf 'cells=%s (verified from --list)\n' "${N}"
    printf 'array=0-%s%%%s\n' "$((N - 1))" "${CONC}"
    printf 'method=A2; epsilon=1e-2; budget=240 exact pricing calls; tol_d=1e-2\n'
    printf 'design=5 frozen settings x seeds{0,11,15} x n{8,12} x b{0.01,0.05}\n'
    printf 'frozen_screen=result/b3_factor_screen/20260820T105318Z\n'
    printf 'screen_record_sha256=27c04d82bc88b62eed84394569b3ab8a35238a3a57c9cf4ba6463fb85f7bf603\n'
    printf 'backend=GRB (EGGLAB_REQUIRE_GRB=1)\n'
    printf 'job_id=%s\n' "${JOB}"
    printf 'git_commit=%s\n' "$(git -C "${REPO_DIR}" rev-parse HEAD)"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${MANIFEST}"
echo "[submitted] b3 factor pilot: ${N} cells as job ${JOB} (manifest: ${MANIFEST})"
squeue --jobs="${JOB}"
