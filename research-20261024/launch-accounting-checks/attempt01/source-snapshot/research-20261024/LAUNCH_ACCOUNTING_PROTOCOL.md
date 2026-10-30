# Canonical launch accounting: one affected source check

24 October 2026. Follow-up to the diagnosed controller entry failure, not a native
retry or new qualification campaign. The old v4 source, rejected ledger, lock and
receipts remain unchanged. No model, fixture, capture, pricing or cluster work.

The new pure helper targets `comparison_native_preflight.freeze_accounting`,
whose canonical component is consumed by `recovery_qualification.resume_state`:
`receipt cumulative - lock carried`. It retains the raw receipt charge for audit,
checks exact receipt addition and reconciled funding, and derives any positive
external correction from the canonical base. It does not verify actual receipt
provenance, grant budget or dispatch permission, write a ledger or change consumers.
It does not implement the generic recovery freezer's separate maximum-with-lock-
floor policy.

## Prospective affected check

- Carry **1518.4011370494984 seconds** from
  `research-20261023/cf1-small-approved-v4/accounting.json`, including every earlier
  failed and conservative charge. No new administrative allowance or reset.
- New source-only package: hard20 seconds, absolute end1538.4011370494984. Check
  work10, outer12.5, inclusive15, parent finalization reserve5. This fits below
  both the earlier1620 and current1740 dispatch stops. Current approved ceiling
  remains1920 with180 shutdown reserve; no new numerical authorization follows.
- One single-thread source-check child, 5 GiB maximum monitored RSS. No numerical
  worker. Use `.venv-local`; sole selected test is `test_launch_accounting.py`.
  Historical test matrices are neither imported as helpers nor executed.
- Exclusive namespace `launch-accounting-checks/attempt01` under this directory.
  Freeze the helper/test, driver, reused monitoring/ownership/accounting helpers,
  protocol/review/implementation/wrapper notes and prospective budget/command.
  Review before execution; don't edit bound sources while the check runs.
- The prospective command object binds the absolute Python/driver invocation,
  selected test and expected source hashes (excluding its own digest). The actual
  pytest argv is retained separately in the attempt receipt. Run the wrapper once
  under `/usr/bin/time`; no automatic retry of an incomplete or failed attempt.

Regression checks use handwritten metadata, including the actual floating-point
representations from the diagnosis, exact comparison to the consumer component,
JSON round trip, zero/positive correction, inconsistent/underfunded inputs,
nonfinite values and immutability. They exercise arithmetic, not stored outcomes.
No solver or historical research asset is loaded as a test input. Inherited proof
closure verification may byte-hash already-bound artifacts; that is not research
input parsing, model loading or outcome analysis.

The driver reuses reviewed fail-closed monitoring, process-group registration,
cleanup/reaping and charge helpers. Preserve monitor/ownership/accounting errors,
all spending and changed-source diagnostics. Charge max(elapsed allocation,
sampled tree CPU, reaped child CPU) plus supervisor CPU. Reconcile only positive
whole-process wall/CPU excess with0.02-second output precision, then record actual
or conservative closure within the same20-second package. No passing test grants
native clearance or retroactively repairs the rejected v4 entry.

After the one complete check, update the current accounting root and handoff and
back up using Nathan Cho's requested identity. No Google Doc entry is needed for
routine arithmetic engineering. Return to the substantive comparison/verifier
work; a future numerical run still needs a separate prospective decision and fresh
namespace with this failure and all spend carried.
