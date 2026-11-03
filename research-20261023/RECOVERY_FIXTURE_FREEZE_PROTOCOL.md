# Prospective externally supervised fixture freeze

23 October 2026. Preparation only: this file and `run_recovery_freeze.py` have not
been executed by the implementation agent. The parent owns launch authorization,
source readback, accounting and all executions. No checked core/runner/test source
is edited, preserving the passing 41-test binding. This wrapper permits only the
existing runner's `freeze` command; it never starts a native solve or the eight
qualification tasks.

The parent launch protocol carries **128.4036048752605 charged seconds** plus a
**20-second package allowance**, hence **148.4036048752605 seconds before freeze**.
The explicit input-accounting JSON must include that total and all later failed
work. The ceiling remains 900 seconds, dispatch stop 720 and shutdown reserve 180.
Before launch the full 32.5-second allocation plus shutdown must fit. Every failed
freeze retains its actual/conservative charge and needs an explicit prospective
repair before another attempt; no retry or incomplete-attempt resume is automatic.

The metadata-only registry and explicit design selected **50997/40 and 50999/80**.
The rejected 50998 identity remains in provenance. The core default is therefore
not used: `freeze-command.json` must include the parent's explicit `--design`.
Registry completeness/disjointness is parent/reviewer evidence, not an inference
from economic outcomes. No fixture exists until the authorized wrapper executes.

## One-shot wrapper and ownership

Run with the checked `.venv-local/bin/python`. `--command-json` must contain a JSON
argv array beginning with that interpreter's absolute `sys.executable`, `-m`,
`experiments.recovery_qualification`, `freeze`. Only explicit freeze flags are
accepted; all command paths must be absolute. Its lock/check/accounting paths must
match the wrapper's arguments. The lock parent must exist, with new lock and
`fixtures/` destinations. The attempt directory is created exclusively and never
reused, including after input-validation failure.

The wrapper reuses the already checked `run_recovery_runner_checks` snapshot,
descendant/group ownership and cleanup helpers, bounded monitor calls, and the
frozen campaign parent-death watchdog. One substantive freeze worker has a
30-second startup-inclusive deadline, one thread per numerical library, and
process-tree RSS at most 5 GiB. A small guardian keeps the worker owned and records
final child CPU; the watchdog kills its group if the actual supervisor dies.
Sampling targets 0.20 seconds, rejects gaps above 0.25, and checks pressure at most
one second apart. Failed/incomplete monitors stop work; >5 GiB or <10% free memory
for five seconds stops work. All observed owned groups receive TERM/KILL cleanup.
The guardian exit must be observed by 30 seconds; 32.5 seconds is the outer
allocation/cleanup limit, never a fresh work budget.

The exclusive fsynced `attempt.json` binds command, carried charge, checked source
inventory, explicit inputs, wrapper/helpers/protocols, prior check receipts and
native-library bytes. Those hashes are compared before/after the worker; no source
edits are permitted during execution. Worker stdout/stderr and fsynced resource
samples are retained. A malformed/missing final CPU record is charged the elapsed
allocation; otherwise the charge conservatively takes the maximum of allocation,
sampled tree CPU, reaped child CPU and final worker CPU. Supervisor CPU, including
preparation and verification, is added separately. Input validation failures get
a nonpassing terminal receipt too; unresolved prior accounting blocks advancement.

## Receipt and native-launch gate

`ATTEMPT_DIRECTORY/supervisor.json` is an exclusive, fsynced terminal receipt with
`phase=recovery_fixture_freeze`, `lock_sha256`, `passed`, `failure`,
`monitor_failure`, `source_changes`, `elapsed_allocation_s`, `charged_cpu_s`,
`supervisor_cpu_s`, `cumulative_qualification_charge_s`,
`sampled_peak_rss_bytes`, and `termination.owned_pgids/surviving_pgids`. It also
binds the attempt hash and output hashes. Passing requires return code zero,
unchanged sources, a valid resulting checked source/fixture lock, timely guardian
exit, elapsed allocation ≤32.5 seconds, healthy monitors and no surviving group.
It matches the unchanged runner's `freeze_accounting` contract. Only the parent
may pass this receipt to the deferred native `run` after all prospective gates hold.
A failed or missing receipt cannot authorize native work.

The explicit phase-0 GRB library metadata is:

- `/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages/gurobipy/_batch.cpython-312-darwin.so`
- SHA256 `54c2ca41a9a9c80b4dd27df09e6b8a73abbb18de90e95198ae676611910dca96`

Hashing these bytes does not import or call the backend. The parent supplied the
path/hash from phase-0 runtime evidence.

## Parent command shape — not executed here

```sh
.venv-local/bin/python research-20261023/run_recovery_freeze.py \
  --attempt-dir research-20261023/recovery-phase1-v1/freeze-attempt01 \
  --command-json research-20261023/recovery-phase1-v1/freeze-command.json \
  --lock research-20261023/recovery-phase1-v1/lock.json \
  --checks research-20261023/runner-checks/attempt02 \
  --accounting research-20261023/recovery-phase1-v1/input-accounting.json \
  --protocol research-20261023/RECOVERY_PHASE1_LAUNCH_PROTOCOL.md
```

A passing receipt would be at
`research-20261023/recovery-phase1-v1/freeze-attempt01/supervisor.json`. This file
records no generation result and does not claim native qualification.
