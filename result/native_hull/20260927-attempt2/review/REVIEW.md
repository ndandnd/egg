# Independent review of native hull attempt 2

**PASS:** all eight prospectively fixed V2 states have independently reconstructed numerical certificates at the unchanged 1e-4 width criterion. The raw archive remains unchanged: 62 files, 905,863 bytes; original manifest SHA-256 `e1d8c201516d7a0be3edcfc866e92bab475d5daba918b80e9570631e96717e36`. Scientific source is frozen at `186c9876805d5096632786c5504f507847a5201f`, regardless of subsequent working-tree changes.

This review did not author the algorithm, import author modules, instantiate a native model, or execute an optimizer. It uses only the Python standard library and the included independently written arithmetic/physical-audit helpers. Every frozen dependency is checked against Git object bytes, all raw files are checked before and after, and the report is derived evidence under this separate review manifest. The unsuccessful first attempt remains unsuccessful: two certificates, four master-cap failures and two blocked successors. V2 does not retrospectively reclassify it.

## Reconstructed evidence

The audit checks all 36 returned native calls: 21 complete-fleet pricing calls and 15 LP masters. It reconstructs 798 raw pricing variable values and 147 raw LP variable values, all semantic mappings and physical constraints, 21 witnesses with 45 charging sessions and 171 SOC events. The raw backend records identify the frozen CBC backend; no fallback is inferred from status labels alone. All returns in this attempt were OPTIMAL.

All 21 global linear pricing minima are independently reconstructed from the complete two-trip physical branches. All 15 restricted PWL LP minima are independently reconstructed, including the three-column masters. All nine accepted exact rational transfers, 24 pool checks and 15 polishing phase lifecycles are checked for their weights, deterministic pair choice, exact line minimizer, objective decrease, serialized-price pool certificate, bit count and cumulative fixed caps. Every raw and accepted polished feasible upper is included when reconstructing the streamed minimum. All fresh Fenchel lower bounds and final best-bound provenance are checked.

| State | Known hull value, displayed | Pricing calls | LP masters | Exact transfers | Saved exact width, displayed |
|---|---:|---:|---:|---:|---:|
| nominal_cold_s0 | 94.8875 | 3 | 2 | 1 | 1.0000000826959621e-6 |
| nominal_cold_s1 | 96.1875 | 3 | 2 | 1 | 1.0000000933985120e-6 |
| nominal_cold_s2 | 94.8875 | 3 | 2 | 1 | 1.0000000826959621e-6 |
| nominal_retained_s0 | 94.8875 | 3 | 2 | 1 | 1.0000000826959621e-6 |
| nominal_retained_s1 | 96.1875 | 1 | 1 | 1 | 9.9999997110744590e-7 |
| nominal_retained_s2 | 94.8875 | 1 | 1 | 1 | 9.9999997682731500e-7 |
| joint_cold | 103.45952216066482 | 4 | 3 | 2 | 1.0000000893970261e-6 |
| fixed_reserve_cold | 99 | 3 | 2 | 1 | 9.9999997971167430e-7 |

Exact binary-rational endpoints, widths, weights, complete-hull supporting prices, reference minima and every transfer are retained in `audit-result.json`; the table displays them as floats. The exact width range displays as **9.999999711074459e-7 to 1.000000093398512e-6**. Maximum rational numerator/denominator size encountered is 322 bits, below the frozen 8,192-bit cap. The individual observed time/count/step budgets pass; the source's wall-clock records are checked for consistency, not independently authenticated elapsed-time measurements.

Retained states 1 and 2 import the full immediately preceding certified retained pool, with identical physical identity, policy, witnesses and ordered projections. The predecessor exit, non-timeout status and complete nonzero native accounting are rechecked. New state bounds, prices, weights and tangent history are fresh. Both retained transitions use one fresh pricing call and one LP master. This small deterministic fixture shows correct reuse; it is not a runtime scaling or general speedup study.

## Why the analytical checks are complete here

These frozen cases have exactly two compulsory 15-kWh services and no travel-energy/cost contribution. Every complete used-fleet schedule either joins the services on one bus or uses two buses. Writing efficiency as eta, total replenishment is T=30/eta. Early grid energy x has upper bound min(early capacity,15/eta). The two-bus branch has lower bound max(0,T-late capacity). The one-bus branch also requires x >= (30+reserve-B)/eta. Empty intervals are excluded. The lower bound is derived from the SOC before/after the second service, not from sampled charging values.

For every branch point, the early opportunity belongs to the A-service bus; both individual late deficits are nonnegative. Their total fits the finite late connector capacity, so a serial terminal schedule exists. Full terminal replenishment, per-bus SOC/reserve, common opening/deadline and one-connector limits therefore suffice throughout each interval. The direct one-bus path cannot avoid the same battery balance. These cases contain no other complete path-cover structure. Hence linear pricing minimizes at branch endpoints, and the full projected hull is the convex hull of those endpoints. The nonlinear objective minimizes on its lower piecewise-linear boundary in (early energy, intrinsic cost), so checking all endpoint pairs and exact one-dimensional stationary points is complete. The independently derived supporting-price minimum minus conjugate equals the full-hull objective exactly for the binary-stored coefficients.

A saved native column can differ from that ideal projection by the qualified floating witness tolerance. For the **saved restricted master**, the three raw columns are therefore not assumed collinear. The auditor eliminates the third simplex weight and independently enumerates all feasible active vertices of the exact four-variable LP (two weights and early/late epigraphs); the other epigraphs are identically zero. This is a complete LP reference, not an integer grid or a pair-only shortcut. The restricted true quadratic reference also checks the interior stationary point in two simplex coordinates and every boundary pair; convexity makes this complete, including singular cases whose minimum is attained on a boundary.

For each polishing step the reviewer independently obtains exact scores c_j+gradient(F)·e_j, the frozen deterministic entering/leaving indices, positive directional decrease d and curvature H. It reconstructs gamma=min(leaving weight,d/H), or the full leaving weight when H=0, and verifies new objective = old objective - gamma*d + H*gamma²/2 with strict decrease and exact nonnegative unit simplex mass. Acceptance still uses the actual serialized float prices and their exact nonnegative-domain conjugate; exact gradient stationarity alone is not a substitute for the saved pool/global gates.

## Numerical scope and residuals

No physical witness is repaired or rationalized to an ideal schedule. All original floating session endpoints/energies remain as saved. The independently replayed physical policy retains the source's 1e-6 energy/objective and 1e-7 time tolerances, the fleet 1e-8-kWh normalization budget and explicit raw-to-session correction ledger. Fraction arithmetic means exact arithmetic on stored binary numbers, not an exact-arithmetic physical optimizer.

Maximum reconstructed raw pricing constraint residual is 2.1316282072803006e-14; maximum raw LP constraint residual is 2.948810786195187e-14. These residuals combine constraints with different units and are diagnostic maxima, not a single physical error metric. Maximum discrepancy between native PWL objective and the exact restricted LP optimum is 5.024343514336531e-14. Maximum combined negative-charge correction plus positive materialized-session capacity excess is 1.5661892642874546e-14 kWh. No correction tolerance is enlarged.

Some saved retained-state feasible objective projections lie a few 1e-14 below the ideal analytical optimum because their physical witnesses are accepted under the existing floating tolerance policy. The analytical target comparison explicitly uses 1e-10 as a comparison allowance; this is not a new physical admission tolerance and does not modify evidence or final width. The final certificate is therefore a **solver-conditioned, tolerance-conditional numerical enclosure**. The exact ideal cyclic theorem and exact stored-number accounting are distinct claims. This audit does not prove a general native solver lower-bound theorem or an operational-data result.

## Adversarial checks and reproduction

The auditor rejects 31 in-memory evidence corruptions, including raw weights/mappings, objective/bound/backend changes, tangent changes, SOC changes, false pool/global certificates, altered transfer gamma/direction/weights/quadratic identities, wrong phase IDs, duplicated step IDs, over-deadline checks, bit/count corruption and failed/incomplete/stale retained dependencies. The controls never modify raw files. Two output-safety controls also reject an existing external report and a repository documentation path without changing either.

Run from any working directory, replacing the checkout path and choosing a new output outside every repository:

```sh
python3 -B /path/to/egg/result/native_hull/20260927-attempt2/review/audit_native_hull_v2.py \
  --attempt /path/to/egg/result/native_hull/20260927-attempt2 \
  --repository /path/to/egg \
  --out /tmp/egg-native-hull-v2-new-audit.json
```

The checkout must retain frozen commit `186c9876805d5096632786c5504f507847a5201f` for source-identity verification; current working-tree source is not imported. A portable run from `/private/tmp` passed with 31 corruptions rejected in about 0.32 seconds. The CLI refuses any output inside a detected Git repository, symlink output, or existing output file. It writes no raw evidence and instantiates no solver. This review folder's separate `MANIFEST.json` covers the four independent audit scripts, report and review text, excluding itself.
