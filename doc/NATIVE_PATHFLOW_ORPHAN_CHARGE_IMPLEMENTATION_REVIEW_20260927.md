# Independent implementation preflight: compact orphan-charge projection

27 September 2026. **Preflight blocked pending the correction-ledger fix below.**
Reviewed the frozen candidate at `b2a5a33f8f3b8eeee09b9b1fc667e63e2ad971c3`;
no source changes or native optimization were made. The focused pure suite
passed: 48 tests across `test_native_pathflow.py`,
`test_native_pathflow_energy_band.py`, and `test_native_pathflow_hull.py`.

The central load and objective bookkeeping is now sound by inspection. The
code distinguishes native load `L`, raw charge sums `R`, materialized plan
load `H`, and replay load `T`; it budgets `L-R`, `H-P`, and `T-H` separately.
Linear pricing reconstructs the native objective at `L` and applies the exact
stored-number correction `price · (T-L)` before bound admission. The planner
evaluates both its raw tangent/true objectives and replayed tangent/true
objectives, and retains the solver lower endpoint while forming the feasible
upper endpoint from replay. The native matrix remains identified as V2 while
the extractor/formulation is versioned V3.

There is one required failure-path defect. `_project_charge_energy` calls the
shared `nr.normalize_charge_energy` before computing positive orphan energy
`O` or emitting the combined path-flow projection ledger. That shared helper
raises immediately if negative correction `N` alone exceeds the budget. In
that case the saved incumbent event exists, but the required combined ledger
does not disclose `O`, `L-R`, or the full attempted correction. The design
requires the ledger to be emitted even when the candidate is rejected. Use a
compact-specific normalization pass that records all raw-to-projected
changes, computes `N+O` and the remaining ledger components, emits the full
ledger, and only then enforces the common budget; leave the indexed helper
unchanged. Add a pure test with `N > 1e-8 kWh` and `O > 0` that asserts rejection
and verifies the complete event. Until this is fixed, the prospective attempt-3
preflight is not ready.

The protocol also promises pure controls not present in the changed tests:
separate interval/session excesses `I` and `J` that are each below the budget
but exceed it together; nonzero `H-P` and `T-H` terms exercised in the combined
ledger; and a nonzero projected planner tangent/true-cost delta. The current
planner test follows a zero-correction plan. Add these focused checks alongside
the failure-path test so a passing suite verifies the changed admission and
objective paths, rather than only their no-correction behavior. The current
invalid-key test does not exercise a known key whose movement is unavailable
in its interval, which is also listed in the protocol.

I did not independently compare the proposed attempt-3 frozen manifest,
serialized 20 controls, targets, budgets, and backend against the immutable
attempt-2 `frozen.json`. The current regression test compares definitions to
attempt 1; the protocol's explicit attempt-2 equality check remains pending
before any source freeze or run.

Compact-hull integration is outside attempt 3, but must be repaired before any
compact-hull qualification. `native_hull.py` writes and checks the indexed
`nr.EXTRACTION_POLICY` for stored columns, retained-pool imports, and hull
result metadata. V3 plans carry `native_pathflow.EXTRACTION_POLICY`, so using
the current hull coordinator can label projected witnesses with the old
policy. The changed formulation ID does invalidate prior pricing-oracle state;
that does not correct this separate provenance label. Version the hull
metadata/import checks to carry the explicit extractor identity, test retained
pool rejection across extraction-policy versions, and include
`src/egglab/native_hull.py` in that later hull freeze. The present identity test
demonstrates a V1-to-V3 boundary; add a direct V2-to-V3 identity assertion in
the later hull gate if a V2 state package is available.

Reviewed file fingerprints at this preflight were:

| File | SHA-256 |
|---|---|
| `src/egglab/native_pathflow.py` | `e388b9b063a758f319ef769f508ea459747d783791c8713fcea6598cfb0d19e9` |
| `src/tests/test_native_pathflow.py` | `a2c4aa2277b87eac6f53e8ee55bc51b422c4063f5a021643ce2f237ded05add4` |
| `src/experiments/native_pathflow_qualification.py` | `e297ebb22d1bc79d3c544add95a1bd6f7bae6f40abd79298e564d655f767d09b` |
| `doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_REPAIR_DESIGN_20260927.md` | `7979ad3f805a60a36b8bb38740b219238b73867b2cf8e398f05a055a515311de` |
| `doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_QUALIFICATION_PROTOCOL_20260927.md` | `7c1e33bae849dbde8ae0f2236708ec52e5d6f8ae8b6df2ebdf57c71b083133c9` |

No optimizer was run. This review does not admit attempt 3, upgrade the failed
19/20 attempt, or qualify compact-hull use.
