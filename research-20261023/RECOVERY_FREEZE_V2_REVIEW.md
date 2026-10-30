# External freeze supervisor v2: source review

24 October2026 UTC. Independent source-only review; no reviewer execution,
imports, tests, fixture/model reads or native dispatch. Old freeze wrapper and
failed receipt remain immutable.

Parent reports reconciled carry718.8639492101057s, including the full failed
allocation and explicit watchdog allowance. This review does not recompute or
replace that separate accounting. Approved1800/1620/180 policy applies; no
automatic retry or native launch is authorized by source readiness.

Final stable source/test readback is pending. Scope is the new wrapper's actual
use of reviewed budget-check `cleanup_receipt` with absolute anchor+32.5 deadline,
retained known PGIDs/reap/unknown/primary-secondary evidence on failure, confirmed
absence pass gate, approved budget constants, unchanged input/source/resource/
physical clock rules, and import-safe fake tests.

## Initial stable source/test readback

Read the new wrapper and10 fake cases. Actual cleanup calls the reviewed
budget-check `cleanup_receipt` with absolute anchor+32.5; a helper exception
retains known groups as unknown, reap status, primary and secondary errors.
Success requires confirmed absent group states and a reaped leader. Inputs use
approved q budget constants while argv/source/resource/worker clocks remain
unchanged. Tests prevent import-time child/native dispatch and exercise the
actual supervisor's terminal receipt, not only cleanup helpers.

One residual audit path was sent to parent/owner: final `RUSAGE_CHILDREN`
observation remained unguarded, so its failure could discard retained terminal
ownership/error evidence before receipt. Use the reviewed check-wrapper pattern:
explicit unknown child CPU/incomplete accounting, elapsed lower-bound charge,
retained audit error and failed gate, with a focused fake regression. Old wrapper
and q runtime need no change. Final repair readback is pending; no execution.

## Final stable source verdict

Read back the narrow child-CPU guard and11 fake cases. Observation failure now
preserves the original primary cause and a separate `child_cpu_audit` error;
child CPU is explicitly null, accounting unresolved/incomplete, and the charge
marked a lower bound. Available elapsed/sample/worker costs remain retained;
the pass gate explicitly rejects the missing observation. The actual supervisor
fake regression checks that ownership and cleanup evidence still reach the
terminal receipt with this failure.

No remaining source-level blocker was found for a parent-owned prospective
source-bound check of the new wrapper/tests (135 total cases with the existing
suite). This is static readiness only, not an executed check or fixture/native
launch gate. Preserve old sources/hash chains; bind the new dependency, wrapper,
tests and protocol before any separately authorized check. Approved budget,
original physical/worker clocks, argv/source/resource rules and failure-first
dispatch remain intact. Reviewer performed no executions or runtime/test edits.
