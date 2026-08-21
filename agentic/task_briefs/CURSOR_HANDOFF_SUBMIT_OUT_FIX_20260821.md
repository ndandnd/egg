# Cursor handoff: thread the run directory through the B3 pilot submit script

Date: 2026-08-21 (America/New_York)

Before doing anything:

```bash
git remote get-url origin | grep -q "ndandnd/egg"
git config --local user.name "Nathan Cho"
git config --local user.email "63525258+ndandnd@users.noreply.github.com"
git push --dry-run origin HEAD
```

(`gh api user` returns 403 for Cursor's GitHub App token by design; that is not
an authorization failure, and commit authorship comes from `git config`.)

No cluster commands. No launching. Never read, list, or hash anything under
`runs/b3_factor_pilot`. Keep the PR draft.

## The defect

`src/cluster/launch_b3_factor_pilot.sh` resolves its run directory as

```bash
OUT="${EGG_RUN_OUT:-runs/b3_factor_pilot}"
```

and uses `$OUT` for the fresh-directory guard, the atomic run-manifest
emission, and `--bind-job`. But the array it submits,
`src/cluster/submit_b3_factor_pilot.sub`, ends with a hardcoded path:

```bash
python experiments/run_b3_factor_pilot.py --cell "${SLURM_ARRAY_TASK_ID}" \
    --out runs/b3_factor_pilot
```

So `EGG_RUN_OUT=runs/b3_factor_pilot_replication bash cluster/launch_b3_factor_pilot.sh`
passes every guard — the new directory is fresh, its manifest is written, the
job binds and releases — and then all 60 array tasks write into the **original**
tree. That tree is the audited flagship evidence and is bound to a
pre-analysis anchor
(`tree_sha256 efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4`,
363 files, 60 directories, 17385781 bytes). Overwriting it would destroy the
only clean provenance the flagship decision has.

The collision may also be quiet rather than loud: the per-cell driver resumes
from matching checkpoint identities, so completed cells could no-op or rewrite
byte-identical logs. Do not rely on that.

## Required change

Branch from current `origin/main` as `cursor/b3-submit-out-fix`. One draft PR.
Change only these three files.

### 1. `src/cluster/submit_b3_factor_pilot.sub`

- Replace the hardcoded `--out runs/b3_factor_pilot` with
  `--out "${EGG_RUN_OUT:-runs/b3_factor_pilot}"`. Keep the path **relative**:
  the script already `cd`s to the `src` working directory, so a relative path
  resolves correctly in both the launcher and the array task.
- Refuse rather than silently defaulting when the variable is set but empty:
  if `EGG_RUN_OUT` is defined and empty, print an error and exit nonzero.
- Make the script testable off-cluster, following the override pattern the
  launcher already uses (`EGG_SBATCH`, `EGG_PILOT`, ...): take the interpreter
  from `EGG_PYTHON` (default `python`) and the environment script from
  `EGG_ENV_SCRIPT` (default `${WORK_DIR}/cluster/unicorn_env.sh`). Do not
  change what those defaults do in production, and keep
  `export EGGLAB_REQUIRE_GRB=1` unconditional.

### 2. `src/cluster/launch_b3_factor_pilot.sh`

- Propagate the resolved directory **explicitly** on the sbatch line rather
  than relying on the site's default export policy, which may be
  `--export=NONE`:

  ```bash
  JOB="$(${SBATCH} --hold --parsable \
      --export="ALL,EGG_RUN_OUT=${OUT}" \
      --array="0-$((N - 1))%${CONC}" cluster/submit_b3_factor_pilot.sub)"
  ```

- Change nothing else. Every existing guard must remain byte-equivalent in
  behavior: the `sbatch` absence check, the hard Gurobi/GRB check, the
  dirty-tree refusal, the fresh-directory rules (including the lone reusable
  `MANIFEST.json`), the `--dry-run` preflight, the exactly-60-cells check, the
  held submit, the bind-failure cancel-and-never-release path, the
  release-failure cancel path, and the `%12` concurrency cap.
- The `.sub` already carries `#SBATCH --requeue`; a requeued task keeps its
  submission environment, so the override survives a requeue. Confirm that in
  the PR description rather than changing requeue behavior.

### 3. `src/tests/test_b3_launcher.py`

This file already has the stub harness you need: `_stubs()` builds fake
`sbatch`/`scancel`/`scontrol`/`squeue`/`sacct`/pilot executables that append
their arguments to an events file, and it already sets `EGG_RUN_OUT` to a
temporary directory. Extend it:

- **Export propagation:** assert the recorded `sbatch` tokens contain
  `--export=ALL,EGG_RUN_OUT=<the temporary out dir>`. This must fail against
  the current launcher.
- **The array actually targets the override** — the important test. Execute
  `submit_b3_factor_pilot.sub` directly with `EGG_RUN_OUT` set to a temporary
  path, `EGG_PYTHON` pointing at a stub that appends its argv to an events
  file, and `EGG_ENV_SCRIPT` pointing at a no-op stub; set
  `SLURM_SUBMIT_DIR` to the repository `src` directory and
  `SLURM_ARRAY_TASK_ID` to something like `7`. Assert the recorded argv is
  exactly `experiments/run_b3_factor_pilot.py --cell 7 --out <override>`.
  Assert on the recorded tokens, never on the file's source text.
- **Default preserved:** with `EGG_RUN_OUT` unset, the same execution records
  `--out runs/b3_factor_pilot`.
- **Empty refused:** with `EGG_RUN_OUT=""`, the `.sub` exits nonzero and
  records no python invocation.
- Confirm the existing launcher tests still pass unmodified — do not weaken or
  rewrite them.

## Verification

Run from `src/`:

```bash
python3 -m pytest tests/test_b3_launcher.py -q
python3 -m pytest tests/ -q
git diff --check
```

Merge current `origin/main` into the branch so CI reports on the PR, and quote
CI-measured counts rather than local ones.

## Report

Branch, draft PR URL, the exact three-file diff, CI-measured test counts, the
recorded argv from the new array-targeting test, and confirmation that no
launcher guard changed behavior, no cluster command ran, and no path under
`runs/b3_factor_pilot` was read. Leave the PR draft.
