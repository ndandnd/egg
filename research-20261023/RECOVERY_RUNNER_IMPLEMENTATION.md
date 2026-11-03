# Recovery operational runner implementation

23 October 2026. `src/experiments/recovery_qualification.py` adds `freeze`,
`self-test`, `run`, and `analyze` around the qualified recovery coordinator and the
existing campaign's receipt, pruning, watchdog and group-cleanup helpers.
`src/tests/test_recovery_qualification.py` provides solver-free checks. Native,
lift, coordinator and historical source/results remain unchanged. No fixture was
generated, native matrix frozen, solver dispatched, protected case read, model
trained, or cluster job run in this package.

## Checks and carried accounting

| Parent-supervised attempt | Outcome | Allocation charge (s) | Supervisor CPU (s) |
| --- | --- | ---: | ---: |
| `runner-checks/attempt01` | 39 passed in 1.97 s | 2.789626583456993 | 0.059588 |
| `runner-checks/attempt02` | 41 passed in 1.95 s | 2.287451916374266 | 0.057350 |

Pre-native review after attempt01 found that a recorded unexpected prefix native
failure could still permit the same task's cold continuation. The checked
source/test/supervisor were archived before the prospectively authorized repair.
The minimal repair closes `dispatch_allowed` on `engineering_events`; the existing
classifier still excludes the expected injected setter exception and permitted
alternative raw/completion rejections. Two targeted emitted-failure-to-gate cases
exercise that distinction. `RECOVERY_RUNNER_REPAIR02.md` preserves the decision.

Both attempts retained stable sources and terminal receipts, with all registered
owned process groups absent. Most tests used fake clocks/models/monitors and
receipts; one bounded real ownership test reused the frozen parent-death and
TERM-resistant descendant helper. It fsynced each detached PGID into the outer
supervisor's registry before the helper could inject parent death. Backend imports
were forbidden. The implementation agents executed no checks themselves.

Carry forward **128.4036048752605 charged seconds**: the previous
88.20958837542922, this package's 30-second administration allowance, its explicit
5-second repair allowance, and both check allocations/supervisor CPU. The original
900-second ceiling, 720-second dispatch stop and 180-second shutdown reserve remain.
These passing checks establish implementation preparation, not native-start,
40/80-case or numerical qualification.

## Operational contract

The immutable matrix is 40/80 trips × static/recovery/cold/start-fault, seed 17,
30 seconds each, existing nonlearned ranking, 30% plus top-three coverage, and `day`
tariff. Candidate bases 50998/50999 are **unverified identities**, not reservations.
Freeze requires a complete identity-only exclusion registry covering screen,
training and study bases, with an attestation; no economic outcomes choose cases.
The existing scale generator borrows parameters only from TRAIN assignments.

Freeze first requires passing checks bound to current runner/test/coordinator
hashes, intact output hashes and no surviving owned groups. Current accounting
must include at least that passing check's cumulative total plus later overhead.
It freezes all `src/egglab`/`src/experiments` Python sources, fixture/market/movement
inventories, reserves, faults, task IDs, evidence, interpreter/package versions and
an explicit native-library hash. Models are an explicit empty inventory. Runtime
backend fallback, changed environment, source, movement order or fixtures is
rejected. Exclusive writes prevent silent replacement or partial-freeze reuse.

The supervisor supplies an anchor before interpreter launch. Recovery retains
12/15-second prefix and 24/27-second full cutoffs, a shared three-second native
completion allowance, and finalization by 30 seconds. Standalone static/cold
controls use integer cutoff 24 and physical cutoff 27. Static bounds stay
restricted; full bounds reuse the qualified original-MIP objective guard. Every
witness is independently replayed/billed; the physical fallback survives faults.
Unexpected engineering errors close subsequent native calls and task dispatch.

The scoped native adapter restores hooks, verifies seed/thread/backend/library,
reads the actual complete binary start inventory, checks its exact selected bits,
omits continuous starts, and preserves bounds/constraint counts. It flushes Python
and C stdio for native log byte spans. Submitted/accepted/rejected/unknown remain
separate; setter success is not acceptance. Unmatched processing text stays
unattributed and cannot satisfy the processing gate. The start-fault adapter raises
a specified exception only after a durable fallback exists.

One exclusive supervisor owns one worker. Bounded monitors sample process trees
at ≤0.25 s and pressure at ≤1 s; monitor errors, >5 GiB RSS, or sustained low memory
stop dispatch. Observed escaped descendant groups are retained, killed and checked.
The frozen watchdog handles supervisor death. Every launch must fit its complete
32.5-second outer allocation plus shutdown inside the cumulative budget. Missing
final CPU is conservatively charged; supervisor/analysis CPU is added separately.

Artifacts include immutable attempt/result/completion and physical plan/replay,
append-only native/resource events, terminal supervisor receipts, and a fsynced
hash-chained qualification ledger. A bounded nonblocking worker→supervisor pipe
acknowledges actual completion fsync time and hashes; the receipt persists it.
Delayed polling cannot move the result endpoint, and missing/malformed/late
acknowledgment censors completion. Cleanup does not change the endpoint.

Resume verifies task/lock/anchor, accounting, ownership, hashes and launch/finish
inventory. Completed failures are skipped and stop further dispatch. Incomplete,
corrupt or unknown attempts block resume pending audited reconciliation. Analysis
uses the same exclusive owner, independently replays witnesses, validates bills,
mapping/bounds/resources/endpoints/budget, and emits machine-readable counts,
denominators, bills, witness identity, native evidence and unresolved gates.
Natural no-plan outcomes cannot replace required fallback/fault/processing coverage.

## Deferred freeze supervision and next commands

Native freeze remains deferred. A future external resource/budget supervisor must
charge its fixture generation, failures and overhead. That wrapper is not supplied
by this package. Native `run` refuses to launch without its immutable
`--freeze-receipt`, whose required schema is:

```json
{
  "phase": "recovery_fixture_freeze",
  "lock_sha256": "SHA256_OF_COMPLETED_LOCK",
  "passed": true,
  "failure": null,
  "monitor_failure": null,
  "source_changes": [],
  "elapsed_allocation_s": 1.0,
  "sampled_peak_rss_bytes": 1000000,
  "charged_cpu_s": 1.0,
  "supervisor_cpu_s": 0.1,
  "cumulative_qualification_charge_s": 129.5036048752605,
  "termination": {"owned_pgids": [12345], "surviving_pgids": []}
}
```

Numbers above are illustrative, not receipts. Real charges must be finite and
nonnegative, elapsed allocation ≤32.5 s, RSS ≤5 GiB, all owned groups absent, and
cumulative charge ≥frozen prior total + worker/supervisor freeze charges. The run
binds its path/hash, carries the larger conservative/actual freeze charge, and
analysis revalidates the binding.

After a complete fresh-identity registry, current cumulative accounting and that
external freeze supervisor exist, commands have this shape. **None were executed.**
The lock parent must exist; `fixtures/` and all artifact destinations must be new.

```sh
# Execute only inside the prospectively budgeted external freeze supervisor.
PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification freeze \
  --lock research-20261023/recovery-phase1-v1/lock.json \
  --checks research-20261023/runner-checks/attempt02 \
  --accounting /absolute/path/to/current-cumulative-accounting.json \
  --reservations /absolute/path/to/complete-identity-only-reservations.json \
  --native-library /absolute/path/to/phase0-qualified-native-library --backend GRB

PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification run \
  --lock research-20261023/recovery-phase1-v1/lock.json \
  --freeze-receipt research-20261023/recovery-phase1-v1/freeze-supervisor.json \
  --output research-20261023/recovery-phase1-v1/runs

PYTHONPATH=src .venv-local/bin/python -m experiments.recovery_qualification analyze \
  --lock research-20261023/recovery-phase1-v1/lock.json \
  --output research-20261023/recovery-phase1-v1/runs \
  --report research-20261023/recovery-phase1-v1/gates.json
```

Current accounting is at least 128.4036048752605 seconds and must include later
preparation/failed work before freeze. The eight-task native matrix remains
unfrozen and all numerical gates remain unclaimed; no ranking inference follows.
