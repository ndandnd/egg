# Approved small-mechanism package: controller entry failed

24 October 2026. Source revision `2fa7a6d0`; policy `cf1-small-approved-v4`.
The user approved32 CPU minutes TOTAL for one inspected40-trip CF1 mechanism
check. The package stopped before launching a worker. **No solver result or
mechanism qualification was obtained. No retry was performed.**

## Completed evidence

- One affected source gate:10 tests passed in0.16s; only
  `test_cf1_small_mechanism_approved.py` was executed. Owned group32760 absent and
  leader reaped; no changed sources or unresolved accounting. Historical tests
  were hash dependencies, not rerun. See `cf1-small-approved-checks/attempt01`.
- One metadata freeze passed, owned group32882 absent/reaped. The fresh lock binds
  existing synthetic50997/40, CF1 seed17/day/no fault, task
  `bf86cfed6825b5b9f591`, exact source/environment/library/fixture identities and
  `common-priceblind-top3-exact30-v1` selection policy. No model assets were used.
  See `cf1-small-approved-v4/freeze-attempt01` and `lock.json`.
- The controller invocation exited1 in0.98s whole wall time. Its ledger has zero
  launch/finish events, no task directories and no remaining owner. It failed in
  `resume_state` before the native launch loop. No worker PGID or native capture
  exists. The assigned mechanism task remains undispatched.

## Cause and correction

The parent's prelaunch accounting initialization copied raw freeze charge
`3.1857290000000003`. The existing verifier derives its canonical component as
`cumulative - carried`, giving `3.1857290000000376`. Their difference is
`3.730349362740526e-14` seconds. Exact ledger component comparison rejected the
initialization even though their rounded cumulative totals agree.

This is a bug in the parent's accounting setup, not evidence of infeasible CF1
routes, failed charging, bad predictions or slow optimization. Independent source/
metadata diagnosis is retained in `CF1_SMALL_APPROVED_ENTRY_DIAGNOSIS.md`.
The future initializer must derive the exact same canonical component as the
verifier and reconcile external spend from that canonical total. Do not weaken
the exact identity check or modify this rejected ledger to manufacture a pass.
No corrected numerical invocation was made under this no-retry package.

The new ACK observer passed inert source checks but was never exercised by a live
worker. Its runtime mechanism and transport timing remain unqualified. The old v3
entry points remain disabled; the old80-trip failures retain their interpretation.

## Preserved accounting

All previous failures and conservative charges remain. Authoritative current
account: `cf1-small-approved-v4/accounting.json`.

| Component | Additional charged seconds | Cumulative seconds |
| --- | ---: | ---: |
| Inherited carry | — |1509.9511370494984 |
| Source checks plus positive whole-process reconciliation/closure |2.65 |1512.6011370494984 |
| Metadata freeze plus positive reconciliation/closure |3.8 |1516.4011370494984 |
| Failed controller entry, prelaunch preparation and closure |2.0 |1518.4011370494984 |

Failed entry's internal supervisor CPU0.544004 is included in its1.0-second
whole-process envelope (max wall/CPU plus0.02 precision); the positive difference
0.455996 and two conservative0.5-second preparation/closure charges are retained.
The rejected launch ledger remains unchanged. The final accounting root is the
independent completed freeze account plus the complete failed-entry observations;
it is **not** a claim that `resume_state` accepted that ledger.

Approved TOTAL1920/dispatch1740/shutdown180 and package ceiling1674.9511370494984
were respected. No reserve was redeemed, spending reset or new allowance taken.
The source, check/freezer receipts, failed entry, copied execution-tool stderr and
compact diagnosis are retained; no native stdout/license trace was produced.

No new ML-quality conclusion, comparison, global bound or scientific milestone
was obtained. No Google Doc entry was added for this engineering startup failure.
Next work is a small checked canonical accounting initializer, not a larger solver
or model sweep. A future numerical attempt requires a separately recorded
prospective decision and fresh namespace with this failure and all spend carried.
