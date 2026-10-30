# Prospective infrastructure recovery of array720831

Array720831 remains the original immutable twelve-task attempt at source commit
`75dd4cf19f1f735cc3dea559567da3b2bd32013e`. Its outputs, successful models,
failure artifacts, accounting, environment and protocol must be retained. This
separate prospective recovery changes scheduling and runtime diagnostics only.
It must not be submitted until root has pinned/reviewed its source and recorded
the original terminal accounting and backup. No submission is performed by this
implementation package.

## Infrastructure evidence and bounded diagnosis

The scoped `tmp/accounting-720831-current.txt` has nine `FAILED|4:0` task rows:
`0,1,4,5,6,7,8,9,11`, all on `snavely-cpu-01` or `snavely-cpu-09`, elapsed
7–13 seconds. Their stderr reports `Illegal instruction`; their wrapper receipts
record child exit132 (128+SIGILL), not a timeout. Each retains launch and source
identity but no Python failure/completion receipt or candidate-start artifact.
The frozen runner saves source identity before importing XGBoost, importing
CatBoost, loading the pool and entering `run_fold`. Thus the demonstrated crash
window is native import or pool loading before a candidate fit, rather than a
failed model fit. Neither a particular library nor an exact unsupported
instruction has been established by the existing artifacts.

Tasks2,3,10 completed with the same pinned versions. Task2 used
`snavely-cpu-16` and was allocated two CPUs despite requesting one. Tasks3/10
used `unicorn-cpu-75`, each allocated one CPU. A read-only `scontrol show node`
inspection found `sb,avx` features on unicorn75; failed01/09 advertise only the
generic `intel,cpu` features. Snavely16 also differs in CPU topology. This supports
a node-dependent native compatibility hypothesis, but scheduler feature absence
does not prove CPU instruction absence. Recovery uses the observed working node
unicorn75; it does not change libraries or claim a specific ISA requirement.
No outer result or inner metric is consulted to define the recovered task set,
node choice, model settings or output namespace.

## Frozen recovery scope

Exactly the nine task IDs `0,1,4,5,6,7,8,9,11` are eligible. Successful original
tasks2,3,10 are retained without refitting. The original driver and model code
remain unchanged; the new stdlib supervisor calls the frozen `run(task_id,
pool_sha, output_root=...)` using the same original fold/seed mapping and all
scientific settings from `ROUTE_MODEL_FAMILIES_V5_PROTOCOL.md`. The exact128
manifest remains SHA256
`d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d`.
The supervisor requires the exact frozen18-path `source_identity.json` source-hash
set and verifies every hash against the recovery checkout before any child import.
A mismatched source, task identity,
pool, original wrapper status or candidate progress is a stop, never a resume.

New output namespace:
`result/physical_learning/20260930-route-model128-families-v5-recovery1`.
Original evidence is passed explicitly with `EGG_ORIGINAL_ATTEMPT_ROOT`, expected
to point to the retained original remote checkout's attempt directory. Each
task's separate `taskNN.runtime` directory is created exclusively before work;
any existing directory blocks a second invocation. The frozen trainer still
creates `taskNN` exclusively. There is no retry, requeue or partial resume.

Wrapper `src/cluster/physical_route_model_families_v5_recovery1.sbatch` declares
array `0,1,4,5,6,7,8,9,11%4`, `--nodelist=unicorn-cpu-75`, one requested CPU,
8GB, 30 minutes, 1700-second whole-supervisor shell cap, numerical/native
threads1, no requeue and excluded node `scaglione-compute-01`. The supervisor
also requires exactly one requested CPU and records actual allocation separately,
as in the original protocol. Nine tasks give at most4.5 requested
CPU-hours, excluding the retained original attempt's separately reported cost.
At most four recovery tasks run concurrently. The shared original isolated
interpreter `/home/nc437/egg-route-family-env-20260930/bin/python` is reused
read-only, with unchanged package pins; no shared old environment is modified.

## Runtime diagnostics and interpretation

The supervisor imports only Python stdlib. Before loading any real pool it runs
separate 60-second child probes for pinned XGBoost import, pinned CatBoost import,
then a 32-row/four-feature synthetic two-tree fit/predict of XGBoost, CatBoost and
ExtraTrees. All synthetic fits use one native worker and touch no scientific
datasets; they do not alter the frozen training menu. A child signal is captured
as a negative subprocess return code and named signal, with start event,
elapsed time, stdout/stderr and their hashes. A failed probe stops before TRAIN
materialization and saves `runtime_preflight_failed`; no alternative library,
candidate or node is selected automatically. CPU model/flags from `/proc/cpuinfo`
and recovery/original source hashes are retained in `recovery_launch.json`.

Training is then one separate child of the original runner. Its native failure
also leaves a supervising receipt even if Python's own failure handler cannot
run. The child budget consumes the remaining portion of a1680-second supervisor
budget; the independent shell cap remains1700 seconds. Handled and hard failures
retain the frozen driver's existing progress rules plus runtime/wrapper evidence.
If the supervisor itself is killed, the shell wrapper may be the final receipt.

Root must record a new launch receipt and backup all original/recovery outcomes
and scoped accounting separately. On completion, independently replay the three
retained original tasks and nine recovery tasks with pinned dependencies before
any combined analysis. A provenance mapping must identify array720831 tasks2/3/10
and the new array's nine replacement task IDs. Runtime differences and original
failed cost remain reportable; twelve combined fold/seed rows remain repeated
measurements, never twelve independent datasets. Reserved data remain sealed.
