#!/bin/bash
# Guarded launcher for the legacy replay revalidation campaign.
#
# Usage (from an interactive Unicorn login prompt, in src/):
#   bash cluster/launch_revalidation.sh runs/phase1 [more runs dirs...]
#
# For each runs dir: counts failing records with the tool's --count, skips
# the dir when zero, sizes the Slurm array exactly, submits with bounded
# concurrency (revalidation runs fixed-sequence Gurobi solves), and writes a
# manifest under <runs_dir>/revalidation/. Never uses `sbatch --wrap` (its
# /bin/sh has no `source`); everything runs through committed bash scripts.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run directly from an interactive Unicorn login prompt." >&2
    exit 127
fi
source "${SRC_DIR}/cluster/unicorn_env.sh"

CONC="${EGG_REVAL_CONCURRENCY:-8}"
[[ $# -ge 1 ]] || { echo "usage: bash cluster/launch_revalidation.sh RUNS_DIR [RUNS_DIR...]" >&2; exit 2; }

for RUNS in "$@"; do
    if [[ ! -d "${RUNS}" ]]; then
        echo "ERROR: no such runs dir: ${RUNS}" >&2
        exit 1
    fi
    N="$(python experiments/revalidate_legacy_replay.py "${RUNS}" --count)"
    if [[ "${N}" -eq 0 ]]; then
        echo "[skip] ${RUNS}: no stored replay failures"
        continue
    fi
    JOB="$(sbatch --parsable \
        --export="ALL,EGG_REVAL_RUNS=${RUNS}" \
        --array="0-$((N - 1))%${CONC}" \
        cluster/submit_revalidate.sub)"
    mkdir -p "${RUNS}/revalidation"
    MANIFEST="${RUNS}/revalidation/MANIFEST-$(date -u +%Y%m%dT%H%M%SZ).txt"
    {
        printf 'runs_dir=%s\n' "${RUNS}"
        printf 'failing_records=%s\n' "${N}"
        printf 'array=0-%s%%%s\n' "$((N - 1))" "${CONC}"
        printf 'job_id=%s\n' "${JOB}"
        printf 'git_commit=%s\n' "$(git -C "${REPO_DIR}" rev-parse HEAD)"
        printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "${MANIFEST}"
    echo "[submitted] ${RUNS}: ${N} cells as job ${JOB} (manifest: ${MANIFEST})"
done
