# Independent implementation preflight: compact orphan-charge projection

27 September 2026. **PASS for the scoped compact attempt-3 implementation
preflight after the fixes below.** The initial review of frozen candidate
`b2a5a33f8f3b8eeee09b9b1fc667e63e2ad971c3` found missing failure-ledger and
control coverage. The author repaired those items in the reviewed working-tree
revision. The expanded pure suite passes 115 tests across
`test_native_pathflow.py`, `test_native_pathflow_energy_band.py`,
`test_native_pathflow_hull.py`, and `test_native_recharge.py`. No source code
was edited by the reviewer and no optimizer was run.

The central load and objective bookkeeping is now sound by inspection. The
code distinguishes native load `L`, raw charge sums `R`, materialized plan
load `H`, and replay load `T`; it budgets `L-R`, `H-P`, and `T-H` separately.
Linear pricing reconstructs the native objective at `L` and applies the exact
stored-number correction `price · (T-L)` before bound admission. The planner
evaluates both its raw tangent/true objectives and replayed tangent/true
objectives, and retains the solver lower endpoint while forming the feasible
upper endpoint from replay. The native matrix remains identified as V2 while
the extractor/formulation is versioned V3.

The initial failure-path defect is resolved. The compact extractor now
normalizes negative values locally without changing the shared indexed helper,
computes both `N` and positive orphan `O`, emits the combined ledger, and then
rejects over-budget candidates. A pure test with `N > 1e-8 kWh` and `O > 0`
checks rejection and retained load/projection evidence.

The previously missing pure controls are now present: `I` and `J` each below
the ceiling but over it together, nonzero `H-P` and `T-H` residuals in the
exact total, nonzero planner tangent/true-cost deltas, and a known charge key
with an unavailable interval visit. Attempt-2 control definitions, targets,
and the full CBC budget compare equal to attempt 3's definitions. The energy
band test now explicitly asserts `pq.TARGET_TOL == energy_v2['target_tolerance']`,
closing the top-level target-tolerance equality check.

The direct frozen-input equality check now compares serialized attempt-3
controls and all targets against attempt 2 and confirms the full CBC budget,
including backend. The attempt-2 frozen-file fingerprint at review was
`185e32e2eb2d7504cb2ac93286de1c816337f9726d942837cea898d4d6b0cd91`. Source
freeze and prospective execution remain separate manager-owned steps. The
attempt-3 `SOURCES` now includes this implementation review, so it will be
covered by the frozen source hash set.

Compact-hull integration is outside this PASS and must be repaired before any
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
| `src/egglab/native_pathflow.py` | `9b8f5017b5a5cded27ff3d23b047ecb40b5994dc83b75df7d50add96d4dc9682` |
| `src/tests/test_native_pathflow.py` | `224fdfa4edc0c3293ce9eabf45609c99be0794062b339838e8039d74125cdf33` |
| `src/tests/test_native_pathflow_energy_band.py` | `63ec41b04545dd760bf5b049e4b51803441abb91980a2404ab35a66de98791e2` |
| `src/tests/test_native_pathflow_hull.py` | `803b8f5b01936f3fb52a597464db9a07f050bf51566481293c3e627d569318c2` |
| `src/experiments/native_pathflow_qualification.py` | `09bf4effcd31adab056ecd9d935436e0e26307bbdb129533d0fedc28b892c9ec` |
| `doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_REPAIR_DESIGN_20260927.md` | `7979ad3f805a60a36b8bb38740b219238b73867b2cf8e398f05a055a515311de` |
| `doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_REPAIR_REVIEW_20260927.md` | `6cd0069b74c2006b138727a7c3817d7ba172539c7163a3d2b08dd68a1684693c` |
| `doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_QUALIFICATION_PROTOCOL_20260927.md` | `7c1e33bae849dbde8ae0f2236708ec52e5d6f8ae8b6df2ebdf57c71b083133c9` |

No optimizer was run. This preflight admits the reviewed compact attempt-3
source for manager-owned source freezing; it does not upgrade the failed 19/20
attempt or qualify compact-hull use.
