# CF1 v5 capacity correction: independent source review

24 October 2026. Read-only source review of the narrow capacity correction,
fresh attempt02 identities, new driver and prospective protocol. No project
imports, tests, native work, research-data work, cluster work or commits were
performed. This note records no passing execution or scientific result.

## Capacity contract and scope

The diagnosis identifies 26 failures at common harness setup: the fake OS lacked
`cpu_count`, and the independently handwritten root lacked its matching
`capacity_cpu_count`. The corrected `owner_harness` defines deterministic
capacity8, exposes it through the fake OS, and places that same value in the root
before writing or hashing it. The unchanged production `_identity` continues to
compare the retained root capacity with `os.cpu_count()`.

The other fake OS binding, in the fake-parent lifecycle test, already supplies
capacity8. Its separate root is created by the unchanged `OwnerSupervisor.run`
from that fake capacity. The handwritten root, fake-parent root and existing
capacity8 supervisor fixtures therefore have matching capacity bindings. No
production capacity, ownership, timing, funding, process-creation or CPU charge
guard is weakened.

The production wrapper diff has four identity/path changes only: source-check
directory attempt02, required attempt/result IDs attempt02, and the future
freeze input `attempt02-accounting.json`. The new test's positive source receipts
use attempt02; stale receipt IDs and the alternate source directory reject
attempt01. Owner lifecycle paths named `entry-owner-attempt01` are distinct from
the source-check attempt identity and remain unchanged.

## Fresh source wrapper and clocks

The new `run_cf1_entry_repaired_capacity_checks.py` exclusively creates
`cf1-entry-repaired-checks/attempt02` and binds the separate
`attempt02-design` command/budget. It explicitly requires the closed failed
predecessor, its unchanged sources and completed absence/reaping, complete
accounting and the authoritative carry1534.2196428390087. It does not admit the
old failure as passing qualification. Prior attempt01, its snapshots, old driver,
command/budget, receipts and spending are not modified by this correction; the
new driver's preflight verifies their retained evidence hashes.

Work8, outer10.5, inclusive11 and parent closure2 agree between driver, wrapper
note and protocol. Carry+11+2 gives1547.2196428390087, below the original source
phase end1547.8351450899538 and campaign end1702.8351450899538. ADMIN0 and global
1920/1740/180 remain unchanged. Parent reconciliation must retain actual and
conservative charges, including positive external reconciliation, preservation
and closure, within these caps; no prior charge is reset or credited.

The retained `sample_owned` helper uses its anchor only in the sample deadline
`anchor+10`. Passing `anchor-2` binds that deadline to actual anchor+8. The real
attempt anchor, elapsed/CPU accounting, ownership events and cleanup anchor are
unchanged. Cleanup uses actual anchor+10.5. The monitor, cleanup/reaping, output
audit and conservative accounting bodies remain inherited; native clocks are
not shifted.

The command still selects only `src/tests/test_cf1_entry_repaired.py`. The eight
qualified historical test files are hash-only dependencies, and the complete
current source closure remains bound. There is no historical test matrix or
automatic rerun. The reviewed source inventory includes this review, the new
protocol/fix/wrapper notes and the new driver.

## Decision and limits

No source-review blocker was found for this diagnosed correction and one fresh,
bounded source gate. The gate is eligible only after the parent freezes the
exact reviewed command and complete manifest; this review does not execute it.
There is no automatic retry after failure.

The 26 formerly blocked owner cases remain unestablished until exercised by a
separately frozen invocation. No pass is predicted. Even a source pass cannot
establish actual owner timing, native entry, real lock qualification, the CF1
mechanism or permission for any later phase.
