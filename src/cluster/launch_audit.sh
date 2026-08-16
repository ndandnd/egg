#!/bin/bash
# Guarded launcher for the audit job.
#
# Usage (from an interactive Unicorn login prompt, in src/). Each argument is
# a root SPEC carrying its expected-count gates:
#
#   bash cluster/launch_audit.sh \
#       runs/phase1:cells=128:loops=128:static=4 \
#       runs/overnight/<stamp>/damping_frontier:cells=288:loops=288 \
#       runs/overnight/<stamp>/boundary_fine:sweeps=64
#
# Gates: cells=N (complete cell.ckpt.json with loop_done), loops=N (done
# loop.ckpt.json), sweeps=N (done+margins_done sweep.ckpt.json), static=N
# (completed static regimes per cell), cg=N (done, bound-sane *.cg.ckpt.json
# for B2-A2, e.g. runs/b2a2_pilot:cg=12). An entirely missing checkpoint then
# fails the audit — completeness of found files alone is not enough.
#
# Verifies each root exists, submits ONE bash batch job (never
# `sbatch --wrap`, whose /bin/sh has no `source`), and writes a manifest.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run directly from an interactive Unicorn login prompt." >&2
    exit 127
fi
source "${SRC_DIR}/cluster/unicorn_env.sh"

[[ $# -ge 1 ]] || { echo "usage: bash cluster/launch_audit.sh 'ROOT[:cells=N][:loops=N][:sweeps=N][:static=N][:cg=N]' ..." >&2; exit 2; }
for SPEC in "$@"; do
    ROOT="${SPEC%%:*}"
    [[ -d "${ROOT}" ]] || { echo "ERROR: no such runs root: ${ROOT} (from spec '${SPEC}')" >&2; exit 1; }
done

JOB="$(sbatch --parsable --export="ALL,EGG_AUDIT_ROOTS=$*" cluster/submit_audit.sub)"
mkdir -p runs/audit-manifests
MANIFEST="runs/audit-manifests/MANIFEST-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
    printf 'roots=%s\n' "$*"
    printf 'job_id=%s\n' "${JOB}"
    printf 'git_commit=%s\n' "$(git -C "${REPO_DIR}" rev-parse HEAD)"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${MANIFEST}"
echo "[submitted] audit job ${JOB} over: $* (manifest: ${MANIFEST})"
