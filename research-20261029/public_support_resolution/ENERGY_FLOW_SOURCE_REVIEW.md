# Energy-flow builder and exact dual checker: independent source review

29 October 2026. Read `energy_flow.py` and `exact_dual.py` against `ENERGY_FLOW_FORMULATION.md` and `EXACT_DUAL_CERTIFICATE_PLAN.md`, plus the needed native timestamp definition. Source-only: no imports, execution, tests, hashes, actual data, native solver, edits to implementation or commits.

## Decision

**Scoped source PASS; no mathematical coefficient/sign defect found in the intended single-connector homogeneous case.** The exact checker reconstructs semantic rows independently rather than trusting the exported matrix. Its residual-box certificate has the correct signs and tangent convention. This is not runtime qualification, provenance admission, a physical-witness check or evidence of a useful lower bound. The future qualification remains necessary.

Two explicit interface limitations deserve attention: linear-price authority is supplied by the result object rather than an independent argument, and native no-optimize outcomes do not use the probe's explicit unavailable-status convention. Neither invalidates an exact accepted bound as currently labeled, but downstream reporting must respect their scope.

## Physical formulation and integer equivalence

- Every original movement receives a selection variable with [0,1] bounds, binary in integer mode. Coverage rows require one incoming and outgoing movement per mandatory service; fleet-start/end balance and the full vehicle cap remain. Positive service duration and validated internal movement chronology imply a DAG, so disconnected selected cycles cannot bypass path interpretation.
- Every movement state has finite [0,B] bounds and perspective reserve/headroom rows. Pullout entry is exactly B*y. Each individual leg subtracts its original exact stored energy times selection; no floating aggregate movement energy is inserted into the exact ledger.
- Depot charging is inserted immediately before the leg indexed by `depot_split`, after all inbound legs and before all outbound legs. Its conservation sign is departure−arrival−eta×charge=0. Terminal charging occurs after the last pull-in leg and terminal state equals B*y. Thus full replenishment holds per used path rather than only in aggregate.
- Service conservation is incoming exit inventory minus outgoing entry inventory=mandatory service energy. The RHS is unconditional, correctly avoiding multiplication by an individual arc choice. At integer coverage exactly one state from each side is active.
- Charge allocations exist only for eligible windows/positive exact resource capacity. Their bounds and selection links cap them by cap*y; the shared interval row counts each allocation once. Market load sums those allocations. The load box is the sum of shared capacities in the period, not that sum multiplied by available visits.
- The source compiler supplies interval identities, but the builder recomputes resource capacities in rational arithmetic. The checker independently reconstructs boundaries/windows and compares interval semantics. This addresses a potentially dangerous rounded-capacity seam. Serialization/inventory realizability still relies on the declared single connector, no taper/switching/parked draw and homogeneous acceptance assumptions.

The exact-ledger integer model therefore implements the written equivalence argument. Its rounded native conversion can differ slightly from that exact model; the implementation appropriately calls native results diagnostic rather than exact physical proof.

## Exact semantic reconstruction

`exact_dual._case` validates the full schema, numeric stored-input types, half-minute source lattice, unique services/movements, resources spanning the horizon, endpoints, chronological legs, depot split and graph reachability. Its lattice agrees with the native source predicate. The case descriptor remains externally admitted authority; internal validation cannot authenticate a changed input case.

`_reconstruct` independently generates variables, exact finite boxes, per-leg/depot/fullness equations, service/coverage/fleet rows, charge selection/shared capacity, load aggregation and operations. It does not import the builder/compiler. Ledger variable names/indexes/bounds/types, all rows, intervals, operations and objective are checked against that reconstruction. Reordering row proposals cannot produce a false bound: any sign-valid multipliers on the reconstructed rows are admissible, although arbitrary remapping can weaken it.

Requiring exported `kind='C'` correctly scopes acceptance to continuous energy-flow results. A binary ledger cannot masquerade as the certified relaxation. Duplicate coefficient terms are algebraically aggregated; acceptance of canceling/repeated entries is safe because the canonical semantic row must still match exactly.

## Objective and dual arithmetic

The MIQP exact market uses Fraction of the original binary floats .2 and1/900, not decimal substitutes. Ledger quadratic terms contain b/2 multiplying the squared variable. The checker reconstructs the same convention. It forms exact tangent slopes a+b*v and constant−Σb*v²/2, adding the original exact operations coefficients. Tangent feasibility is unnecessary; a missing tangent gives the disclosed zero tangent, still a valid but potentially weak lower bound.

For minimization, >= rows project y to nonnegative and <= rows to nonpositive; equality rows retain arbitrary rational multipliers. Residual is c−Aᵀy. The correction chooses the lower bound for a nonnegative residual and the upper bound for a negative residual. Therefore the returned value k+y·rhs+Σmin(residual*l,residual*u) is exact and valid without stationarity or native optimality. Zero entries, zero curvature and signed equality multipliers are handled correctly. Every variable family has finite derived bounds, so no infinity sentinel is relied upon.

The checker validates all intended ledger coefficients before evaluating Pi. Missing Pi returns CERTIFICATE_UNAVAILABLE without a silent zero vector; dimension/sign/numeric issues reject or are explicitly sign-projected. Native status and RC are not proof inputs, correctly. Nonfinite Fraction proposals and malformed common JSON shapes are caught and returned as stage-specific rejection. This is source reasoning only; malformed-control runtime behavior is untested.

## Downstream conditions and small interface caveats

1. **Linear-price authority:** `verify_and_bound(case_dict,result)` takes prices from `result['prices']`. It proves a lower bound for that explicit vector, which is correctly labeled; it cannot independently prove that this vector is the frozen chosen gradient or another externally intended price. The owner/caller must compare the result vector to the admitted target price before using V_lower in a support calculation. A future explicit expected-prices argument would make this boundary clearer.
2. **No-optimize native status:** energy_flow.solve records `optimize_called=False` but still reads raw model Status/SolCount and attempts optional attributes. This is not fabricated optimization success because the call flag is retained and absent Pi cannot certify. Prefer an explicit no-optimize diagnostic outcome/raw_status=None for consistent downstream interpretation, or ensure callers never call it a completed numerical solve solely from packet delivery. No live-model mutation after a solved OA snapshot exists here because there is no OA loop.
3. **Physical upper is separate:** an exact lower bound does not qualify a rounded incumbent. The independent physical replayer must admit the candidate under original exact capacities and use reconstructed exact load/operations when forming an upper bound. Thresholding fractional root selections is not a physical plan.
4. **Native API behavior remains untested:** lazy imports, unavailable QP attributes, Pi/RC extraction, JSON serialization and native model lifecycle require the prospective literal qualification. A missing or failed diagnostic should be preserved without rerun or automatic alternate solver.

For that future qualification, the highest-value controls are wrong row sign/RHS, missing row, changed variable bound, incorrect b/2 convention, tangent constant corruption, both residual endpoint choices, absent/nonfinite Pi, and integer-ledger rejection. These are suggested obligations, not tests performed here.
