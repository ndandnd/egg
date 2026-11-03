# Focused static integration review

Disposition: **PASS — both original blockers resolved by targeted static follow-up.**

Follow-up read only the affected `run.py:228–267`, `worker.py:319–337`, and `OWNER_NOTE.md` clock clarification. The original findings are preserved below as the review record; neither remains open. No broader repeat review or execution/import/hash/test occurred.

Reviewed current `PROTOCOL.md`, `FIELD_AUTHORITY.md`, `worker.py`, `run.py`, `prepare.py`, literal launch controls, fixture API source, and only needed original bootstrap/admission/fleet/value/bank-builder/runner/network API excerpts. No execution, import, compilation, test, hash computation, generated input, old outcome, native call, commit, or additional agent.

1. **Pipeline stage clocks exclude final per-stage external receipt I/O.** In `run.py`, `run_worker` records `stage_elapsed_s` and `parent_cpu_s` before `save(folder/'external-receipt.json',row)`. Counterfactual pipeline sums consume those earlier values. Consequently that serialization/flush/fsync is paid by physical campaign resources but omitted from both counterfactual pipeline costs. The protocol explicitly includes serialization in inclusive stage clocks. Finish this paid stage I/O before the authoritative parent stage deltas are captured, or explicitly attribute the residual exactly once to the relevant pipeline. Avoid a recursive requirement that a receipt measure its own final write; the owner/master row can hold the authoritative completed-stage deltas.

   **Resolved:** `run.py:262–267` saves one explicitly marked prepublication external snapshot, then updates the in-memory master row's CPU/elapsed deltas after that save. Those completed-stage values feed pipeline accounting. `parent_elapsed_s` remains the endpoint-admission clock through packet reading; `OWNER_NOTE.md:15` states the distinction and preserves the endpoint ceiling. No recursive second receipt write is added.

2. **Combined union witness counts are absent.** `worker.py` admits and retains both complete producer banks without deduplication, but its union branch never fills the initialized `bank_raw_columns` / `bank_unique_physical_witnesses` fields. The compact cells therefore publish null union counts. Per-origin `banks` counts survive in the nested packets, but summing their unique counts does not give the number of unique physical witnesses across the union. Compute combined raw count and combined witness-key cardinality from the already admitted union entries during this paid phase, keeping every entry and original origin/index.

   **Resolved:** `worker.py:329–330` records `len(entries)` and the cross-origin physical witness-key cardinality immediately after both complete banks are admitted. The entry list, origin/index identities, and subsequent canonical common-member matching remain intact; the set is used only for the reported unique count.

The checked integration otherwise supports the proposed experiment:

- Helper rebinding changes fixture lookup only; original runner, projector, builder, physical realization/validation and fixed-duty candidate filters remain referenced APIs. Local and reachable sibling source inventories align between preparation and owner preflight; loaded sibling paths are checked against that inventory.
- Source-shape prices, nonuniform station power, original SOC/grid/realized terminal checks, fixed-duty ordering and bus/session costs are consistently bound. Union station adders reproduce the original posted grid-electricity objective; both physical terminal inventories are independently screened at 160.
- Strict fresh delivery remains distinct from retaining F; cheaper/tied F can be retained after strict fresh delivery. F can protect N/D without an available full bank. Whole-bank qualification precedes endpoint handling, so normal complete NoSelection banks can reach joint recovery. Union consumers re-admit complete exact pinned buffers without dropping or deduplicating records.
- D final-bank authority is limited to timely normal return and its own final journal admission/hash pass; the source's initial pre-dive digest is preserved separately. Interrupted/nonreturning D cannot acquire that authority.
- All 40 planned states and eight planned pairs remain present; denominators use each cell's own positive F grid-electricity component, with no available-only mean. Preparation is adopted once; owner self/children totals are not augmented by overlapping task telemetry. Unresolved child, fatal identity/record and resource conditions stop onward work.

This PASS covers static integration and the two targeted repairs. It is not runtime qualification, source-freeze approval, or permission to leave DRAFT/PENDING. No integration blocker remains from this review.
