# Prospective classical baseline specification

Design only; no implementation, cohort/asset read, inference or execution. Freeze
this specification and its implementation before future outcomes. These are
additional **unvalidated candidate classical controls**, not established strong
or optimal baselines and not silent replacements for the frozen heuristic.
Adding arms requires a prospective manifest and budget. No novelty,
minimum-fleet optimum or performance claim is made.

## Interfaces and price audit

`codex_offline_rank.heuristic(case)` ranks by negative moving time, negative
0.1 slack and positive 0.1 depot dwell. It sees no tariff coefficients.
`NativeCase` supplies trips, declared movements/legs, battery/reserve, efficiency,
resources and market edges; supply coefficients `a,b` are separate planner inputs.
The offline audit loads fixed saved day logits, which cannot update themselves
when tariffs change.

The companion source-interface audit identifies current online calls:
`codex_local_campaign.py:197` passes `market.a` to `v8_scores(case,prices,root)`;
line 208 passes it to `score_case` for CatBoost. Both use
`learned_proposals.edge_features(case,prices)`, exposing charging-window mean/min
and market mean/spread (lines 85–113); neither receives `b`. Thus these scorers
can respond to changes in `a`, subject to actual fitted behavior, but not a
`b`-only change. This is an input audit, not an asset or response experiment.
Native charging/planning receives both `a,b`. A price-responsive bill alone
therefore cannot identify a learned ranking effect.
CA1's additional `b` input makes its comparison with these learners a deployable-
method comparison with unequal information, not matched-information attribution
to learning.

## Charging-aware edge ranking: CA1

Contract: `score(case,a,b) -> scores in original movement order, feature ledger`.
Validate dimensions, finite `a`, nonnegative finite `b`, and case physics. Let
`C=battery_kwh-reserve_kwh`, `eta=efficiency`. For each flexible connection
`e:i→j`, compute service energies `Ei,Ej`, movement energy `Ee`, total leg minutes
`de`, and `S=Ei+Ee+Ej`.

For a depot movement, its only intermediate charging window is exactly the gap
around `depot_split`. Intersect that gap with resource and market boundaries.
For each resulting slice, grid capacity is
`c=duration/60 * min(per_bus_kw,grid_kw)` when a connector exists, otherwise zero.
Aggregate by market period to `c_t`; set `U=eta*sum(c_t)`. Direct edges have `U=0`.
Record `D=max(0,S-C)` and margin `C+U-S`.

Use IEEE-754 binary64 operations, `math.fsum` for energy/capacity sums and signed
comparison residuals, and fixed ranking tolerance `tau=1e-6 kWh`. Set a stress
flag when any residual exceeds tau: direct `S-C`; depot
`Ei+predepot_energy-C`, `postdepot_energy+Ej-C`, or `D-U`. Log residuals within
`[-tau,tau]` as borderline. Use ordinary binary64 ordering for remaining rank
keys, with no epsilon ties; reject nonfinite computed features. This is a ranking
convention, not exact arithmetic, outward rounding or proof of impossibility.
Flags never certify feasibility either: they ignore other vehicles and earlier
route consumption. Replay's admission tolerances remain unchanged.

Define a deterministic electricity proxy `P(x,w)=sum(a_t*q_t+b_t*q_t²/2)`, with
`q_t=x*w_t/sum(w)`. For a depot use `w=c_t` and `x=D/eta`; zero demand costs zero.
Zero total weight returns zero proxy and a capacity-shortfall diagnostic; its
stress flag follows the same tau rule. For remaining movement energy
`max(0,Ee-D)/eta`, use market-period durations as `w`. Add these two proxies to
`deadhead_cost_per_min*de`. This proportional-fill proxy is neither optimized
charging nor realized fleet energy cost. Edge proxies cannot be summed into an
actual fleet bill or electricity saving; they use tariff inputs without labels.

Rank ascending by `(stress_flag, proxy_cost, -margin, -U, movement_id)` and
convert that order to descending integer scores. Preserve all boundary movements.
For the next study use the common price-blind backbone and exact flexible count
in `RECOVERY_LEARNED_VALUE_STUDY_ADDENDUM.md`; it supersedes the earlier
rank-dependent 30%/top-three union. Flags affect rank, not a separate deletion rule. Save
features, order and actual retained cardinality. Complexity is `O(MR+M log M)`
with `R` resource/market slices, `O(M+R)` working storage; all work is timed.

## Constructive low-fleet proposal: CF1

Topology construction is deliberately price-blind. Start one route per trip,
ordered by `(start_min,end_min,id)`, selecting declared pullout/pullin modes by
`(total leg minutes,id)`. Missing boundaries mean construction failure, not global
infeasibility. Intermediate route count may exceed `max_vehicles`.

Enumerate merges from the last trip of route A to the first of distinct route B
using declared direct/depot movements. Accept only chronological, nonbranching
joins covering each trip once and passing optimistic route SOC propagation:
start full, subtract each leg/service energy, allow up to the individual charging
capacity at each declared window, cap SOC at battery capacity, and require reserve
throughout plus enough terminal-window capacity to replenish fully. Use the same
binary64/tau convention for this screen; it is not an impossibility proof.
Ignore shared charger contention here. Choose the eligible merge minimizing
`(added deadhead minutes,-added charging capacity,movement_id,A_first_id,B_first_id)`;
remove the replaced pullin/pullout. Added minutes equal new-link minutes minus
those removed; added capacity equals new-link capacity minus removed pullin
capacity. Repeat until no merge remains. This greedy
rule targets few vehicles without claiming the minimum. Straight recomputation
costs at most `O(N²MR)` and stores `O(M+NR)` data.

If routes exceed `max_vehicles`, report no constructive proposal. Otherwise call
`recover_paths` and build the original full native model. Fix every movement
binary bound to the proposed 0/1 topology. Attempt charging feasibility, then at
most two tangent-objective solves under target `a,b`: start with `(a_t,0)`, add
`(a_t+b_t*load_t,-b_t*load_t²/2)` after the first replay. All calls share the
cumulative fixed-topology completion allowance. Retain the lowest replay-valid
exact bill. Extract charging sessions and independently replay
SOC, simultaneous connector/power use, full terminal replenishment and exact bill.
Necessary checks and path recovery never replace this proof. Fixed-topology bounds
are not unrestricted bounds. This needs a new helper: existing
`_complete_topology` requires incumbent variable values and cannot directly accept
an uncharged route list.
Before launch, qualify the helper's fixed-binary inventory, unchanged physical
rows, remaining variable types and solver statuses; call it an LP only after
confirming every unfixed variable is continuous. Feasible/optimal fixed-topology
status is not full-model optimality. Neither implementation correctness nor
completion within the proposed six seconds at T=60 is established.

After a qualified fixed-topology `INFEASIBLE` status, undo merges in reverse insertion order, at most
two repairs; all rebuilds share the same allowance. Timeout/no incumbent stops
construction attempts. No feasible route/bill oracle or reference label is used.
A replay-valid witness becomes a durable fallback; submit only full-model movement
binaries via the existing checked start interface, leaving continuous values unset.
Retain fallback through rejection; record actual native processing separately.
Without a witness, attempt cold full search only if time remains.

## Common clock

One supervisor anchor precedes loading, scoring and construction. CA1 uses the
next study's common recovery schedule. CF1 permits construction through
`t0+0.1T`, fixed charging through `t0+0.2T`, cumulatively at most the common
`max(2,0.1T)` completion seconds; unused time returns to full search. Keep the
common finalization reserve, original endpoint and full-search round cap. Count
all setup, necessary checks, repairs, native calls, replay, exact billing, captures
and durable writes. No free cached labels, preprocessing or reset clocks.
Record no-plan, rejected, censored and missing outcomes without replacement.
