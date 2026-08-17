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

3. From the current interactive Unicorn login prompt, submit both arrays with
   `bash cluster/launch_phase12.sh`. Do not SSH from Unicorn back into itself:
   a nested non-interactive SSH shell may omit the Slurm client path, producing
   `sbatch: command not found` even though Gurobi initialization succeeds. The
   launcher refuses to proceed unless `sbatch`, `squeue`, Gurobi, and the
   hardened 128-cell grid are all available.

4. `squeue` is only a live view. Once jobs disappear, use `sacct` as the
   authoritative result, then count `cell.ckpt.json` and `sweep.ckpt.json`.
   A disappeared job may have completed, failed, been cancelled, or been
   requeued.

5. Do not push from Unicorn. GitHub HTTPS authentication is not configured on
   the cluster. Pull raw runs to the Mac using one streamed SSH archive, then
   run `sync_results.sh` locally so the distilled CSV and `SUMMARY.md` can be
   committed and pushed.

For targeted overnight work, use `cluster/launch_overnight.sh`. Set
`EGG_AFTER_JOB=<jobid>` to queue the suite behind a running array. The launcher
writes a stamped manifest and caps concurrent tasks; the scientific design is
recorded in `doc/OVERNIGHT_EXPERIMENTS.md`.

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
| `sbatch: command not found` after the Gurobi preflight passed | Submission was run through a nested non-interactive SSH session from Unicorn back into itself; that shell lacked the Slurm client path | Submit directly from the current Unicorn login prompt with `bash cluster/launch_phase12.sh`; the launcher checks `sbatch` before doing any work |
| Replay validation failed cells with `terminal SOC 6.00 < 6.0` (phase-1 job 51417: 24 failures; boundary job 51831: 23 failures); occasional SOC-floor/battery-overfill variants | Extracted charges/loads were rounded to 6 decimals before the independent replay while replay used a 1e-6 kWh tolerance; rounding plus solver primal-feasibility residuals accumulated along vehicle chains until tight constraints appeared violated | Full-precision extraction in the EVSP extractor, `solve_fixed_sequences`, and `solve_uncontrolled` (rounding only in hashes/presentation); one documented audit tolerance `REPLAY_TOL_KWH = 1e-4` kWh in `egglab/evsp.py` (audit-only — MILP constraints unchanged); diagnostic messages now print actual value, required bound, shortfall/excess, and active tolerance; regression tests in `tests/test_replay_tolerance.py` |
| 18 (phase 1) + 163 (damping frontier) loop records with `replay_ok=false` survived in otherwise complete runs | `egglab/loops.py` appended every loop record and advanced the checkpoint WITHOUT checking `rec["replay_ok"]`, so replay-invalid iterations were never failed work units and were never replaced by retries | Fail-fast ordering in `loops.py`: replay is checked BEFORE `append_jsonl` and BEFORE any checkpoint mutation; a failed iteration raises and leaves `state["iter"]` untouched (regression-tested). Legacy records are handled by the sidecar revalidation campaign below — raw JSONL is append-only evidence and is never edited, deleted, or waived by commit age |
| `source: not found` in the audit Slurm log | The audit was submitted with `sbatch --wrap`, which runs under `/bin/sh`; `source` is a bash builtin. The job continued only because the environment happened to be inherited | Never use `sbatch --wrap`. Use the committed `#!/bin/bash` scripts: `cluster/submit_audit.sub` via `cluster/launch_audit.sh`, and `cluster/submit_revalidate.sub` via `cluster/launch_revalidation.sh` |

## Replay tolerance policy (2026-08-15)

The independent replay audit (`egglab/evsp.py:validate_solution`) accepts
absolute energy deviations up to `REPLAY_TOL_KWH = 1e-4` kWh (0.1 Wh). This
exists solely to absorb MILP solver primal-feasibility residuals (~1e-6 per
constraint, accumulated along a vehicle chain) and floating-point replay
arithmetic. It must never be raised to hide model bugs, and it does not relax
any MILP constraint. Time-feasibility checks remain integer-minute exact with
zero tolerance. Solution values (charges, loads, energy totals) are stored at
full float precision; rounding is reserved for hashes and presentation only.
Cells that failed replay under the old rounding (jobs 51417/51831) can simply
be rerun with the same commands — checkpoints of completed units remain
valid; the failed units were never marked done.

## Legacy replay revalidation (2026-08-16)

Policy (full rationale: `MEASUREMENT_CLOSEOUT.md`): raw run records are
append-only evidence. Records stored with `replay_ok=false` are never edited,
deleted, or auto-waived because their commit predates the replay fix. Each is
individually revalidated — the exact stored trip partition is re-realized at
the recorded prices under the current full-precision oracle, replayed with
the current validator, and compared against the legacy economics — and the
verdict is written to an atomic sidecar (`<runs>/revalidation/<sha256>.json`)
keyed by the SHA-256 of the complete original record line. Audits and the
collector report both the raw counts (never hidden) and the effective status
after exact-hash sidecar matching.

Exact commands for the current campaign (interactive Unicorn login, `src/`):

```bash
cd "$HOME/egg/src"
source cluster/unicorn_env.sh

# 1. Revalidate both roots that contain legacy failures:
bash cluster/launch_revalidation.sh \
    runs/phase1 \
    runs/overnight/20260815T033012Z/damping_frontier

# 2. After the arrays complete (sacct, then checkpoints), run the
#    three-root audit as a proper bash batch job, WITH expected-count
#    gates so an entirely absent checkpoint fails the audit:
bash cluster/launch_audit.sh \
    runs/phase1:cells=128:loops=128:static=4 \
    runs/overnight/20260815T033012Z/damping_frontier:cells=288:loops=288 \
    runs/overnight/20260815T033012Z/boundary_fine:sweeps=64
```

The audit exits zero only when every EXPECTED checkpoint exists and is
complete (cells: loop_done + required static regimes; loops: done; sweeps:
done + margins_done), every stored replay failure is covered by a
`certified_equivalent` exact-hash revalidation (alternative realizations are
diagnostic only — the per-slot load vector determines the next endogenous
price state, so economic equivalence is not trajectory equivalence), no
revalidation is nonaccepted, and every record status is exactly OPTIMAL
(missing statuses fail). `SUMMARY.md` in each root always shows the raw
counts and the expected/found/complete/missing table, e.g.:

```
- raw legacy replay failures: 163
- successfully revalidated: 163
- unresolved replay failures: 0
```

## B2-A2 12-cell pilot (2026-08-16)

Certified plain column generation (method A2 of `MEASUREMENT_RESULTS.md`
Section 8): `egglab/b2a2.py` + `experiments/run_b2a2_pilot.py`. Grid: seeds
{0, 11, 15} x n_trips {8, 12} x b {0.01, 0.05}; epsilon 1e-2; budget 240
exact pricing calls per cell. Launch gates (all three required BEFORE any
full-grid work): (i) tiny complete-enumeration tests pass locally
(`python3 -m pytest tests/test_b2a2.py -q`), (ii) all 12 pilot cells satisfy
bound sanity, (iii) pilot records/checkpoints pass replay and completeness
audits.

Exact commands (interactive Unicorn login prompt):

```bash
cd "$HOME/egg"
git switch main && git pull --ff-only origin main && git log -1 --oneline
cd src
source cluster/unicorn_env.sh

# 0. Verify the grid before submitting (the launcher refuses anything != 12):
python experiments/run_b2a2_pilot.py --list | tail -1
# expected: total: 12 cells

# 1. Submit (derives the array from --list; %12 concurrency; --requeue;
#    email nc437@cornell.edu on END/FAIL/REQUEUE; manifest under
#    runs/b2a2_pilot/):
bash cluster/launch_b2a2_pilot.sh

# 2. Monitor:
squeue --me
sacct -j <JOBID> --format=JobID,State,Elapsed,ExitCode
tail -f slurm-egg-b2a2-pilot-<JOBID>_<TASK>.out

# 3. Inspect one cell's certificate:
python -c "import json; s=json.load(open('runs/b2a2_pilot/s0_n8_b0.01/a2.cg.ckpt.json')); print(json.dumps(s['outcome'], indent=2))"

# 4. Audit gate (cells=12), as a proper bash batch job:
bash cluster/launch_audit.sh runs/b2a2_pilot:cg=12
# or directly at the prompt:
python experiments/audit_runs.py runs/b2a2_pilot --expect-cg 12
```

Per-cell evidence written under `runs/b2a2_pilot/<cell>/`:
`a2.cg.ckpt.json` (the atomic per-oracle-call checkpoint and SINGLE source
of truth: identity block, columns with replay evidence, LB/UB trajectories,
committed oracle and iteration events with stable call/solve ids, outcome,
uplift interval), `a2.oracle.jsonl` and `a2.iterations.jsonl` (materialized
atomically FROM the checkpoint, so one completed oracle call appears exactly
once after arbitrary restart; iterations carry both the incumbent and the
certified-bound reduced costs, the pricing gap, and every actual clean-RMP
tangent-refinement solve individually), and
`dictator.jsonl`/`dictator.ckpt.json` (the independent dictator solve —
gated on OPTIMAL status, a finite certified bound, and adaptive
convergence — feeding the uplift interval; the complete record and every
per-round adaptive subsolve's stats are committed inside the checkpoint and
`dictator.jsonl` is materialized atomically from it, so restarts never
duplicate it). Budget-exhausted cells additionally commit the terminal
clean-RMP's solve evidence as a master-only iteration event. LB_CH is
always built from the
pricing solver's certified dual bound, never the incumbent. A preempted task
repeats at most the one in-flight oracle solve; completed columns and bounds
survive requeue; a corrupted checkpoint (LB above best UB) or any identity
mismatch (instance, market a/b/U, epsilon, budget, tolerances, solver
settings, dictator provenance) fails loudly at resume. Solves honor
`SLURM_CPUS_PER_TASK` for solver threads and record the applied count.

## B2 A3-A5 36-cell stabilization pilot (2026-08-17)

Stabilized column generation per `B2_STABILIZATION_SPEC.md` (normative math:
du Merle 5-piece box/penalty, Wentges smoothing with automatic alpha,
proximal bundle with t halved on null steps). Certification is UNCHANGED
from A2: `UB_CH` from the clean RMP over all columns, `LB_CH` only from
clean-dual certification pricing; stabilization only chooses candidate
columns. Both call kinds draw the same 240-call budget and are logged
separately. Launch gates: the A2 pilot is closed (job 80309, 12/12
certified; audit job 81432 PASS) and the A3-A5 battery passes locally
(`python3 -m pytest tests/test_b2a345.py -q`).

Exact commands (interactive Unicorn login prompt):

```bash
cd "$HOME/egg"
git switch main && git pull --ff-only origin main && git log -1 --oneline
cd src
source cluster/unicorn_env.sh

# 0. Verify the grid before submitting (the launcher refuses anything != 36):
python experiments/run_b2a345_pilot.py --list | tail -1
# expected: total: 36 cells

# 1. Submit (array derived from --list; %12 concurrency; --requeue; email
#    nc437@cornell.edu on END/FAIL/REQUEUE; manifest under runs/b2a345_pilot/):
bash cluster/launch_b2a345_pilot.sh

# 2. Monitor:
squeue --me
sacct -j <JOBID> --format=JobID,State,Elapsed,ExitCode
tail -f slurm-egg-b2a345-pilot-<JOBID>_<TASK>.out

# 3. Inspect one cell's certificate and stabilization dynamics:
python -c "import json; s=json.load(open('runs/b2a345_pilot/a3_s0_n8_b0.01/a3.cg.ckpt.json')); print(json.dumps(s['outcome'], indent=2)); print('serious:', s['stab']['serious_steps'], 'null:', s['stab']['null_steps'])"

# 4. Audit gates: 36 complete-and-sane cells, 12 per method, AND 12
#    CERTIFIED per method (budget-exhausted cells are valid and sane but
#    do NOT satisfy the pilot's certification gate):
bash cluster/launch_audit.sh \
    runs/b2a345_pilot:cg=36:cg_a3=12:cg_a4=12:cg_a5=12:cgcert_a3=12:cgcert_a4=12:cgcert_a5=12
# or directly at the prompt:
python experiments/audit_runs.py runs/b2a345_pilot --expect-cg 36 \
    --expect-cg-method a3=12 --expect-cg-method a4=12 --expect-cg-method a5=12 \
    --expect-cg-certified-method a3=12 --expect-cg-certified-method a4=12 \
    --expect-cg-certified-method a5=12
```

Per-cell evidence under `runs/b2a345_pilot/<cell>/` follows the A2 pilot
layout (`<method>.cg.ckpt.json` as source of truth; oracle/iteration JSONL
materialized from it) plus: candidate-call events (`phase=stabilized`) with
Theta_cert, serious/null decisions, exact parameter values before/after,
stabilized master solve evidence (A3/A5; marked `stabilized: true`, never
counted as clean solves; A4 solves no master), broadcast-price trajectory
metrics (L-infinity max step, total variation), and the clean/stabilized
oracle-call split in the outcome. The 576 fresh A1 cells and the 960-cell
full grid are NOT part of this stage; they follow only after this pilot
passes its audit.

**Outcome (2026-08-17)**: jobs **91001** and **91002** completed the
36-cell stabilization pilot with **36/36 certified**, all solves OPTIMAL
and replay-valid, and no budget exhaustion; the audit (cg=36 with
per-method sanity and certification gates) passed. Per-cell runtimes and
oracle-call counts are extracted from the checkpoints — never from Slurm
console text — by `experiments/analyze_b2_pilot.py` into
`result/b2_pilot/<stamp>/cells.csv` (solver wall time separated from the
per-cell dictator stage, which every method-cell repeats by design).
Scientific medians (A2 21.5 / A4 29 / A3 33 / A5 33 oracle calls) put the
stabilization kill signal ACTIVE — see `doc/DECISION_LOG.md` 2026-08-17:
the 960-cell campaign is PAUSED; do not submit it.

## B2 pilot closeout transfer and analysis (2026-08-17)

One-password transfer of both pilot run roots to the analysis machine:

```bash
ssh nc437@unicorn-login-01.coecis.cornell.edu \
  'cd "$HOME/egg/src" && tar -czf - runs/b2a2_pilot runs/b2a345_pilot' |
tar -xzf - -C "$LOCAL_REPO/src"
```

Then, where the raw runs live (they are gitignored and never committed):

```bash
cd "$LOCAL_REPO/src"
python3 experiments/analyze_b2_pilot.py \
    --a2-root runs/b2a2_pilot --a345-root runs/b2a345_pilot \
    --analysis-code-commit <commit-1-hash>
git add ../result/b2_pilot/<stamp>
git commit  # commit 2 of the two-commit provenance protocol
```

## B2 208-cell matched expansion (2026-08-17, Option B)

Population robustness for the stabilization kill decision
(`DECISION_LOG.md`): the remaining 52 moderate/strong instances (seeds
0-15 minus the pilot's {0, 11, 15}; n {8, 12}; b {0.01, 0.05}) x methods
A2-A5 = exactly 208 method-cells, settings identical to the pilots
(epsilon 1e-2, budget 240, duck market, per-cell dictator stage).
Explicitly NOT a scale test. Certification is an OUTCOME here, not an
audit gate: acc-1 tests >= 95% certification on the full population, so a
budget-exhausted cell is valid completed science — the audit gates
completeness only.

Exact commands (interactive Unicorn login prompt):

```bash
cd "$HOME/egg"
git switch main && git pull --ff-only origin main && git log -1 --oneline
cd src
source cluster/unicorn_env.sh

# 0. Verify the grid (the launcher refuses anything != 208 and refuses
#    any pilot seed leaking in):
python experiments/run_b2_expansion.py --list | tail -1
# expected: total: 208 cells

# 1. Submit (array 0-207%12 derived from --list; --requeue; mail
#    nc437@cornell.edu on END/FAIL/REQUEUE; manifest under runs/b2_expansion/):
bash cluster/launch_b2_expansion.sh

# 2. Monitor:
squeue --me
sacct -j <JOBID> --format=JobID,State,Elapsed,ExitCode | tail -20

# 3. Audit (completeness + per-method counts; NO certification gates —
#    certification rates are the measurement):
bash cluster/launch_audit.sh \
    runs/b2_expansion:cg=208:cg_a2=52:cg_a3=52:cg_a4=52:cg_a5=52
# or directly:
python experiments/audit_runs.py runs/b2_expansion --expect-cg 208 \
    --expect-cg-method a2=52 --expect-cg-method a3=52 \
    --expect-cg-method a4=52 --expect-cg-method a5=52

# 4. Transfer (one password, same pattern as the pilots):
#    ssh nc437@unicorn-login-01.coecis.cornell.edu \
#      'cd "$HOME/egg/src" && tar -czf - runs/b2_expansion' |
#    tar -xzf - -C "$LOCAL_REPO/src"
```

The full-population analysis (64 instances x 4 methods = 256 method-cells,
joining `runs/b2_expansion` with the pilot roots) is a separate
prespecified analysis PR after the data lands; the acceptance/kill
criteria then get their true denominators (64 instances/method for the 2x
criterion; 96 b=0.05 method-cells for acc-1).

## Branch hygiene

The hardened implementation and this runbook are merged into `main`. Submit
only from `main`; delete source branches after their PR is fast-forwarded.
