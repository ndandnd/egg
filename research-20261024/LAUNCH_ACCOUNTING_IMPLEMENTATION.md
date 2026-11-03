# Pure canonical launch accounting

24 October 2026. Added `src/egglab/launch_accounting.py` and a focused handwritten
test file. No historical ledger, source snapshot, receipt, or exact consumer
comparison was changed. No code, import, test, fixture, model, cluster job, or
native retry was run for this implementation.

`build_launch_accounting` accepts four explicit numeric inputs and returns a
frozen record. It retains `receipt_charged_cpu_s` as diagnostic evidence and
computes `freeze_charge_s` using the exact consumer expression:
`receipt_cumulative_charge_s - carried_charge_s`. It requires the receipt's
cumulative charge to equal carried plus raw receipt charge exactly. Every input
must be a finite, nonnegative Python int/float scalar, excluding booleans.
This targets the comparison-native freezer; the generic recovery freezer's
maximum-with-lock-floor rule is outside this helper's contract.

The caller must supply an independently reconciled total covering both the
canonical base and the raw cumulative receipt. The external correction is that
total minus `(carried_charge_s + freeze_charge_s)`; negative corrections raise
instead of being clamped. The function performs no I/O and confers no launch
authority, evidence normalization, or new budget.

Sources reviewed: `research-20261023/CF1_SMALL_APPROVED_ENTRY_DIAGNOSIS.md`,
`comparison_native_preflight.freeze_accounting`, and
`recovery_qualification.resume_state`. The regression preserves raw charge
`3.1857290000000003` while deriving canonical charge `3.1857290000000376` from
cumulative `1515.7868660494985` minus carry `1512.6011370494984`. Tests cover
exact consumer equality after JSON round trip, zero and positive reconciliation,
invalid/inconsistent/underfunded inputs, input preservation, and record freezing.

This implementation does not establish CF1 mechanics. The V4 entry stopped
before worker launch and retains its no-retry status. All further source-check
spend remains charged from `1518.4011370494984` under the existing 32-minute cap;
this helper does not reset that accounting.
