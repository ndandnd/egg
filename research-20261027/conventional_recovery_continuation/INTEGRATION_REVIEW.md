# Repaired continuation: focused static integration review

Disposition: **PASS — all three original blockers resolved by targeted static follow-up.**

Follow-up read only the affected LOCAL inventory entries, `run.py:230–251` reuse assertions, and `run.py:540–577` accounting/publication region. The original findings remain below with resolutions; none remains open. No expanded review, old artifact access, execution/import/test/hash/backend call occurred.

Scope: new `PROTOCOL.md`/`FIELD_AUTHORITY.md`, minimal worker/owner/preparer diffs against the frozen pilot, exact fixture text diff, affected new owner regions, and `LAUNCH.json`/`REUSE_BINDINGS.json` control declarations. The fixture diff is empty. The closed binding phase was accepted as CLOSED_PASS and was not rerun or audited. No old master/artifact/bank data, broader physics/source/correspondence review, execution/import/test/hash/backend call, commit, or new agent.

1. **Incorporated original field authority is missing from source inventory.** The new field authority incorporates the original pilot's field-authority contract, and the new protocol explicitly says original protocol/fieldauthority are preparation source inputs. Both `run.py:LOCAL` and `prepare.py:LOCAL` include original `PROTOCOL.md` but omit original `FIELD_AUTHORITY.md`. Add that single literal source-contract path to both inventories so preparation and main source admission bind the incorporated contract.

   **Resolved:** Both LOCAL inventories now include the same literal original `conventional_recovery_pilot/FIELD_AUTHORITY.md` path alongside the original protocol. Preparation and main source admission therefore bind that incorporated contract.

2. **Reuse admission omits the stated value/denominator assertions.** `run.py:admit_reuse` checks source/task/descriptor/flags/pins/cost telemetry but never explicitly checks finite reused `retained_value` or positive finite F `target_common_grid_electricity`. Later ratio construction safely returns null for an invalid value, but that is not the prospective transfer assertion promised by the protocol. Add these narrow metadata assertions to admission of the three reused rows; no extra artifact read or replay is needed.

   **Resolved:** `run.py:240–245` requires each reused retained value and its grid-cost component to be finite and agree within the existing tolerance. F additionally requires a finite positive common grid-electricity denominator and agreement between common/retained value. The assertions use the already decoded transfer metadata without another read or replay.

3. **Explicit cumulative actual-study cost is missing.** New physical package resources, the historical prepublication ledger, and whole-research cumulative prefix are retained separately. However, the readout has no explicit cumulative actual-study total combining the externally closed original 17.34 CPU package (including failed UN) with the current package. The protocol expressly requests cumulative actual campaign cost separately from idealized counterfactual pipelines. Publish that total with clear prepublication/external-closeout scope, using frozen accepted historical charge rather than rereading or re-metering the old attempt. Preserve the failed-UN/overhead ledger and avoid adding reused stage costs to current physical resources.

   **Resolved:** `run.py:547–560` takes a consistent new-package CPU/elapsed snapshot, retains zero new physical charge for reused stages, and publishes separate closed-prior (17.34 CPU / 19.17 elapsed), provisional-current, and combined-actual-study fields. Explicit scope identifies the prior charge as closed, current values as prepublication, and final external parent receipt as authoritative. Whole-research cumulative totals remain separately labeled.

The remaining changed integration is consistent with this continuation:

- Exactly original B62001-N12-F/N/D rows are eligible, against a frozen compact-master byte pin and exact dependency dictionaries. Paths are literal namespace/task constructions. Main preflight transfers only those rows, records reuse, and skips dispatch; worker namespace admission independently denies their three new-namespace tasks.
- Reused dependencies require the original source identity; fresh dependencies require the current source identity. The original physical all-record/selected-fleet admission paths remain intact. UN/UD now import their backend in their own fresh process before model construction.
- Reused successes retain their original provenance and costs, with `attempted_this_run=false`; old failed UN remains separate failure/accounting history. Forty scientific states and existing strict/fallback/paired-denominator semantics remain intact. Current physical CPU excludes reused acquisition charges, while counterfactual pipeline sums include needed historical acquisitions and original/common new preflight once each.
- Source preparation remains source-only, uses the same static sibling import closure, and emits a pending candidate. Main gates require accepted binding/preparation meters, exact reuse contract, frozen source/control, environment, parameters and budgets. The reviewed DRAFT/PENDING control cannot dispatch.

No integration blocker remains from this review. This PASS is static integration only, not runtime qualification or a replacement for the separate source/control freeze. The human authorization covers the separately frozen repaired continuation; this review adds no extra trial, retry, retuning, ML or follow-on authority.
