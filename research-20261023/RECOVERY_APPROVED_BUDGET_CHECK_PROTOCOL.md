# Approved total-budget amendment: one source-bound check

24 October 2026 UTC. The user explicitly approved increasing **total cumulative
native qualification** to **1,800 charged seconds**, with **1,620-second dispatch
stop**, **180-second shutdown reserve**, one numerical thread and **5 GiB** owned
process-tree RSS. This replaces the previous 900/720 limits prospectively. It is
not 1,800 additional seconds and resets no historical charge or receipt.

Carry **587.8814716266195 seconds** from
`admission-capture-checks-v2/accounting.json`. Add **one 20-second administrative
allowance for the whole approved revision package**, including this check,
subsequent freeze preparation and native closeout: **607.8814716266195 seconds
before actual new execution**. Do not add another administration allowance at
freeze or native launch. Charge actual check, freeze, worker, monitor, supervisor,
failure and finalization work additionally. The allowance is conservative
accounting, not measured utilization.

## Exactly one check

Prepare one exclusive `admission-capture-checks-budget/attempt01`, using the
reviewed `run_admission_capture_checks_v2.py` supervision behavior. The new
`run_admission_capture_budget_check.py` is an explicitly authorized policy-only
copy: its supervision, cleanup and accounting helpers are unchanged. Parent owns
execution, receipts, accounting and the runtime budget patch. The implementation
agent creates the new wrapper/metadata and parametrizes its fake helper checks,
without runtime imports or execution.
Existing attempts and source-bound outcomes remain immutable.

The parent-owned runtime amendment changes only the cumulative ceiling and
dispatch-stop constants to 1800/1620. Recheck the resulting exact sources; an old
passing check does not bind this changed runtime. Freeze all transitive egglab/
experiments Python sources, the wrapper/helpers, protocol/input and these five
modules before spawning exactly this child argv:

```sh
.venv-local/bin/python -m pytest -q \
  src/tests/test_recovery_qualification.py \
  src/tests/test_recovery_supervision_repair.py \
  src/tests/test_recovery_integer_cutoff.py \
  src/tests/test_recovery_admission_capture.py \
  src/tests/test_check_supervision_v2.py
```

The same 118 cases remain, with six helper checks now parametrized over both
original/new wrappers: **124 cases**, preserving their test bodies. The parent's
two dispatch-boundary fixtures use `q.DISPATCH_STOP-20` rather than the old
literal 700, preserving the budget-guard scenario under the approved ceiling.
No fixture generation, trained-asset load,
native solver import/call, cohort inference, training or cluster work is included.
Retain its source-bound, registered, bounded ownership test. Keep sources stable
through terminal receipt review. One failed check stops this package; no automatic
retry, altered assertion or hidden replacement attempt is authorized.

Retain 30-second check work and absolute 32.5-second outer cleanup allocation,
one thread, 5 GiB, 0.05-second target scheduling and the strict 0.25-second completed-
sample policy. Shared query deadlines, overlong-query failure, explicit detached-
group registration, permission-denied unknown state, bounded owned cleanup and
first-primary/all-secondary failure evidence stay unchanged. A raised resource
budget does not loosen resource monitoring or physical/native cutoffs.

Charge max(allocation elapsed, sampled owned-tree CPU, total reaped-child CPU)
plus own supervisor CPU. Monitor children already belong to total child CPU;
record their separate diagnostic without adding it twice. Require exact source,
argv, prior-evidence and output hashes, complete charge observations, successful
exit and all owned groups confirmed absent. Missing/failed audit or ownership
proof cannot pass, even if pytest prints success. Preserve any incomplete spend
as requiring separate reconciliation before authoritative carry.

## Metadata and execution boundary

The new wrapper has explicit fixed policy: prior
`admission-capture-checks-v2/accounting.json`, carried 587.8814716266195, single
package administration 20 and fresh `admission-capture-checks-budget/attempt01`.
It preserves the old wrapper and verified historical evidence. Its prior-artifact
inventory uses the passing v2 receipt's actual attempt/result/log/resource/
ownership/registered-group filenames; it does not expect a nonexistent new
cleanup-reconciliation file. The earlier failed check/reconciliation remain
bound through inherited accounting evidence.

`admission-capture-checks-budget/command.json` records exact parent and child argv,
parent environment, stable source inventory, carry and limits; no runtime input
adapter is needed. Added bound inventory is
the old wrapper, this new protocol, `RECOVERY_BUDGET_APPROVAL.json` and command
JSON, in addition to current runtime/tests and existing helper evidence. The
wrapper freezes exact source/argv/evidence hashes before Popen. The parent has
confirmed the two budget fixtures are final; the wrapper, dual-wrapper fixture
and this protocol are held stable for review. The command JSON cannot include its
own hash; the wrapper binds that file in the actual attempt inventory. A stable
source inventory is not a passing check result.

Exact parent command, recorded only:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 \
.venv-local/bin/python research-20261023/run_admission_capture_budget_check.py
```

These parent settings apply before importing runtime helpers. The wrapper also
sets the same six numerical thread variables and bytecode policy on its child.
Keep the historical external freeze wrapper immutable: after this check the
parent must verify its stricter legacy entry guards against the actual new carry
before using it; no historical evidence hash is silently updated.

A passing check is an engineering gate only. Parent must separately review the
subsequent source/environment/task lock and externally supervised freeze receipts
before any deliberate native dispatch. Old failed native-v1/v2/v3 outcomes stay
failed; neither the new ceiling nor this check creates a native qualification,
comparison result or scientific claim.
