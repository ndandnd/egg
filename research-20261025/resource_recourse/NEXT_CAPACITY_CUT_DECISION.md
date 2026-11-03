# Next analytic diagnostic: necessary preterminal charging capacity

25 October 2026. STATIC mathematical direction only, not a launch manifest. This note uses `INTERPRETATION_REVIEW.md` and the source/schema of `classical.opportunity`; only field names were checked in the existing derived `READOUT.json`. No original cases/plans, outcome values, new calculations, imports, hashes, replay, native calls or solver work were accessed/performed. No script is created or run by this decision.

## Question and fixed scope

Can necessary charging-access cuts account for the fixed-reference failures under 45 kW, while remaining consistent with the admitted adaptive topology at 10006 despite its higher total energy? This is a new analytical diagnostic: the completed readout reports energy, windows and a terminal **sufficient** condition, but did not evaluate the following per-bus/shared necessary inequalities. It is not another compact export, acquisition attempt or rescue solve.

Evaluate all eight original-reference group×resource diagnostics and all sixteen planned adaptive group×resource×tariff records, retaining every missing/unavailable record. Use only opportunity diagnostics already exported in the closed readout. Distinguish an accepted newly selected topology, an unchanged retained route and an acquired-prior fallback using their existing flags. Do not substitute fallback diagnostics for an unavailable new topology or count repeated copies of one diagnostic as independent cases. The four exposed groups remain the units; no available-only effect or population claim is proposed.

## Necessary cut and assumptions

Let `h=1080` minutes be the common terminal opening, `B` battery capacity, `r` reserve and `eta` constant charging efficiency. For vehicle `v`, the exported fields supply total consumption `D_v`, ideal grid demand `E_v=D_v/eta`, margin `m_v=B-r-D_v`, final return time and its selected depot-visit windows. Require all paths to finish consumption and return by `h`, full initial batteries, reserve at final arrival, nonnegative service/movement draws, no unmodeled draw after return, and no terminal charging before `h`. Before `h`, charging can occur only in the selected depot windows. Charging is divisible/preemptible with the source's zero/one serial connector and declared shared/per-bus power. These are ideal physical assumptions, not statements that a copied numerical matrix is exact.

At final arrival, `SOC_v = B-D_v+eta*g_v(pre) >= r`. Therefore every feasible schedule needs

`g_v(pre) >= ell_v := max(0, D_v-(B-r))/eta = max(0,-m_v)/eta`.

No battery or case read is needed to reconstruct this from the exported exact strings. If `D_v>0`, use `ell_v = E_v*max(0,-m_v)/D_v`. For `D_v=E_v=0` and a nonnegative margin, `ell_v=0`; inconsistent zero/negative demand, efficiency, margin or missing joins gives **unavailable**, not a guessed value. When reconstructed, `eta=D_v/E_v` must be consistent across positive-demand buses and lie in `(0,1]`. This is algebra on exported represented coefficients, not regeneration or an independent physical replay.

For each vehicle, clip its selected depot windows to `[0,h)` and merge overlaps to form `W_v`. Let `W` be the union across vehicles, merging overlaps again. For any time set `U`, let

`C(U) = integral_U [1(connector available)*min(bus power,grid power)] dt/60`.

The frozen study uses one connector, bus power 90 and constant grid level `p` in `{90,45}` over the horizon, so `C(U)=min(90,p)*duration_minutes(U)/60`. Do not sum individual window capacities across overlapping windows or buses. Necessary conditions are

`ell_v <= C(W_v)` for every bus, and `sum_v ell_v <= C(W)`.

The shared inequality follows because actual preterminal charge must supply each bus's lower bound but cannot exceed the shared connector's capacity on the union of selected opportunities. Individual cuts prevent one bus's inaccessible deficit being hidden by another bus's windows. Capacity ignores headroom, the order of service consumption and competition among subsets of buses; it is deliberately an **upper** bound on usable early charging.

One companion total-energy cut uses only the already exported terminal capacity `C_T` and total ideal grid demand `E=sum_v E_v`: post-opening charging cannot exceed `C_T`, hence preterminal charge must also be at least `max(0,E-C_T)`. The shared lower bound can therefore be reported as `max(sum_v ell_v, E-C_T, 0) <= C(W)`. Require `all_return_by_terminal_open=true` and common terminal start equal to `h`; otherwise this particular decomposition is unavailable. No subset enumeration, time-prefix expansion, capacity scan or optimization is included in this proposed package.

## Reporting and limits

Report the exact represented lower bounds, per-bus and merged shared capacities, signed capacity-minus-required margins, window/overlap counts and assumption/missing flags. Preserve the original acquisition/native/physical-admission statuses beside these diagnostics without reclassifying them. A negative margin is a violation of a necessary condition of the **stated ideal fixed-topology model**. It can provide a structural explanation for a restricted native `INFEASIBLE` status; it is not an unrestricted or tolerance-qualified code certificate. A nonnegative margin proves neither feasibility nor the cause of failure: earlier SOC deadlines, headroom and overlapping allocation can still obstruct charging.

Higher total energy can coexist with better feasibility if route changes provide more accessible early windows or redistribute per-bus reserve deficits. The already admitted adaptive witness is evidence of its operational feasibility; a passing cut would only be consistent with that evidence. An apparent violation for such a witness must retain the discrepancy and inspect assumptions/represented numerical scope, not repair a plan, widen tolerances or revoke prior admission automatically. No reporting epsilon is an optimization or energy-feasibility bound. Keep exact signed margins; tiny represented violations remain numerically qualified rather than promoted to physical impossibility.

Failure to explain one or all three reference statuses must be reported. The unresolved full-graph `INF_OR_UNBD` cases remain unresolved regardless of cuts on the reference topology; neither a reference violation nor a passing reference cut establishes global fixed-N feasibility/infeasibility. This diagnostic supplies no route-optimality, cost/timing-causality, ML value or new model-training gate.

## Prospective input allowlist and budget

The sole numerical input would be the existing closed `resource_recourse/READOUT.json`, read once. Authorized context is group/base/service/resource/target/phase, original versus selected-route role, parent endpoint/operational source/retained-route-change flags and existing status/missing labels. Within `opportunity_diagnostics`, admit only `available`, `unavailable_reasons`, `per_vehicle` (`vehicle` for local joins only, `total_consumption_exact`, `ideal_grid_kwh_exact`, `no_midday_soc_margin_kwh_exact`, `last_pullin_return_min_exact`), `selected_depot_windows` (`vehicle`, `lo_min_exact`, `hi_min_exact`; movement IDs unused), `all_return_by_terminal_open`, `common_terminal_start_min_exact`, `common_terminal_capacity_grid_kwh_exact`, and `total_ideal_grid_kwh_exact`. Do not inspect original rows/specs/plans, charge sessions, loads, costs, score/model fields or cached nested diagnostics. Missing exported fields remain missing; do not reopen parent artifacts. Output scalar cut/margin summaries and anonymous per-bus ordinal diagnostics, not raw movement/window-ID vectors.

Select a separate NEW analytical allowance of **20 CPU seconds / 45 wall seconds total**, body 15 CPU / 35 wall and publication/exit reserve 5 CPU / 10 wall, under the human's standing routine resource authority. Use one standard-library process/thread, no children/native libraries. The resource-recourse package and its sole compact readout are CLOSED and are not reopened or renamed. Before any execution, parent must freeze a thin source/field projection, one exact command and a fresh exclusive namespace, prospectively charge this new allowance against the current cumulative tracking prefix, and preserve actual spend/failure. No historical reset or automatic retry follows. If schema/assumptions are missing, record unknown rather than reopening cases or plans. This direction is not an executable manifest and authorizes no run.
