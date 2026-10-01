# Graph budget v8: manual startup recovery1

This is a separate operational recovery after a diagnosed startup failure. It
does not change model mathematics, features, labels, optimization, inner stopping,
folds, seeds, epoch limits, anchor tolerances or persistence. No fitting, native
probe, SSH, submission, requeue or automatic retry ran in this local package.
Root owns independent review, source freeze, deployment and any manual launch.

## Preserved failed attempt and diagnosis

Array729522 used source commit `5ed3da7e7cd41dc319de9a35fe2f3f9f23035c01`.
All12tasks failed1:0 on node75 after one accounted second each, before any native
probe or fit. Keep all original12allocated CPU/task seconds in cumulative cost;
do not replace those costs with recovery time. The collected shell receipts
measure zero whole shell seconds, separately from the scheduler's one second.
The original wrapper, launch, logs and result root remain unchanged:

- `src/cluster/physical_route_graph_budget_v8.sbatch`
- `research-20260930/learning-campaign/LAUNCH_729522.json`
- `tmp/v8-729522-slurm/` (all12stderr files)
- `result/physical_learning/20261001-route-model128-graph-budget-v8/` (all12guard receipts)

Local verification found exactly task IDs0–11, each receipt `returncode=1`,
`wrapper_phase=guards`, and no probe path/hash. Every stderr is exactly
`/etc/profile.d/slurm.sh: line 2: INCLUDE: unbound variable`. The v8 early-trap
wrapper sourced the site's optional-variable-reading profile after enabling
`set -u`; the previously working v6 wrapper sourced it before strict mode.
No model/ISA/training conclusion follows from this startup failure.

## Recovery change and immutable identity

NEW `src/cluster/physical_route_graph_budget_v8_recovery1.sbatch` retains an EXIT
receipt trap before profile/guards. While sourcing the same absolute site file,
it temporarily disables nounset (`set +u`) so unset optional variables have
ordinary empty shell expansion, then immediately restores `set -euo pipefail`.
It does not alter the site file, manufacture an INCLUDE value, or relax required
run/task/source/runtime guards. Genuine profile nonzero exits still propagate.
The receipt distinguishes `system_profile`, `guards`, `native_probe`, `training`
and a completed-wrapper Boolean. Premature zero exit before a completed training
command is a failed attempt; native/error/timeout codes remain unchanged.

The unchanged v8 CLI's existing `--output-root` points at the NEW once-only root
`result/physical_learning/20261001-route-model128-graph-budget-v8-recovery1`.
A per-task exclusive attempt marker is created before native probe/bank access.
Existing task directories, wrapper receipts or attempt markers block reuse.
Every new receipt is exclusive and identifies original array729522, manual
recovery1, executed-wrapper SHA256, current source commit, probe hash and hashes
of recovery wrapper/tests/protocol, original wrapper/scientific sources and
original launch. Early failed guards may have missing hashes when no repository
was accessible; that is explicit failure evidence. Future admission requires
complete matching source hashes and a completed task/anchor replay, not merely
a successful shell receipt. The unchanged CLI's source identity still binds all
v6/v8 scientific/runtime dependencies; recovery receipt supplements that identity.

## Frozen science and prospective manual budget

Retain `ROUTE_MODEL_GRAPH_BUDGET_V8_PROTOCOL.md` unchanged: exact128 TRAIN pool
SHA256 `d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d`,
17features,80fit/16inner/32outer grouped folds,seeds17/29/43, original two graph
architectures/Adam, fresh fits with900epochcap,patience30,1600s/arm and3400s/fold.
Both source300anchors remain mandatory with original1e-10 absolute tolerances;
failures/missing anchors hold outer evaluation. No optimizer resume, forced
extra epochs, architecture choice by outer scores or reserved-data access.

Prospective recovery is fresh array0–11%4, each1requestedCPU/8GB/1hour/native1,
sole node75, exclude scaglione-compute-01, no requeue/automatic retry. Maximum
new requested allocation is12CPUhours; including the failed attempt gives at
most12CPUhours plus12accountedCPUseconds for these two v8 attempts. Actual CPU,
RSS and elapsed accounting must be collected separately. The existing3500second
external child allowance subtracts elapsed startup/guards/probe time before
each child invocation; native probes precede all bank reads. Scheduler1hour is
the absolute allocation boundary. Preserve every failure and time record.
Never exceed4trainingworkers or the established combined12CPU/96GB ceiling.
Any overlap with another study requires root's explicit identity-scoped check;
this wrapper does not submit work or discover/authorize concurrent workloads.

## Meaningful local checks and qualifications

`PYTHONPATH=src python3 -m pytest -q src/tests/test_physical_route_graph_budget_v8_recovery1.py`
passed9fixtures in2.61s (earlier same focused pass2.83s retained here). `bash -n`
also passes. Fixtures copy the wrapper and replace only the absolute profile
path with a temporary optional-INCLUDE profile; fake git/timeout/graph commands
never import torch, probe native operators, read a bank or fit. Checks cover
unset optional INCLUDE, restored strict mode, explicit missing required guard,
profile nonzero exit, premature profile zero exit, unchanged132/124/137native
and timeout propagation, failed training propagation, exclusive reuse refusal,
new output-root forwarding and scheduler limits. Production exposes no profile
path override. These tests qualify control flow only; every real task must still
pass the existing node75 import/operator/autograd/NPZ probe and later scientific
saved-state replay. There is no claim of recovered cluster execution yet.

Frozen original SHA256 identities (verified unchanged locally):

| File | SHA256 |
| --- | --- |
| original v8 wrapper | 1b69c398fcffa9a951d679e16e47fd657c7f891d13b04715799d6b13e551f984 |
| v8 scientific module | 0cc7ddc190efcef21cbedafd17ce741383e33f798b1a782c3f3a81e1cce47fbd |
| v8 CLI | 28b06bb59d2d72a141246daf8674d1f19178e1dc9334e68eb241f21afd622f39 |
| recovery1 wrapper | 19fb6bcb02a9b55e4310974bb1b1e61e8850a7f0576317087b2918c1f9a62b78 |
| recovery1 tests | b4c4802578ab61d439e0fb56e318fad66f1591b4536fb9043b2935692002d333 |

The recovery protocol's own hash is bound by wrapper receipts and the next
reviewed source freeze. Original attempt artifacts are never overwritten.
