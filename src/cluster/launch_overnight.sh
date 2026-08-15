#!/bin/bash
# Submit the targeted overnight experiment suite from a Unicorn login shell.
# Optional: EGG_AFTER_JOB=51417 bash cluster/launch_overnight.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run directly from an interactive Unicorn login prompt." >&2
    exit 127
fi
if ! command -v squeue >/dev/null 2>&1; then
    echo "ERROR: squeue is unavailable in this shell." >&2
    exit 127
fi

source "${SRC_DIR}/cluster/unicorn_env.sh"

STAMP="${EGG_OVERNIGHT_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ ! "${STAMP}" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "ERROR: invalid EGG_OVERNIGHT_STAMP: ${STAMP}" >&2
    exit 1
fi

DEPENDENCY_ARGS=()
DEPENDENCY_LABEL="none"
if [[ -n "${EGG_AFTER_JOB:-}" ]]; then
    if [[ ! "${EGG_AFTER_JOB}" =~ ^[0-9]+$ ]]; then
        echo "ERROR: EGG_AFTER_JOB must be a numeric Slurm job ID." >&2
        exit 1
    fi
    DEPENDENCY_ARGS=("--dependency=afterany:${EGG_AFTER_JOB}")
    DEPENDENCY_LABEL="afterany:${EGG_AFTER_JOB}"
fi

OUT_ROOT="runs/overnight/${STAMP}"
mkdir -p "${OUT_ROOT}"

DAMPING_JOB="$(sbatch --parsable --export="ALL,EGG_OVERNIGHT_STAMP=${STAMP}" \
    "${DEPENDENCY_ARGS[@]}" cluster/submit_overnight_damping.sub)"
BOUNDARY_JOB="$(sbatch --parsable --export="ALL,EGG_OVERNIGHT_STAMP=${STAMP}" \
    "${DEPENDENCY_ARGS[@]}" cluster/submit_overnight_boundary.sub)"

{
    printf 'stamp=%s\n' "${STAMP}"
    printf 'git_commit=%s\n' "$(git -C "${REPO_DIR}" rev-parse HEAD)"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'dependency=%s\n' "${DEPENDENCY_LABEL}"
    printf 'damping_job=%s\n' "${DAMPING_JOB}"
    printf 'damping_cells=288; seeds=0..15; n_trips=12; b=0.01,0.05; alpha=1,.75,.5,.35,.25,.2,.15,.1,.05; max_iters=240; concurrency=24\n'
    printf 'boundary_job=%s\n' "${BOUNDARY_JOB}"
    printf 'boundary_cells=64; seeds=0..7; n_trips=8,12; slots=8,12,16,20; delta=-1.5..1.5 step .01; concurrency=16\n'
} > "${OUT_ROOT}/MANIFEST.txt"

echo "Overnight stamp: ${STAMP}"
echo "Damping frontier: ${DAMPING_JOB}"
echo "Fine boundaries:  ${BOUNDARY_JOB}"
echo "Manifest: ${OUT_ROOT}/MANIFEST.txt"
squeue --jobs="${DAMPING_JOB},${BOUNDARY_JOB}"
