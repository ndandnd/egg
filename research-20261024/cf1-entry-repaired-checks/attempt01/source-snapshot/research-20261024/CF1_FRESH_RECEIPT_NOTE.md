# CF1 fresh receipt inventory

24 October 2026. Compact inventory of already inspected receipts. This wake is
for ONE design packet only. No numerical execution is cleared by this note.

## Current carry and termination

Authoritative carry is **1527.8351450899538 seconds**, from
`launch-entry-checks/accounting.json`. Its prior charge is
1524.0216024654942 and current charge is 3.813542624459684. Accounting observations
are complete; the source check passed; owned groups are absent and reaped.
Native dispatch and metadata freeze are both false.

`launch-entry-checks/attempt01/result.json` records returncode 0, passed, leader
reaped, group absent, no surviving groups, no cleanup errors, no secondary errors,
and no source changes. Its pre-closure cumulative charge
1527.0851450899538 is reconciled by the accounting file's explicit 0.75 seconds
of source-snapshot and finalization charges. No receipt conflict was found.

## Preserved stopped v4

`../research-20261023/cf1-small-approved-v4/entry-failure.json` records controller
returncode 1, zero worker launches, zero task directories, `owner_exists=false`,
and status `controller_entry_failed_task_undispatched`. The recorded error is
`Missing/corrupt cumulative carry-forward ledger`. No retry occurred and the
mechanism is unqualified. Its `runs` directory contains only `campaign.json` and
`ledger.jsonl`; no active numerical worker or owner is recorded.

## Original fixture and exact task scope

The retained authority is
`../research-20261023/CF1_SMALL_APPROVED_PROTOCOL.md`: exactly CF1, synthetic
base50997/40, seed17, day tariff, no fault, protocol revision4, policy
`cf1-small-approved-v4`. The original recorded task ID is
`bf86cfed6825b5b9f591`.

- Sole fixture: `../research-20261023/recovery-phase1-v7/fixtures/base50997-n40.json`
- Fixture SHA256: `c6eca9f94f1190d9736f6ac3732b6dbd395578e723b7907ff2cee179cbd10429`
- Full case identity: `58b3e0628e6ad1e3876bb142cec2636cb7bc826738da0f6a34f60555954370f8`
- Target market hash: `f1da29dda920210565f103a311f47b5b5f460e3704050ae711966ca852425be2`

The original scope fixes `.venv-local`, Gurobi, one native thread, one worker,
5 GiB, startup-to-deployment60, supervisor61, and outer62.5-second clocks. It
permits no fixture generation or substitution, other task, automatic retry,
comparison screen, training sweep, cluster work, or sealed-data access. Those
historical constraints do not themselves authorize a fresh dispatch.

## Reusable binding references only

Existing wrapper filenames available for design bindings:

- `../research-20261023/run_cf1_small_approved_checks.py`
- `../research-20261023/run_cf1_small_approved_freeze.py`
- `run_launch_accounting_checks.py`
- `run_launch_prefix_checks.py`
- `run_launch_entry_checks.py`

Presence is not new qualification. This note adds no source execution, metadata
freeze, numerical clearance, or new audit.
