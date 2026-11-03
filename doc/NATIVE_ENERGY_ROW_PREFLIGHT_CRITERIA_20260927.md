# Independent criteria for aggregate-energy strengthening

27 September 2026. Prospective analytical review only. No optimizer was executed and no scientific source was edited. The unstrengthened compact formulation is `egg-native-pathflow-v1`. A new formulation identity, source freeze and unchanged twenty-control plus eight-hull-control requalification are required before a strengthened version supplies scientific results.

## Intended conservation and why it strengthens the relaxation

Let S be total service battery consumption, E_m the total battery consumption of movement m, z_mk its grid energy, and eta charging efficiency. Every selected path begins and ends with the same full battery. Summing its selected movement and service SOC equations cancels every internal SOC and both boundary inventories. Summing paths gives

`eta * sum(z_mk) = S + sum(E_m * y_m)`.

This is redundant for complete integer path covers in the intended physical model, including multileg movements, partial charging windows, reserve and finite terminal power. Charge belongs to selected modes, so inactive modes contribute zero. It does not require any fractional schedule interpretation. It is generally not redundant for the big-M LP relaxation because partially selected movement equations have slack.

An exact fractional counterexample in the existing nominal cyclic fixture is:

| Quantity | Value |
|---|---:|
| y(out_A), y(in_A) | 1, 1/4 |
| y(out_B), y(in_B) | 1/4, 1 |
| y(depot_AB), y(direct_AB) | 3/8, 3/8 |
| SOC before/after A | 20, 5 |
| SOC before/after B | 17.5, 2.5 |
| Terminal charge owned by in_B | 17.5 kWh |
| Every other charge | 0 |

All old relaxed flow, path-count, service SOC, movement big-M, reserve/battery, charge-ownership, market-link and shared-capacity rows hold exactly; starts=ends=1.25. The aggregate equation requires 30 kWh and excludes this point by 12.5 kWh. A pure preflight test should reconstruct all old rows at this point and then show the new row rejects it. It must not label the fractional point an executable schedule.

## Floating coefficient distinction

An exact physical conservation identity does not imply a bit-identical redundant equality in the implemented native matrix. The existing source computes each E_m with Python `sum` over its legs. A newly flattened sum or replacement by `math.fsum` can change that coefficient. Pullouts precompute `B-E_m`, terminal expressions accumulate `-E_m-B`, and big-M row assembly adds/subtracts the stored M_m. A float scalar containing the sum of service energies can also differ from the exact sum of individually stored service coefficients.

Thus an equality at one rounded RHS is not an exact redundancy proof for all binary-stored inputs. For example, three stored values 0.1 sum exactly as binary rationals to a value different from the single rounded float `sum([.1,.1,.1])`. The discrepancy is `1/36028797018963968`. Replacing `sum` by `fsum` alone cannot remove representability limits.

The recommended two inequalities use a computed, outward-rounded band that covers both the intended per-leg physical model and the existing stored-row integer model. This is an arithmetic enclosure, not a tuned feasibility tolerance. The native normalization, physical replay, numerical bound guard and solver settings remain unchanged.

## Physical and stored-row bands

For the physical band, define exact stored-leg sums `E_m^leg`, the existing rounded movement coefficient `E_m^f`, and `d_m=E_m^leg-E_m^f`. Let `S_exact` be the exact sum of stored service energies. Conservation and `0<=y_m<=1` imply

`S_exact + sum(min(d_m,0)) <= eta*sum(z) - sum(E_m^f*y_m) <= S_exact + sum(max(d_m,0))`.

The sum over all available modes is conservative; a valid path cover selects at most 2N movements, so a selection-count bound can tighten it without solving a matching problem.

For the existing stored native integer rows, write a movement's code residual as `phi+C`, with C its actual stored expression constant and M its actual stored big-M coefficient. The source adds `(phi+C)<=M*(1-y)` and `(phi+C)>=-M*(1-y)`. Under the inspected linear-expression float addition/subtraction semantics, selecting y=1 implies the exact rational residual R=phi+Q(C) lies in

`l = Q(C)+Q(M)-Q(float(C+M))`,

`u = Q(C)-Q(M)-Q(float(C-M))`.

Let D=Q(C)-C_ideal, where the desired constants using the existing E_m^f are `-B+E_m^f` for pullout, `E_m^f` for direct/depot, and `-B-E_m^f` for pullin. The intended residual therefore lies in `[l-D,u-D]`. Reverse that interval's sign for pullin, because its code residual has the opposite telescoping orientation. Service equalities have their original exact stored coefficients. Summing selected residuals gives

`A = S_exact + sum(E_m^f*y_m) - eta*sum(z)`.

At most 2N movements are selected. A safe A_min is the sum of the 2N smallest negative lower endpoints (including zero as the unselected option); A_max is the sum of the 2N largest positive upper endpoints. Hence the aggregate expression lies in `[S_exact-A_max,S_exact-A_min]`. Take the union enclosure with the physical band and round its endpoints outward to finite floats.

This derivation concerns exact binary-stored rows, not the larger set accepted under a native solver's feasibility tolerance. No claim that every numerically tolerated old incumbent satisfies the new band to zero residual is made. Qualification and independent replay must retain their original numerical policies.

The implementation should record or check the actual generated expression constants and coefficient maps against this calculation. The diagnostic here inspected local Python-MIP `LinExpr` operations, not a live compiled native matrix. Tiny-constant shortcuts in expression libraries and later runtime changes must not silently invalidate a claimed exact stored-matrix proof. In particular, actual service-row constants must also be checked: a library that drops a tiny service subtraction changes the stored service constant, whose difference from the ideal energy must then be propagated into the stored-row band or rejected by an explicit profile-consistency gate. In the inspected frozen cases all nonzero energy constants are far above the local library's negligible-constant threshold.

## Read-only diagnostics on current inputs

The standard-library script and detailed exact JSON are at `research-20260927/agent-notes/energy-row-preflight/inspect_aggregation.py` and `aggregation.json`. They inspect the frozen twenty-control JSON plus both complete public case variants without importing model code or a solver.

All twenty original fixtures have zero derived physical/stored-row band width. Both public cases have service-RHS float aggregation error +5.3290705182007514e-14 kWh. Each has 504 movements whose rounded leg sum differs from its exact sum, with maximum individual discrepancy 2.1316282072803006e-14 kWh. Maximum precomputed pullout subtraction defects are 2.1316282072803006e-14 kWh for depot 15 and 2.4868995751603507e-14 kWh for depot 16.

The physical band offsets around S_exact are approximately [-9.947598300641403e-13,+1.1111112030448567e-12] kWh for depot 15 and [-9.947598300641403e-13,+1.6546763959013333e-12] for depot 16. The derived stored-row band dominates both: exactly **±37/17592186044416 kWh**, approximately ±2.1032064978498966e-12. The union's exact absolute endpoints for both are

`[250264333071608001/281474976710656, 250264333071609185/281474976710656]`.

These diagnostics support a prospective arithmetic enclosure; they are not a new solver result or a waiver of full implementation review.

## Required source and execution checks

The preflight should verify the new formulation tag reaches raw snapshots, plans, hull dispatch/state identities and retained-boundary checks. Reuse the exact existing movement coefficients and eta; charge summation must include every owned interval once, including terminal visits, with no market-load substitution that double-counts energy. Record exact band inputs, outward endpoints and the actual added coefficient/row description in immutable raw evidence. Native dimensions should increase by the declared two constraints, without new variables or changed objective/replay/caps.

Pure tests should cover the fractional witness above; zero-energy movement and multiple-charge-visit cancellation; multileg rounding; nonrepresentable service sums; pullout/terminal assembly defects; both sign directions of the arithmetic band; outward endpoint containment; and rejection of changed/missing energy-row metadata. A source comparison should show only the approved energy constraints and version/provenance changes. All twenty physical fixtures and eight hull cases, targets, prices, limits and predecessor chains must stay unchanged. Native result audits must independently reconstruct the new rows, physical witnesses and fresh certificates. Earlier failures and successes stay archived with their original formulation/source identities.

## Flat-price matching reference: conditions before implementation

For a common price p across every chargeable period, full replenishment makes charging cost `(p/eta)*(service energy + selected movement energy)`. Define each movement's relaxed additive cost as its original driving-time cost plus `(p/eta)` times its energy. With a unique pullout and pullin for every service, the N-single-service baseline is vehicle cost times N plus fixed service charging cost plus all individual pullout/pullin movement costs.

An allowed connection i→j using mode m replaces pullin_i and pullout_j by m and saves one vehicle. Its saving is `vehicle_cost + cost(pullin_i) + cost(pullout_j) - cost(m)`. A maximum-weight bipartite matching over declared DAG connections yields the exact minimum cost of the path-cover relaxation when the vehicle cap is N. Parallel modes may be reduced only by choosing the best saving for the same ordered service pair. Unmatched vertices retain their original depot movements. For a smaller vehicle cap require at least N-V matched connections, rather than silently using an unconstrained matching.

This drops battery/reserve, charging-window and shared-connector feasibility, so its optimum is a lower bound, not a feasible fleet or native optimum. DAG ordering is necessary to rule out matched cycles. The actual service graph, explicit stationary-wait energy/time and all source movement alternatives must be preserved. The conservation premise and coefficient convention must be the same as the target physical model; if comparing a per-leg exact bound with a numerically perturbed native matrix, disclose or bound that difference. Use an exact matching/dual certificate or outward verified arithmetic before calling it certified. No matching optimization or operational bound was computed by this review.
