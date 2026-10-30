# Independent native hull V2 preflight

27 September 2026. **Ready for a distinct frozen V2 eight-cell qualification.**
No native optimizer was imported or executed by this reviewer; no author source,
protocol or raw evidence was edited. The failed first attempt remains two
certified cells, four master-cap failures and two blocked dependencies. Its
independent audit is preserved under `result/native_hull/20260927-attempt1/review/`.
This review does not reinterpret any of those outcomes or claim V2 has run.

## Scope and mathematical assessment

V2 replaces repeated native LP tangent refinement within a fixed pool with one
ordinary LP followed by bounded exact pairwise simplex improvement. The complete
fleet feasible set, native pricing dependency, eight case/market/target/dependency
definitions, original native budgets and both certificate tolerances are
unchanged. Result/column schema and state identities are intentionally versioned.
No archived V1 pool is implicitly admitted to the new schema.

For stored complete-fleet projections `(e_j,c_j)`, let the current weights be an
exact nonnegative unit simplex. The objective is
`Q(w)=sum_j w_j c_j+F(sum_j w_j e_j)`. With exact stored-number gradient h,
column scores are `s_j=c_j+h*e_j`. Choose a minimum-score toward column i and a
maximum-score strictly positive-weight away column j, with deterministic smallest
index tie breaking. If `d=s_j-s_i>0`, transfer gamma from j to i. Curvature along
that line is `H=sum_t b_t(e_it-e_jt)^2>=0`, and

`Q(new)=Q(old)-gamma*d+H*gamma^2/2`.

The implemented `gamma=min(w_j,d/H)` for H>0 and `gamma=w_j` for H=0 is the exact
minimum on that feasible line segment. It preserves every other exact weight,
nonnegativity and unit mass, and strictly improves the objective. Selecting an
away column with zero weight is excluded. The source verifies the exact
objective equation and strict decrease after reconstructing and physically
replaying the whole columns. Exact rational weights remain authoritative even
when a displayed float load underflows to zero; no positive mass is discarded
through a float round trip.

This is a feasible improvement argument, not finite-step exact solution of every
possible pool. After each step, the restricted-pool certificate still uses the
**actual serialized floating gradient** and its exact conjugate arithmetic.
Only `g_pool<=1e-6` admits a new global pricing call. The final hull certificate
still requires a fresh admitted native global pricing lower bound and exact
stored-number width `<=1e-4`. A small nonlinear objective error, stationary
unrounded gradient or completed step count does not replace either condition.
Exact stationarity/repetition with an open serialized-price gap yields
`stalled_bounded`; resource exhaustion yields `budget_exhausted`.

Every raw master mixture and accepted polished mixture now updates the current
state's best feasible upper bound immediately. Thus an inner failure retains
improvements already logged, addressing the first attempt's lost-summary-upper
bound behavior. A retained upper bound alone cannot promote a failed state to
certified. Existing whole-fleet replay, native status/bound admission, physical
roundoff policy, actual-price Fenchel formula and failed-predecessor admission
remain dependencies of the unchanged global proof.

## Fixed resources and repaired preflight findings

The three added per-state limits are 256 accepted transfers, 8,192 bits per
checked rational numerator/denominator and five cumulative seconds of polishing,
also limited by the remaining 60-second state deadline. Original master/pricing
caps, one thread, native phase caps, worker cap and outer process-group cap remain
unchanged. One native LP is used per current pool; duplicate tangent points are
logged but not appended to force another identical LP solve. No cap increase,
solver retuning, known analytical seed or target-specific two-column shortcut is
introduced.

Two issues were independently reproduced and repaired **before** this V2
preflight disposition:

1. The first V2 candidate checked the polishing deadline only at loop entry.
   A slow pool check/logging step could finish after the limit and still return
   qualified. An independent pure fake-clock example returned qualified after
   seven seconds with a five-second budget. The repaired source rechecks the
   deadline after the pool calculation and its logging, before accepting the
   pool criterion. The same example now raises the declared budget failure and
   preserves already streamed feasible upper bounds. Time limits are cooperative
   between bounded arithmetic/logging operations; the separate worker/outer
   process limits remain the external termination mechanism.
2. The first V2 accounting candidate compared only aggregate step/check totals
   across polishing phases. A fabricated step for nonexistent phase 999 could
   be counted against phase 0. The repaired accounting follows the active phase,
   start cumulative-step value, permitted check/step order, unique sequential
   cumulative step identifiers, per-phase completed counts and matching finish.
   Misattributed, duplicated, out-of-order or missing events fail even when
   aggregate totals agree. Failed/malformed predecessor receipts remain blocked.

The source author made these repairs; the reviewer did not edit implementation.
The bounds and physics were unaffected. Every polishing start/check/accepted
step/finish remains recorded with immutable column keys, before/after weights,
exact gradients/scores/direction/curvature/gamma/objectives and elapsed time.

## Independent validation performed

- All **64** pure/fake tests passed with an external import blocker rejecting
  `mip` and `gurobipy`. They include retained dependency failure, LP plateau,
  zero-curvature improvement, exact weights below float range, step/bit/time
  exhaustion, streamed upper bounds, late deadline rejection and six polishing
  phase corruption controls.
- Re-ran the two originally independent fake-clock and nonexistent-phase
  reproducers: both are now rejected.
- Compared all eight complete control manifests with the immutable V1 record,
  excluding only intentionally versioned state identity. Every physical case,
  market, target, dependency and physical/market identity is unchanged. Every
  original Budget field is unchanged; only the three declared polishing limits
  were added.
- Constructed a third physically replayed two-bus column with 5 early kWh and
  combined it with two archived complete-fleet extreme schedules. For **20**
  deterministic distinct positive rational starting simplexes, independently
  minimized every segment of this pool's supporting boundary and compared the
  polished result with that exact reference. All returned within the unchanged
  pool criterion after 2–5 transfers. Every saved step equation, strict decrease,
  exact unit mass and phase accounting check passed. This is a pure mathematical
  control using explicitly supplied feasible columns, not a native experiment
  or a scientific seed.

## Interpretation and execution gate

The exact improvement routine operates on stored numerical projections.
Replaying a tolerance-accepted physical column does not convert it into an exact
ideal-physics witness. Existing numerical feasibility and native global-bound
assumptions remain. No new convergence theorem, empirical speed advantage,
learned-price benefit or operational performance result follows from this
preflight. In particular, the V1 failure stays part of the research record.

Freeze the complete snapshot below, then execute a new attempt and audit its
raw pricing evidence, master mappings, every exact transfer, phase accounting,
imported pools and final bounds independently. A compact path-flow oracle is a
separately qualified formulation; this reviewed V2 snapshot still uses the
original native recharge oracle and does not silently switch pricing backends.

## Reviewed freeze-ready source snapshot

| File | SHA-256 |
|---|---|
| `src/egglab/native_hull.py` | `05daaaea72d6eaba982b1b552720b6781e34a9063a1503ef3ea0b424e364de24` |
| `src/experiments/native_hull_qualification.py` | `4129080d33dd474e4296a02fcc4af5feb18051be814bde016edf3f5450eb8d30` |
| `src/tests/test_native_hull.py` | `9a7c5ab571b35b407d393f03bf38eb6e5f0e8381ee163fead37a3439c7943f32` |
| `doc/NATIVE_HULL_QUALIFICATION_PROTOCOL_20260927.md` | `4a88398af643902ff7a25c0a0008612eae79300a5347c87a9c9dc7d70785bd4a` |
| `doc/NATIVE_HULL_CERTIFICATION_DESIGN_20260927.md` | `690fdbdafe65102a845d4f052f737cf1a9ec938562b360bfa1a06e12f4114a0f` |
| `src/egglab/native_recharge.py` | `0067123a7f71cc6e9c89e1262cdcbd612cafdcfc252e35bcfca7f1f54c45d0f3` |
| `src/experiments/native_recharge_qualification.py` | `200c5bec8e6f8c7f7e466ef045b439dceae9fa2b35984cc452d4d29471dfde1e` |
