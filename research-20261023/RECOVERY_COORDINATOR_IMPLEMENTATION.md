# Shared-clock recovery coordinator implementation

Parent closeout: source-hashed supervised attempt02 passed all34 coordinator tests after the explicitly recorded exact-rational test repair. Only the new coordinator test module was run in this package, not the older interface suite. See `RECOVERY_COORDINATOR_RESULTS.md`; this establishes solver-free checks only, and the operational/native runner remains deferred.

Implementation package only. No native solves, training, cluster work, sealed-case
reads, campaign dispatch, or numerical qualification are authorized by this file.
The source/tests are prospective until the separately supervised solver-free check
has an immutable source hash, resource receipt, and charge in the cumulative ledger.

## Runner boundary

`egglab.recovery_coordinator.coordinate(source_case, full_case, a, b, *,
parent_monotonic, deadline, storage, budget=None, planner=None,
clock=time.monotonic, allowed=lambda: True, physical_fallback=None)` performs at
most one restricted prefix planner invocation and one unrestricted full invocation.
The default planner is the existing `native_pathflow.solve_planner`; injected test
planners use its exact signature. It requests `completion=True` in both stages.
There is no new solver implementation or frozen-source modification.

The supervisor must supply its monotonic anchor from **before interpreter launch**
and `deadline=parent_monotonic+30`. Imports, loading, preparation, failed work, lift,
start setup and materialization consequently consume the same allowance. The
coordinator cannot extend or reset either value. The fixed schedule is:

| Activity | Absolute end / cap |
| --- | --- |
| Prefix integer search | anchor + 12 seconds |
| Prefix extraction, completion, replay and durable lift | anchor + 15 seconds |
| Full integer search / latest full planner entry | deadline - 6 seconds; entry strictly earlier |
| Full extraction, completion and replay | deadline - 3 seconds |
| Finalization and result/completion artifacts | deadline |
| Native fixed-topology completion | 3 seconds cumulative across both stages |

The completion interpretation is conservative: elapsed wall time inside every
fixed-topology native call, including failing calls, debits **one shared 3-second
allowance**, preserved across prefix/full and across feasibility/objective calls.
It is not replenished by early prefix return. Physical extraction/replay overhead
also consumes the corresponding absolute planner cutoff. A native overrun cannot
be preempted here; it is charged by elapsed time, remaining calls are gated, and
the supervisor must enforce the outer process deadline and censor overruns.

A narrowly scoped context manager wraps `pf._optimize_once`, as the existing local
campaign worker does. A model is fixed-topology only when its nonempty routing `x`
list has every lower bound equal to its upper bound. Each native call receives the
minimum of its original deadline, physical stage cutoff, and either integer cutoff
or remaining cumulative completion allowance. The budget phase limit is likewise
clamped. The hook is restored on success/failure, and a nonblocking process lock
rejects nested/concurrent coordinator scopes. This mechanism is for the specified
single serialized worker; other threads must not call the planner concurrently.

`allowed` must return exactly `True` to permit dispatch. Exceptions fail closed.
It is checked before planner entry and each native call, so an eventual supervisor
can expose parent-death, resource-stop and monitor-health state. Process ownership,
descendant termination, CPU/RSS/pressure monitoring and shutdown are supervisor
responsibilities, not implemented or qualified by this module.

## Witness and bound behavior

A prefix plan goes through the existing `recovery_lift.lift_plan`: source replay,
unique movement-ID/physics checks, full replay, exact target-market bill, and a
full movement binary inventory. Cached solver bills, source grid indices,
continuous starts and restricted bounds are not used as full-case evidence.
`storage.save_fallback` is called explicitly before any warm full invocation;
required persistence never depends on the planner's diagnostic callback. A save
failure blocks full dispatch and produces `storage_failed`. A save that completes
after the prefix cutoff is recorded as a timing failure, while its already saved
physical fallback remains available. Any dispatched prefix that misses its physical
or durable cutoff stops further full dispatch, even if the full-entry gate would
otherwise have time remaining. Loading that skips prefix dispatch altogether may
still take the cold full path with the actual remainder.

The retained durable fallback lives outside the native planner; the planner receives
a deep copy as `start_plan`, with `start_case=full_case`, while the original witness
and exact bill survive start rejection/unknown processing, native exceptions,
timeout, no incumbent, failed extraction/completion, later replay rejection and
contradictory full infeasibility. An optional initial physical full-case fallback
is independently replayed and persisted by the same path. With no admitted prefix
witness, unrestricted continuation is cold with the actual remaining time. With no
remaining launch time, finalization proceeds without a planner/native call.

A later full plan is independently replayed/billed and can replace the selected
witness only if its exact rational bill decreases. The original durable witness
remains in `fallback`; the final selected physical witness is in `selected` and
materialized in the result. Their objectives never inherit a solver incumbent.

`restricted_prefix_lower` is diagnostic only. Global lower-bound provenance comes
only from admitted unrestricted full-model rounds with matching native matrix and
formulation identities. The coordinator invokes the existing `_candidate_score`
and `admit_bound` objective/replay guards with each round's **original unrestricted
MIP lower bound**, using a completion incumbent only when the selected plan came
from completion. It never takes the fixed-route LP lower bound. Stored round
endpoints must match the unchanged guard. Reversed bounds or full infeasibility
against a saved physical witness invalidate global lower state and expose a
contradiction; these outcomes cannot certify or discard the fallback.
Independent bound admission also checks the clock after replay and objective
validation, so a replay crossing the planner cutoff cannot import a late bound.

## Storage and endpoint contract

`DirectoryStorage` provides exclusive, fsynced `fallback.json`, then fsynced
`result.json`, then hashed `completion.json` in a fresh attempt namespace. Directory
entries are fsynced too. Existing files raise instead of silently overwriting or
resuming. A custom storage implementation must provide the same durable-before-
return guarantees for `save_fallback`, and `materialize(result, schedule=..., clock=...)`
must return `censored` plus the result-materialization endpoint measured after
result fsync. The return envelope contains `result`, `completion`, and `censored`.
Materialization failure is censored with its failure record. Serialization time is
charged; late result or completion materialization is censored. Cleanup is outside
the endpoint. The supervisor must also validate completion presence/hash/schema and
its own observed timeliness; the result receipt cannot certify itself.
Nonfinite values in diagnostic events and the separate raw restricted-bound
diagnostic are encoded as tagged `nonfinite_float` objects. Physical witness fields
and admitted bound fields retain strict finite JSON serialization; diagnostics
cannot relax physical admission.

The future runner still must own immutable `attempt.json`, append-only
`native.jsonl`/`ledger.jsonl`, supervisor receipts and CPU/resource accounting;
source/model/environment freeze; output namespace/source locks; terminal/failure
resume skips and audited reconciliation of incomplete attempts; parent/descendant
shutdown; and the existing 900-second ceiling / dispatch reserve. The module's
`events` are in-memory diagnostic facts, not a substitute for those receipts. This
package does not implement the numerical matrix or claim operational-supervisor
qualification.

## Solver-free checks prepared

`src/tests/test_recovery_coordinator.py` uses a handwritten one-trip physical
fixture and an import guard rejecting native solver imports. It covers ID inventory
and changed target tariffs at durable admission, clock costs carried from loading,
cold continuation, fallback survival and exact bill retention, late save and
serialization, no-time finalization, invalid fallback, failed durability, resource
and parent gate failures, cumulative completion limits, hook restoration/nesting,
original full MIP versus restricted/fixed-route bounds, objective tampering, and
exclusive hashed result/completion storage. Additional static review cases cover
dispatch stop after a late prefix save, late independent bound replay, a gate check
that crosses the integer cutoff, and nonfinite diagnostic serialization. A fake optimizer also traverses the
actual `solve_planner` API with completion enabled. Existing recovery interface
checks remain relevant and unchanged.

Bounded solver-free command used by the parent check protocol:

```sh
PYTHONPATH=src .venv-local/bin/python -m pytest -q src/tests/test_recovery_coordinator.py
```

No tests were run by the implementation agent before handing this source package
to the parent for its explicitly charged check. The parent's immutable
`coordinator-checks/attempt01` receipt reports **22 passed, 12 failed**; all twelve
failure locations compare an exact bill with the incorrect literal `119/2`.
The runtime correctly evaluates the stored binary float coefficient `.2` exactly:

```python
Fraction(7) + 2*15 + Fraction(.2)*225/2
# 2143713422628356141/36028797018963968; float value 59.5
```

The tests now derive that rational directly from the handwritten fixture and
retain exact string equality. No coordinator, lift, guard or arithmetic source
changed for this repair. These are test-expectation failures; assertions after
those failure locations still require the separately charged repaired check.
The first check charged 0.7734692078083754 allocation seconds plus
0.01885300000000001 supervisor CPU seconds, carrying the cumulative qualification
charge to **87.67245720780838 seconds**, including the existing administrative
allowance. The first attempt's source snapshot and receipts remain unchanged.
`RECOVERY_COORDINATOR_REPAIR02.md` records the prospective reason for the second
permitted check; that check has not been run by the implementation agent.

Supervisor process-tree failure,
missing/corrupt receipt and complete resume behavior remain future-runner checks,
not tests claimed by this bounded coordinator package.
