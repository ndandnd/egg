# Unicorn runbook and incident log

This is the operational memory for running `egg` on Unicorn. Read this file
before submitting an array. Cursor should treat it as the source of truth for
the recurring environment, Slurm, Git, and results-transfer failures.

## Current workflow

1. Merge the code PR into `main` before launching. On Unicorn, update the
   checkout and record the commit:

   ```bash
   cd "$HOME/egg"
   git switch main
   git pull --ff-only origin main
   git log -1 --oneline
   ```

2. From `src/`, source `cluster/unicorn_env.sh`. It activates the Python 3.12
   `~/evsp_env` environment, disables user-site contamination, selects the
   shared Gurobi license, and refuses a CBC fallback. Confirm:

   ```bash
   cd "$HOME/egg/src"
   source cluster/unicorn_env.sh
   python -c 'from egglab.solver import backend; print(backend())'
   ```

The expected output is `GRB`.

Before using the hardened 128-cell Phase 1 array, verify the cell count
directly from the checked-out code:

```bash
python experiments/run_phase1.py --list | tail -1
# expected: total: 128 cells
```

If an array was accidentally launched from the old 64-cell `main`, preserve
the mixed output and start clean after the hardened PR is merged:

```bash
ARCHIVE="runs/archive/pre-hardened-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${ARCHIVE}"
[[ -d runs/phase1 ]] && mv runs/phase1 "${ARCHIVE}/phase1"
[[ -d runs/phase2 ]] && mv runs/phase2 "${ARCHIVE}/phase2"
mkdir -p runs/phase1 runs/phase2
```

Moving rather than deleting keeps failed and pre-hardened records available
for diagnosis without allowing them to contaminate the corrected rerun.

3. Submit explicit arrays and save both parent job IDs. Phase 1 is `0-127`
   after the hardened rerun; Phase 2 is `0-31`.

4. `squeue` is only a live view. Once jobs disappear, use `sacct` as the
   authoritative result, then count `cell.ckpt.json` and `sweep.ckpt.json`.
   A disappeared job may have completed, failed, been cancelled, or been
   requeued.

5. Do not push from Unicorn. GitHub HTTPS authentication is not configured on
   the cluster. Pull raw runs to the Mac using one streamed SSH archive, then
   run `sync_results.sh` locally so the distilled CSV and `SUMMARY.md` can be
   committed and pushed.

## Definitive post-array check

Replace the two IDs before running:

```bash
P1_JOB=51078
P2_JOB=51079
cd "$HOME/egg/src"

echo '=== task states ==='
sacct -X -j "${P1_JOB},${P2_JOB}" \
  --format=JobID,JobName%24,State,ExitCode,Elapsed,NodeList

echo '=== non-completed tasks ==='
sacct -n -X -j "${P1_JOB},${P2_JOB}" \
  --format=JobID,State,ExitCode |
  awk '$2 != "COMPLETED"'

echo '=== checkpoints ==='
printf 'phase1: '
find runs/phase1 -name cell.ckpt.json | wc -l
printf 'phase2: '
find runs/phase2 -name sweep.ckpt.json | wc -l

echo '=== matching logs with errors ==='
for f in slurm-egg-phase1-${P1_JOB}_*.out \
         slurm-egg-phase2-${P2_JOB}_*.out; do
  [[ -e "${f}" ]] || continue
  grep -Ein 'error|traceback|exception|failed|killed|oom|requeue' "${f}" || true
done
```

## One-password results pull

Run this on the Mac, not on the login node. One `ssh` process streams both
experiment trees, so the SSH password is requested once:

```bash
LOCAL_SRC="/Users/nadan/Documents/projects/egg/src"
REMOTE="nc437@unicorn-login-01.coecis.cornell.edu"
mkdir -p "${LOCAL_SRC}/runs"

ssh "${REMOTE}" \
  'tar -C /home/nc437/egg/src/runs -czf - phase1 phase2' \
  | tar -C "${LOCAL_SRC}/runs" -xzf -
```

## Incident history and permanent fixes

| Symptom | Cause | Permanent rule/fix |
|---|---|---|
| `unicorn_env.sh: No such file` in a Slurm log | Slurm stages the script under `/var/spool/slurmd`; `BASH_SOURCE[0]` was not the checkout | Resolve the checkout from `SLURM_SUBMIT_DIR`; submit from the repo or `src/` |
| Base Python had no `gurobipy` | `~/evsp_env` was not activated | Always source `cluster/unicorn_env.sh` before testing or submitting |
| `SRE module mismatch` | Gurobi 3.11 Python libraries contaminated Python 3.12 via `PYTHONPATH` | `unset PYTHONPATH`; do not expose the personal Gurobi 11 Python tree |
| Gurobi license not found at `~/config/gurobi.lic` | That file does not exist on Unicorn | Use the shared `/share/apps/software/gurobi/gurobi.lic` through the helper |
| `egglab backend=CBC` despite Gurobi being installed | User-site `mip`/`cffi` packages or a license failure caused fallback | Set `PYTHONNOUSERSITE=1`; require `GRB` in cluster jobs |
| First pilot failed immediately | Helper path was resolved from the Slurm staging directory | Keep the `SLURM_SUBMIT_DIR` path-resolution logic |
| Two SSH password prompts during results pull | Phase 1 and Phase 2 used separate `scp` processes | Use one `ssh ... tar ... | tar ...` stream |
| `python: command not found` on the Mac | macOS exposes `python3`, not `python` | The collector must select `python` or `python3`; run local collection after pulling |
| Cluster sync could not push to GitHub | HTTPS password authentication is disabled and no token/SSH key is configured | Never push from Unicorn; push the distilled results from the Mac |
| `squeue` entries disappeared and status was unclear | `squeue` is not historical accounting | Use `sacct -X` and inspect exit codes/logs |
| Phase 1 tasks `0-63` completed but `64-127` failed | A 128-task array was submitted while `main` still defined only 64 cells | Merge the hardened PR first; run `python experiments/run_phase1.py --list` and require `total: 128` before submitting |
| `rg: command not found` on Unicorn | Ripgrep is not installed on the login/compute image | Use the portable `grep` loop above; do not add ad hoc packages to the cluster |

## Branch hygiene

Do not use the stale `codex/results-workflow` branch for new launches. The
hardened implementation belongs in the PR #7 branch until it is merged into
`main`; close stale workflow branches after their useful changes are either
merged or superseded.
