# Primitive-to-freeze accounting: static phase-input review

25 October2026. Note only: no qualified module/test/receipt edits, import,
hash audit, test, primitive, freeze or numerical execution.

Source attempt01 passed45 tests/75 subtests; PGID27953 was reaped/absent and
sources unchanged. The parent-reconciled source account is
`cf1-responsive-checks/attempt01-accounting.json`, total
S=2546.091499549272, source-phase spend4.26717816695s. Source30 is the ORIGINAL
allowance, not a fresh30s allowance after another phase.

## Actual consumers and the dependency

`cf1_responsive_supervision.freeze(args)` currently requires exactly the source
account path above. It therefore rejects a completed primitive account supplied
through the CLI. Passing the source account instead leaves lock.carried_charge_s
at S even though the primitive has subsequently consumed resources.

The underlying existing `comparison_native_preflight.freeze` is different:
it calls `q.accounting(args.accounting)`, requires total>=the checked-source
receipt total and package start, and writes that supplied total into
lock.carried_charge_s. It also binds the actual account file hash in
lock.prior_accounting_sha256/evidence and carries its evidence inventory.
`q.accounting` checks a finite cumulative minimum, the retained coordinator
proof and evidence hashes; it does NOT itself require a completed primitive,
policy/phase flags or a direct link to the current source pass. Those checks
must be explicit at the phase boundary.

## Preferred smallest contract: current account, unchanged production bytes

After a genuinely passing, closed primitive, let P be the driver's authoritative
immutable account. Choose its exact path once; do not modify/alias the source
account. Require P to link the exact source account/result/attempt01 command and
qualified production/test inventory, and to bind the actual primitive command,
driver, result, resource/ownership/cleanup receipts and reconciliation inputs.
Require the primitive's tested component hashes to match the still-current
qualified bytes. Historical incomplete-observation flags remain false/unknown;
fresh complete flags describe only the newly closed primitive.

The boundary validates policyv6, the actual primitive phase, passed=true,
native_dispatch=false, metadata_freeze=false, complete fresh observations,
closed/reaped owned groups, finite nonnegative current charge, exact
P.prior_charge_s=S and P.charged_cpu_s=P.prior_charge_s+P.current_charge_s.
Limits remain3600/3420/180, package600/end3026.723449631016. Independently fund
P.total +metadata25 +entry65 +native62.5 +supervision120 +final45 before freeze.
Do not rely on the adapter's narrower internal10s planning check for this full
reservation.

Use a NEW, reviewed binding-only research driver which enters the existing
`revision6()` and calls the existing `adapter.freeze(args)` directly, with
args.accounting=P. Reproduce the qualified wrapper's exact lock/design/check
path restrictions and replace only its phase-account restriction with the
explicit P contract above. Keep checks=source attempt01. The future frozen
command must name this driver, not the unchanged module's rejecting freeze CLI.
Bind the new driver's exact bytes and all actual arguments in the metered phase
manifest, including the driver hash in design.evidence so the actual freezer
carries it into lock.evidence. Keep raw receipt.source_hashes equal to
lock.sources as the existing consumer requires; extra driver/evidence bindings
do not replace that production inventory. Source01 and the primitive do not retrospectively qualify that new
driver. Parent must explicitly review this narrow phase-binding adaptation.

This preserves the passing production/test bytes and primitive eligibility,
uses the actual current carry, and needs no production-source identity churn.
It is an existing adapter API call with stricter phase inputs, not a replacement
freezer or a waiver of source/asset/environment/fixture verification. Do not
introduce a dynamic monkeypatch or weaken the qualified module's path guard.

The resulting lock carries P.total. Raw metadata receipt cumulative must equal
P.total+raw_metadata_charge exactly. The separate postfreeze account must have
prior_charge_s=P.total and current_charge_s=ONLY metadata's own internal charge,
positive external reconciliation/preparation and closure. Its cumulative is
that exact sum and its phase is metadata_freeze with hard_total_ceiling_s3600.
Existing `build_launch_accounting` retains canonical raw freeze charge and
separately appends any external correction. Primitive spending is already in
the lock's prior; it is never renamed metadata CPU or added again as correction.

## Alternatives and qualification implications

Keeping the old source-account input could be mathematically reconciled by an
outer guard and separately labelled primitive correction in the canonical
launch prefix. However, the lock/freezer would use a stale baseline, internal
funding would omit the primitive, and a metadata-phase current_charge field
would contain an earlier phase. This is less clean and not the preferred path.
Editing the immutable source account, using an alias, dropping the primitive
cost or calling it metadata CPU are unacceptable.

If parent instead requires the production `freeze` entrypoint itself to accept
P, its account-path/phase contract must change. That changes qualified bytes:
preserve source01/P receipts, use a fresh source gate with the affected tests,
and do not claim source01 or P covers the changed file. Any subsequent source
check/preparation cost must also be carried into the ACTUAL final freeze input;
P alone would then be stale. No new policy/native namespace is intrinsically
required merely for this pre-freeze contract change, but source execution
identity and exact hashes must remain truthful.

Any extra affected source validation is charged against remaining original
source30: at most30-4.26717816695, before new source preparation/closure. Preserve
all intervening primitive charges in cumulative carry; track source allowance
consumption separately rather than reset the total or pretend the primitive
was source work. Parent must record the applicable absolute cumulative caps and
remaining reservations before that gate. No validation is requested here.

Needed narrow checks for the chosen driver: a closed linked P is passed to the
actual adapter unchanged; stale S, mismatched source/component proofs, failed/
incomplete primitive and inconsistent sums are rejected before freeze. A small
consumer fixture should establish lock prior=P.total and postfreeze prior plus
metadata-only delta, including nonzero external metadata correction, with no
double primitive charge. These are phase-binding tests, not a historical matrix
or a native retry. A failed/pending primitive clears no metadata phase.
