# Bounded full-model recovery interface — 23 October 2026

Implementation only. No optimization, training, cluster work, qualification launch,
commit, or modification of frozen model/protocol/evidence was performed.

`egglab.native_pathflow.solve_planner` accepts optional `start_plan`, `start_case`,
and absolute monotonic `deadline` keywords. Omit `start_case` for an existing full
case witness; supply the immutable pruned source case otherwise. The effective
search deadline is the minimum of the caller's deadline and the existing budget's
relative cap. The caller must start its common clock before acquisition/loading;
this interface does not grant acquisition a fresh allowance. No new reserves or
experimental allocation are selected here. Native phases and completion share
the effective deadline. Physical fallback validation/finalization is still charged
and can overrun; elapsed wall/CPU and deadline overrun are returned explicitly.

`egglab.recovery_lift.lift_plan` promotes the reviewed pure prototype without
changing its physical checks or numeric tolerances. It validates source/full IDs
and physical definitions, independently replays both cases, deep-copies physical
events only, recomputes full loads/operating cost and the exact rational target
bill, and retains provenance. No continuous-grid or cached source aggregate is
copied. Source extraction policy is retained as provenance; physical admission
supports physical plans without claiming a native extraction identity.

The planner saves the lifted witness before model setup. Every rebuilt full
unrestricted tangent model receives all movement binaries by full movement ID,
including explicit zeros on extra edges, through the existing inventory-checking
`_attach_pricing_start`. No bounds or constraints are fixed for this start and no
continuous variables are submitted. Submission and unknown solver acceptance
are reported separately. Start setup rejection, backend exceptions, timeout,
no incumbent and later admission failures preserve the best admitted physical
bill. An infeasibility result conflicting with the witness is reported as
`model_replay_contradiction`. Fallback-only status is `feasible`, with lower
bound negative infinity; no restricted or completion bound is promoted. The
existing candidate/admit-bound boundaries supply full native bounds separately
from the fallback bill. Existing no-start defaults retain their prior behavior.

`solve_pricing` additionally accepts the same absolute deadline and optional
`start_case` for source/full mapping validation. Its historical no-fallback failure
semantics are preserved. `_checked_pricing_start` accepts the existing completion
policy for same-case starts; its explicit source-case path uses the pure physical
lift. These APIs do not certify native start acceptance.

Solver-free validation (local Python environment):

```
PYTHONPATH=src:research-20261017/recovery-prototype .venv-local/bin/python -m pytest -q src/tests/test_recovery_interface.py research-20261017/recovery-prototype/test_recovery_lift.py src/tests/test_native_pathflow_mip_start.py src/tests/test_pathflow_completion_retention.py
```

Result: **51 passed in 0.29 s** (final targeted run). `git diff --check` passed. Tests cover permutation/extra-zero inventory,
unchanged binary bounds and no continuous starts, source/full physics violations,
changed tariff recomputation, fallback retention across setup/backend/replay/no
incumbent failures, infeasibility contradiction, deadline exhaustion, invalid
fallback rejection, full-bound/fallback-objective separation, and existing
same-round raw/completed candidate retention. Native qualification is outstanding
and must use a separately frozen tiny budget; no solver conclusions follow from
these mocks or handcrafted physical fixtures.

Review follow-up: planner diagnostic callback failures are contained and returned
as `instrumentation_failures`; incumbent capture failures are handled within the
protected candidate stage. Fault tests exercise both. An admitted later witness
that contradicts an earlier global lower retains its bill, invalidates the lower
to negative infinity, reports `bound_replay_contradiction`, and preserves the
conflicting values/action. A final enclosure guard covers failures before the
ordinary bound comparison. Review follow-up suite: **57 passed in 0.35 s**, plus
clean `git diff --check`; no native solver calls.
