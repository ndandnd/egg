# Common selection and CA1 candidate control

24 October 2026. Source-only package: new
`src/egglab/classical_controls.py`. Qualified runner/coordinator, native model,
replay and model assets are unchanged. No runtime import, test, solver, fixture
generation, inference or comparison was executed by the implementation agent.
CF1 is not implemented here. CA1 remains an **unvalidated candidate classical
control**, not an established strong/optimal baseline or feasibility method.

## Interfaces and exact selection

- `select_connections(case, scores)` returns a JSON-ready selection ledger.
- `restrict_case(case, scores)` calls that selector once and returns
  `(restricted_native_case, ledger)`, preserving original movement order and all
  other case fields without mutating the original.
- `ca1_score(case, a, b)` returns original-order integer scores, scalar feature
  rows, flexible-only rank order, tariff hash and policy metadata.

Inputs are validated with the existing pure native-case validator, plus string
ID and finite score/tariff checks. The selector calls the existing frozen
`codex_offline_rank.heuristic`, then orders flexible movements by descending
heuristic score and movement ID. It takes up to three incoming and three
outgoing connections per trip and unions them into the common price-blind B.
Boundary pullout/pullin modes are preserved outside flexible count M.

K is computed as `min(M, max((3*M+9)//10, len(B)))`, the exact integer ceiling
of30% rather than a floating threshold. Each arm fills the remaining slots from
F minus B using its descending scores and movement-ID ties. Returned masks and
retained IDs follow the original case order. M=0 and all-backbone cases are kept
with explicit zero exposure, never replaced. Structural coverage and equal edge
counts do not certify feasibility or equalize search difficulty.

The ledger records original/retained/backbone/fill IDs, mask, M, B count, K,
exposure, full and restricted identities, and hashes of ID lists, mask, scores
and backbone scores. `restricted_identity` and `retained_case_identity` identify
the same filtered case. The apply helper checks that identity before returning.

## CA1 formulas and ledger convention

CA1 implements the frozen `RECOVERY_CLASSICAL_BASELINE_SPEC.md` proxy. It uses
binary64 inputs/operations and `math.fsum` for energy/capacity sums, signed
residuals and cost aggregation. Direct capacity is zero. Depot capacity comes
only from the gap at `depot_split`, intersected with resource and market periods;
connector zero supplies no energy. Capacity is single-vehicle grid kWh, converted
to battery kWh using efficiency. It does not allocate shared fleet contention.

Stress uses the declared direct or pre/post-depot and demand/capacity residuals
against `TAU_KWH=1e-6`; residuals within the closed tolerance band are recorded.
Flags affect rank, never a separate deletion rule or impossibility assertion.
All leg durations contribute to CA1 deadhead minutes, including stationary legs;
the common backbone retains the frozen heuristic's different moving-time rule.

The proportional proxy uses `a*q + b*q*q/2`, without optimizing or clipping demand.
Zero demand costs zero. Positive demand with zero capacity costs zero under the
declared convention but records a distinct capacity-shortfall diagnostic/stress.
Remaining movement energy uses market-duration weights. Rank keys are ascending
`(stress, proxy_cost, -margin, -U, movement_id)`, with ordinary binary64 ordering
after the stress convention. Flexible ranks become descending integer scores;
boundary score0 is explicitly unranked. Nonfinite computed features are rejected.

The scalar ledger records energies, usable battery, window endpoints, grid and
battery capacity totals, demand, margin, stress/borderline residuals, shortfall
and each proxy component. It hashes each period-capacity vector rather than
retaining every vector. Reconstruct it with the frozen case and the accessible
pure `_capacity_by_period` helper. Metadata bind case identity, original movement
IDs, normalized binary64 `a,b` hash and versioned policies. Capacity-vector hash
encoding is canonical compact JSON with sorted keys and nonfinite values forbidden.

Resource/market partitions are merged once. Beyond input validation, scoring is
O(MR + M log M), selection O(M log M), with O(M+R) working storage and scalar
ledger output; R counts combined resource/market slices. The existing native
validator adds its own reachability-validation cost (up to O(NM)). All validation,
imports, backbone construction, hashing, scoring and selection must be inside the
future arm's clock; there is no free cross-arm cached backbone or label.

CA1 proxy values are neither realized fleet energy costs nor admissible bounds.
Its `b` input advantage over current `a`-only learned scorers belongs to a
deployable-method comparison, not matched-information attribution to learning.
Independent full replay/charging feasibility remains a separate future step.

## Qualification status

Module source is held stable for narrow review and the test owner's handwritten
solver-free checks. No check outcome is claimed here. V7's pass does not qualify
this new selector/CA1 or a60-second study interface. Parent owns the single
source-bound check and any later decision; no comparison or native attempt is
created. Carry remains1293.1124853401802s, ADMIN0, with the standing1800/1620/180
ceiling/dispatch/reserve and one-thread5GiB limits.
