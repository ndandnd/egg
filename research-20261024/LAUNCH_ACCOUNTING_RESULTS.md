# Canonical launch-accounting regression checked

24 October 2026. One affected solver-free check completed. This closes the
identified arithmetic regression at the pure helper boundary; it does not show
that a controller invokes the helper or qualify a native mechanism.

`src/egglab/launch_accounting.py` retains raw freeze charge
3.1857290000000003 but derives the comparison freezer's canonical component
3.1857290000000376 using the same cumulative-minus-carried expression as its
consumer. It validates exact receipt addition, finite nonnegative inputs and
independently reconciled funding, and returns an immutable record. It neither
writes a ledger nor grants launch authority. The generic recovery freezer's
maximum-with-lock-floor policy is outside this helper's contract.

## Evidence

- Independent source review found no blocker, then checked the prospective budget,
  exact command and14 frozen source hashes before execution. See
  `LAUNCH_ACCOUNTING_REVIEW.md` and `launch-accounting-checks/command.json`.
- ONE exclusive `launch-accounting-checks/attempt01` ran only
  `src/tests/test_launch_accounting.py`: **8 tests and48 subtests passed in0.02s**.
  Handwritten cancellation values, exact component/JSON equality, reconciliation,
  rejected malformed/underfunded inputs and immutability were exercised. No old
  test matrix, numerical library, model, fixture or capture was a test input.
- Owned PGID43658 was absent, leader reaped, no surviving groups or cleanup errors.
  Monitored peak RSS35,356,672 bytes; no changed sources, failure or unresolved
  accounting. The driver reused the reviewed monitoring/ownership/cleanup helpers.
- Inherited bound proof bytes were hash-checked, not parsed as research inputs.
  No metadata freeze, solver/controller launch, native retry, model training,
  inference, new timetable or cluster action was performed.
- The15 bound source files were preserved as exact immutable byte snapshots,
  matching the attempt's original hashes. The final proof root uses these
  snapshots rather than new mutable live source paths. Original receipts remain
  unchanged; the parent snapshot manifest is separately bound.

## Complete carry-forward

Authoritative account: `launch-accounting-checks/accounting.json`.

| Item | Charged seconds |
| --- | ---: |
| Prior v4 failure and all inherited work |1518.4011370494984 |
| Complete internal source-check charge |2.004292790684581 |
| Positive whole-process excess |0 |
| Conservative parent closure |0.5 |
| Conservative immutable-source preservation charge |0.25 |
| **New cumulative charge** |**1521.155429840183** |

Internal charge is allocation1.2415297906845808 plus supervisor0.762763.
Whole-process time was1.33wall/.66user/.52system; its precision-adjusted1.35s
envelope did not exceed the conservative internal charge, so nothing was
subtracted. The pre-snapshot carry1520.905429840183 remains recorded; no charge
was removed. ADMIN0. All859 inherited/new proof paths are retained in the account.
The20-second source package end1538.4011370494984 and current1920/1740/180 policy
were respected; the package also fits below the former1620 dispatch stop.

The rejected v4 ledger and all historical sources/receipts remain untouched.
Zero native workers have been launched by that failed package. The actual ACK
observer and CF1 charging/start mechanism remain runtime-unqualified. No model
quality, economic performance, global bound or publication conclusion follows.

Next: use this helper in a small source-bound prospective initializer rather than
copying raw components manually; verify the exact ledger-prefix contract without
a solver. A future numerical attempt still needs its separately recorded decision,
fresh namespace and all current spending carried. This check is not that decision.
No routine Google Doc entry was added for passing arithmetic engineering.
