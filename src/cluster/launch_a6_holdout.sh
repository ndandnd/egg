#!/bin/bash
# Guarded launcher for the frozen A6 holdout (EXACTLY 128 method-cells).
#
# Before sbatch, the driver constructs and independently replays a zero-charge
# feasible cover for ALL 32 physical instances and atomically records those
# witnesses plus all 64 market hashes in runs/a6_holdout/PREFLIGHT.json.  Any
# infeasible instance or provenance/grid failure exits before submission, so
# neither method sees holdout outcomes unless the whole population passes.
#
# The scientific completion audit is deliberately NOT a 64/64 certification
# gate: valid budget exhaustion scores 241.  After completion use:
#   python experiments/audit_runs.py runs/a6_holdout --expect-cg 128 \
#     --expect-cg-method a2=64 --expect-cg-method a6_a4=64
#
# Usage (interactive Unicorn login prompt, from src/):
#   bash cluster/launch_a6_holdout.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${SRC_DIR}/.." && pwd)"
cd "${SRC_DIR}"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch is unavailable; run from an interactive Unicorn login prompt." >&2
    exit 127
fi

if [[ -n "$(git -C "${REPO_DIR}" status --porcelain --untracked-files=no)" ]]; then
    echo "ERROR: tracked tree is dirty; refusing holdout preflight/submission." >&2
    exit 1
fi
BRANCH="$(git -C "${REPO_DIR}" symbolic-ref --quiet --short HEAD || true)"
if [[ "${BRANCH}" != "main" ]]; then
    echo "ERROR: holdout launch requires branch main; found ${BRANCH:-detached HEAD}." >&2
    exit 1
fi

CODE_COMMIT="$(git -C "${REPO_DIR}" rev-parse HEAD)"
if ! ORIGIN_MAIN="$(git -C "${REPO_DIR}" rev-parse refs/remotes/origin/main 2>/dev/null)"; then
    echo "ERROR: local origin/main ref is unavailable; run git pull --ff-only origin main before launch." >&2
    exit 1
fi
if [[ "${CODE_COMMIT}" != "${ORIGIN_MAIN}" ]]; then
    echo "ERROR: local main HEAD ${CODE_COMMIT} != local origin/main ${ORIGIN_MAIN}; run git pull --ff-only origin main (or publish/merge the experiment code) before launch." >&2
    exit 1
fi
SELECTION_GATE_COMMIT="8f59a905bd5e12ac5784e57aebc66a03b47a00cb"
SELECTION_REL="result/a6_pilot/20260819T005514Z/SELECTION.json"
EXPECTED_SELECTION_SHA="026ddc38e90f9dd2e9342a50cfb5550bc52731c5f1ee67d87d53008bd6b4b507"

if ! git -C "${REPO_DIR}" merge-base --is-ancestor \
    "${SELECTION_GATE_COMMIT}" "${CODE_COMMIT}"; then
    echo "ERROR: committed selection gate ${SELECTION_GATE_COMMIT} is not an ancestor of ${CODE_COMMIT}." >&2
    exit 1
fi
git -C "${REPO_DIR}" ls-files --error-unmatch "${SELECTION_REL}" >/dev/null
SELECTION_SHA="$(
    python -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' \
        "${REPO_DIR}/${SELECTION_REL}"
)"
if [[ "${SELECTION_SHA}" != "${EXPECTED_SELECTION_SHA}" ]]; then
    echo "ERROR: selection SHA is ${SELECTION_SHA}; expected ${EXPECTED_SELECTION_SHA}." >&2
    exit 1
fi

source "${SRC_DIR}/cluster/unicorn_env.sh"
export EGGLAB_HOLDOUT_CODE_COMMIT="${CODE_COMMIT}"

# One-shot submission gate, acquired BEFORE the physical preflight. Atomic
# mkdir prevents concurrent launchers from reaching preflight or sbatch
# against the same checkpoint paths. The sentinel persists on every later
# failure: recovery or resubmission requires explicit audit and review.
mkdir -p runs/a6_holdout
PREEXISTING_CKPT="$(
    find runs/a6_holdout -type f -name '*.ckpt.json' -print -quit
)"
if [[ -n "${PREEXISTING_CKPT}" ]]; then
    echo "ERROR: preexisting holdout checkpoint ${PREEXISTING_CKPT}; refusing first submission. Recovery requires audit/review." >&2
    exit 1
fi
LOCK_DIR="runs/a6_holdout/SUBMISSION_LOCK"
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    echo "ERROR: holdout submission sentinel ${LOCK_DIR} already exists; refusing duplicate/concurrent submission. Never delete it without audit/review." >&2
    exit 1
fi
CLAIM_TMP="${LOCK_DIR}/CLAIM.txt.tmp.$$"
{
    printf 'status=claimed-before-preflight\n'
    printf 'git_commit=%s\n' "${CODE_COMMIT}"
    printf 'selection_sha256=%s\n' "${SELECTION_SHA}"
    printf 'claimed_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${CLAIM_TMP}"
mv "${CLAIM_TMP}" "${LOCK_DIR}/CLAIM.txt"

# Whole-population physical gate.  This writes only deterministic feasibility
# witnesses/hashes; no A2 or A6 method cell is run here.
python experiments/run_a6_holdout.py \
    --preflight --out runs/a6_holdout

LIST="$(python experiments/run_a6_holdout.py --list)"
GRID_LIST_SHA="$(
    printf '%s\n' "${LIST}" |
        python -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())'
)"
N="$(printf '%s\n' "${LIST}" | tail -1 | sed 's/total: \([0-9]*\) cells/\1/')"
if [[ "${N}" != "128" ]]; then
    echo "ERROR: holdout --list reports ${N} cells; expected exactly 128." >&2
    exit 1
fi
for METHOD in a2 a6_a4; do
    METHOD_N="$(printf '%s\n' "${LIST}" |
        grep -c "'method': '${METHOD}'" || true)"
    if [[ "${METHOD_N}" != "64" ]]; then
        echo "ERROR: --list contains ${METHOD_N} ${METHOD} cells; expected 64." >&2
        exit 1
    fi
done
if printf '%s\n' "${LIST}" | grep -q "'method': 'a6_a3'"; then
    echo "ERROR: forbidden a6_a3 arm appears in holdout --list." >&2
    exit 1
fi

SEED_SET="$(printf '%s\n' "${LIST}" |
    sed -n "s/.*'seed': \([0-9][0-9]*\),.*/\1/p" |
    sort -nu | paste -sd, -)"
EXPECTED_SEEDS="16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"
if [[ "${SEED_SET}" != "${EXPECTED_SEEDS}" ]]; then
    echo "ERROR: --list seed set is ${SEED_SET}; expected ${EXPECTED_SEEDS}." >&2
    exit 1
fi
N_SET="$(printf '%s\n' "${LIST}" |
    sed -n "s/.*'n_trips': \([0-9][0-9]*\),.*/\1/p" |
    sort -nu | paste -sd, -)"
if [[ "${N_SET}" != "8,12" ]]; then
    echo "ERROR: --list n_trips set is ${N_SET}; expected 8,12." >&2
    exit 1
fi
B_SET="$(printf '%s\n' "${LIST}" |
    sed -n "s/.*'b': \([0-9.][0-9.]*\),.*/\1/p" |
    sort -nu | paste -sd, -)"
if [[ "${B_SET}" != "0.01,0.05" ]]; then
    echo "ERROR: --list b set is ${B_SET}; expected 0.01,0.05." >&2
    exit 1
fi
if ! printf '%s\n' "${LIST}" |
    grep -q "'selected_arm': 'a6_a4'"; then
    echo "ERROR: --list did not verify committed a6_a4 selection." >&2
    exit 1
fi

PREFLIGHT="runs/a6_holdout/PREFLIGHT.json"
if [[ ! -s "${PREFLIGHT}" ]]; then
    echo "ERROR: whole-population PREFLIGHT.json is missing or empty." >&2
    exit 1
fi
PREFLIGHT_SHA="$(
    python -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' \
        "${PREFLIGHT}"
)"

INTENT_TMP="${LOCK_DIR}/INTENT.txt.tmp.$$"
{
    printf 'status=prepared\n'
    printf 'git_commit=%s\n' "${CODE_COMMIT}"
    printf 'grid_list_sha256=%s\n' "${GRID_LIST_SHA}"
    printf 'selection_sha256=%s\n' "${SELECTION_SHA}"
    printf 'preflight_sha256=%s\n' "${PREFLIGHT_SHA}"
    printf 'prepared_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${INTENT_TMP}"
mv "${INTENT_TMP}" "${LOCK_DIR}/INTENT.txt"

CONC=12
JOB="$(sbatch --parsable \
    --export="ALL,EGGLAB_HOLDOUT_CODE_COMMIT=${CODE_COMMIT}" \
    --array="0-$((N - 1))%${CONC}" \
    cluster/submit_a6_holdout.sub)"
SUBMITTED_TMP="${LOCK_DIR}/SUBMITTED.txt.tmp.$$"
{
    printf 'status=submitted\n'
    printf 'job_id=%s\n' "${JOB}"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${SUBMITTED_TMP}"
mv "${SUBMITTED_TMP}" "${LOCK_DIR}/SUBMITTED.txt"

MANIFEST="runs/a6_holdout/MANIFEST-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
    printf 'campaign=a6-holdout (spec doc/A6_SPARSE_STABILIZATION_SPEC.md Section 6)\n'
    printf 'cells=%s (verified: 64 a2 + 64 a6_a4; a6_a3 forbidden)\n' "${N}"
    printf 'grid=seeds 16-31 x n{8,12} x b{0.01,0.05}; 64 matched instances\n'
    printf 'grid_list_sha256=%s\n' "${GRID_LIST_SHA}"
    printf 'array=0-%s%%%s\n' "$((N - 1))" "${CONC}"
    printf 'epsilon=1e-2; budget=240 exact oracle calls; budget exhaustion is valid and scores 241\n'
    printf 'audit=--expect-cg 128 --expect-cg-method a2=64 --expect-cg-method a6_a4=64 (NO certification-count gate)\n'
    printf 'selection_path=%s\n' "${SELECTION_REL}"
    printf 'selection_sha256=%s\n' "${SELECTION_SHA}"
    printf 'selection_gate_commit=%s (verified ancestor)\n' "${SELECTION_GATE_COMMIT}"
    printf 'preflight_path=%s\n' "${PREFLIGHT}"
    printf 'preflight_sha256=%s\n' "${PREFLIGHT_SHA}"
    printf 'submission_sentinel=%s (persistent; deletion requires audit/review)\n' "${LOCK_DIR}"
    printf 'feasibility=32/32 physical instances have exact zero-charge covers; 64 market hashes recorded before sbatch\n'
    printf 'job_id=%s\n' "${JOB}"
    printf 'git_commit=%s\n' "${CODE_COMMIT}"
    printf 'submitted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${MANIFEST}"

echo "[submitted] A6 holdout: ${N} cells as job ${JOB} (manifest: ${MANIFEST})"
squeue --jobs="${JOB}"
