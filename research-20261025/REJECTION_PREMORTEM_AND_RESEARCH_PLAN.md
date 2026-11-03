# EGG: rejection premortem and a smaller, decisive research program

25 October 2026. Prepared after the human requested a scientific reset and actual
experiments. This is a research assessment, not a manuscript or acceptance forecast.
The evidence audit and targeted primary-paper checks are companion files.

## Honest starting point

There is a real finite-budget development result: a graph-attention connection
ranker produces feasible schedules with lower integrated supply cost in a
completed 20-timetable, three-seed, six-arm experiment. All 342 admitted physical
plans were independently replayed. The graph and new CatBoost each returned
60/60 valid endpoints. These are useful assets, not a finished contribution.

At 40 trips, graph and CatBoost essentially tie; graph's median group gain over
the simple heuristic is 0.47%. At 80 trips it is 68.36%, but 91.916% of the summed
paired saving is the cost of using fewer buses. Different timetable groups
occupy the two sizes. The architecture result, electricity mechanism and scaling
mechanism therefore remain unidentified. Random pruning also helps relative to
a struggling unrestricted formulation. We must preserve these distinctions.

The current screen's saved `bill` equals c+a'L+1/2 L'BL, an integrated supply-cost
objective. Under an all-units marginal-price payment p=a+BL, an atomic fleet pays
c+a'L+L'BL. Historic results should be relabelled in scientific interpretation,
not rewritten. An economic institution cannot be supplied retrospectively by a
different name for the objective. A separate reoptimization under the intended
payment rule is required for strategic-behavior claims.

## Imagine the rejection letter

1. **The authors have not isolated their mechanism.** Their large gain is mostly
   fleet size and may disappear after supplying all methods with a competent
   constructive incumbent. Fixed fleet count alone still leaves route-energy
   confounding; one tariff cannot identify price-aware learning.
2. **The closest prior work is stronger than the claimed contribution.** Learned
   EVSP connection pruning, greedy/learned hybrids and adaptive pricing networks
   already exist. Related studies solve hundreds to thousands of trips and
   include serious classical candidate selection. Our weak score and compact-MIP
   failures cannot stand in for that literature.
3. **The economic object changes across sections.** System cost, fleet payments,
   price-taking response, convexified support and an executable market mechanism
   are different objects. An LP/QP dual price is not a truthful auction.
   The assumed price impact must also be plausible for the fleet's size relative
   to the relevant market or feeder; an arbitrary large slope cannot substitute
   for that calibration. Fleet cost and energy-cost units must be comparable.
4. **The mathematical results are either inherited or too elementary.** A
   two-schedule cycling condition, incumbent retention, Caratheodory support and
   a Fenchel-gap decomposition are useful tools. Without a new implication that
   changes an algorithm or operational decision, they are not the contribution.
5. **The external-validity and computational claims outrun the experiment.**
   Twenty related synthetic timetables, one price shape, imitation labels and a
   short horizon do not establish practical generalization. Seeds are not new
   timetables. Restricted bounds do not certify the unrestricted problem.
6. **The study is fragmented.** Stabilization, cycling, ML architectures, recovery,
   pricing and bid menus each get a partial result, but none answers one central
   question convincingly. More source tests do not repair that fragmentation.

## What to concede now

- The tested stabilization variants did not earn an end-to-end acceleration
  headline on their historical cohort. Do not promise that higher dimension will
  reverse the result, or reopen protected holdouts to seek a better story.
- Generic learned pruning and generic recovery are prior art. GNN superiority
  over strong trees/classical optimization is currently regime dependent and
  inadequately tested.
- The current comparison is a planner-resource-cost experiment, not established
  strategic payment savings, tariff learning, global optimality or a market
  implementation.
- The model can help produce plans through an optimizer; it is not a reliable
  standalone fleet-plan predictor. More epochs or architectures are not the
  scientifically justified next action.
- The independent engineering evidence should be retained, but the recent
  supervision work has consumed disproportionate attention. Stop expanding that
  machinery. Preserve strict clocks for a later genuine speed claim, while using
  simpler bounded analyses for questions that need no real-time controller.

## One question to earn

**When electricity prices and shared charging constraints change, does learning
preserve valuable feasible schedule alternatives better than strong classical
methods, and can the resulting decisions be verified efficiently?**

This is a hypothesis, not a novelty claim. The primary study should initially
state the planner objective unambiguously. Atomic payment minimization is a
separate economic control. A market-design paper should proceed only if the
institutional mapping and an important price-support result survive their own
tests. Do not bolt a bidding mechanism onto a scheduling paper for venue fit.

## Experiments in decision order

| Priority | Experiment and identification | Gate and consequence |
|---|---|---|
| 0: now | Reprice the existing verified complete-plan library under mean-preserving tariff shifts; compare equal observed fleet counts, energy quantity, time exposure and curvature. Separately compare planner and all-units-payment objectives. | A witnessed ranking reversal identifies available price sensitivity in this library. Absence does not prove absence in the full problem: plans and charging were originally optimized for one regime. No ML attribution follows. |
| 0b: now | Solve small convex relaxations of that library and independently bound their primal-dual gap; inspect curvature and load-profile diversity. | Learn whether nonconvex price-support geometry is material in observed alternatives. Catalog bounds are never full-fleet certificates. A negligible effect weakens the immediate economic story; a positive effect motivates full-space pricing checks, not a theorem claim. |
| 1 | Competent-baseline challenge on new development groups: graph, CatBoost, charging-aware constructive/GRASP and LP-informed control, plus unrestricted search as appropriate. Common physical model and viable incumbent, exact retained budget, repeated seeds, paid end-to-end time. | Continue a learning claim only if it improves decisions over the best classical control. If the common incumbent erases the effect, concede that the old gain primarily repaired weak fleet construction. Select the smallest effective method. |
| 2 | Price-information intervention: the same trained ranker with actual versus frozen/permuted price inputs, paired across tariff and charging-capacity regimes. Fixed-fleet and fixed-route charging diagnostics isolate demand and timing. | If charging can respond but classical/tariff-blind methods capture its value, concede the price-learning mechanism. If charging barely responds, change the scientifically justified operating regime before adding model complexity; preserve the negative result. |
| 3 | Recovery/budget allocation: classical and learned prefixes, common unrestricted continuation, full-from-start with the same incumbent, and prespecified time checkpoints. | Establish primal versus certificate benefit separately. If rebuilding/restoration uses the gain, simplify. No guaranteed superiority follows from keeping an incumbent. |
| 4 | Independent scaling: nested timetable sizes and public-network instances with whole-network holdouts, physical battery/SOC and charger stress, tariff shifts, repeated seeds. | Demonstrate a useful range rather than a single solver-collapse point. Include failures and unresolved bounds; no outcome-selected exclusion or final-test tuning. |
| 5: only if needed | Diverse feasible witnesses/quality-band labels and per-trip decision/ranking loss, held architecture and inference cost fixed. | Require better downstream decisions and damaging-exclusion rates. AP/log loss alone cannot justify the labeling/training cost or a larger network. |

The first baseline experiment should be a small discriminating development
study, not a large factorial sweep. Eight new bases, three seeds, four methods
and two fleet conditions produce 192 assignments; at 60 seconds per assignment
the nominal online envelope is 3.2 hours. A separately frozen practical budget
must also include construction, loading, replay, failures and study-level cost.
Eight groups do not establish broad generalization. The concrete classical
method must first demonstrate feasibility; its unit tests do not count.

Prespecify availability/failure as an endpoint, paired per-timetable economic
differences, a practical improvement margin, uncertainty calculation, budget
checkpoints, seed order and all exclusions before results. Do not select the
winning model on these evaluation outcomes and then call that same result a test.
For an expensive method, report the number of repeated decisions needed to
amortize data generation, labeling and training.

Permuting one trained model's price inputs tests sensitivity and distribution
shift, not by itself the value of learning price information. That claim also
requires a similarly tuned tariff-blind model trained/selected using training
groups only, plus a frozen-candidate-pool charging-reoptimization control. This
separates the downstream solver's price response from a learned ranking effect.

## The mathematical work worth doing

Use the exact cost/price-support decomposition in
`PRICE_SUPPORT_DECOMPOSITION_NOTE.md` as a diagnostic foundation. For a complete
feasible schedule j and a true supporting convexified price p*, its cost excess
splits into linear-price opportunity loss and a curvature-weighted load-profile
distance. This is a classical identity, not a newly discovered theorem.

A worthwhile extension must prove something specific and useful: for example,
conditions under which charging flexibility makes a price signal implementable;
a nonvacuous approximation/certification guarantee for preserving an appropriately
diverse schedule set; or a structural relation between resource bottlenecks,
load-profile geometry and the actual cost of coordination. The proof must apply
to the physical feasible set being solved, including shared capacity. Independent
rounding across fleets does not preserve coupled feasibility automatically.

Negative controls are essential. Splitting time intervals while scaling energy
and curvature consistently should not create an economic effect. More stored
time coordinates do not necessarily mean more decision-relevant directions.
Increasing a menu cannot by itself eliminate an indivisibility gap. Finite
price-iteration transients cannot prove nonexistence of an equilibrium.

## What an excellent first draft would contain

One explicit decision problem/institution and one falsifiable contribution;
formulation-level comparison with the closest papers; a structural result whose
implication is tested; a genuinely strong and reproducible classical benchmark;
mechanism ablations; independent scale/network/regime tests; and an honest
boundary of failure, cost and certificate scope. A few compelling connected
figures are more valuable than a catalog of architectures and engineering gates.

The present task executes the two immediate diagnostics and two distinct
classical competence controls, and records what they
actually show. It does not declare the remaining experiments complete or claim
an Operations Research/Management Science acceptance probability. The long-term
venue aspiration should guide significance, not force positive findings.

## Results obtained during this reset

Both immediate analyses were executed once under their prospectively recorded
budgets. The first consumed 342 admitted old endpoints and matched the exact
original objectives and historical input hashes. On the minimum-observed-fleet
bank, moving the cheap window from day to late yields a materially better bank
selection in 13/20 timetables. Median saving from changing the original-day bank
winner is 0.7165%, maximum 4.2338%. Flat and other time-shifted coefficients give
smaller median effects. These are fixed-plan catalog opportunities, not a
measured ability of the GNN to respond or a full-problem optimum.

The system-cost and uniform marginal-price-payment minima have materially
different system costs in 8/20 original-day minimum-fleet banks (maximum loss
6.0774 cost units from selecting the payment minimizer). This is an actual
counterexample to treating the two objectives as interchangeable, within the
same recorded candidate library. It is not a strategic-equilibrium result.

The second experiment covers 120 catalog/price/curvature cells. At original day
prices and curvature, the median pure-minus-convexified catalog gap is 0.025455%
of best pure cost, with maximum approximately 1.021835%. At five times curvature
the day median is 0.225830%. All zero-curvature controls are exactly zero. One
SLSQP status is non-success and remains a failed optimizer receipt; all 120
separately checked rational primal/dual bounds satisfy the frozen numerical
catalog tolerance. No retry was made. This is finite-library evidence, neither
an upper nor a lower bound on the full fleet integrality gap. The small typical
total-cost effect challenges an assumed large benefit in this observed bank.
Fixed fleet costs dilute that percentage: report absolute and electricity-cost-
normalized gaps before judging its economic importance. The catalog's omissions
also prevent a conclusion that the full physical problem has an unimportant gap.

There is also a representational limitation visible in source, without an
experiment: `codex_local_campaign.v8_scores(case, prices, root)` receives only
`market.a`; `learned_proposals.edge_features` has price-window/mean/spread
features but no `market.b`. With the case, linear-price vector and model fixed,
varying supply curvature cannot alter this ranker's scores. This does not show
its retained set must become bad, but it rules out claiming that its current
connection ranking *adapts* to changes in curvature. Adding a feature is justified
only after establishing useful decision variation under that intervention.

The diagnostic load libraries have a median 2.5 singular directions explaining
95% of their squared variation, despite 30 stored time periods. This descriptor
is conditional on the small observed bank; it supports testing actual load-space
variation rather than assuming that a larger nominal time dimension guarantees
stabilization gains.

Bank cardinality constrains this descriptor mechanically: with m distinct load
profiles its centered rank is at most min(m-1,30). Report that ceiling and support
counts alongside the SVD statistic; do not label it intrinsic physical dimension.

See `price_signal_audit/RESULTS.md` and `catalog_hull_audit/RESULTS.md` for exact
denominators, intervals, costs, failures and caveats. These negative/limited
results narrow the next experiment; they do not need to be turned into a
spectacular claim.

The additional classical competence check finished once on the prespecified
40/80-trip pair. It admitted a physically replayed40-trip plan with15 buses in
13.109s, but its80-trip29-bus construction produced no independently admitted
endpoint: charging returned after the55s cutoff, and full record publication
finished at64.613s. The helper's internally feasible candidate remains preserved;
this is not a proof of infeasibility. Historical graph endpoints used3 and5 buses
on these cases, respectively, under different seeds/allocation. The disparity
disqualifies this greedy implementation as our strong classical control; it does
not disqualify classical methods. Do not run the large comparison until a serious
construction/improvement baseline is competent. See
`classical_competence/RESULTS.md` for the failure and resource accounting.

A distinct global fleet-count control was then executed once on the same exposed
pair, preserving the full physical constraints and doing one solve per case.
It independently replayed a three-bus40-trip plan, with native incumbent/bound
both3 (3.724s total). At80 trips it returned30 buses and a fleet lower bound of2
after60s native search (71.332s total). A previous learned endpoint used5 buses.
These objectives, seeds and budgets are unmatched, so this is no speedup or paired
ML comparison. It identifies a serious formulation/search weakness to challenge:
the80-trip model has177,958 variables and190,037 rows. A stronger classical route
pool, root-LP-informed control and common feasible starting plan are now mandatory
before claiming an electricity-specific learned advantage. See
`classical_competence/FLEET_FIRST_RESULTS.md`. No further repetitions were made.

A subsequent frozen three-cover conventional pool also completed once. Its40-trip
plan had3 buses. At80 trips it returned24 replay-valid buses with a numerical
restricted fleet bound of24 in0.746s of native search. Thus search exhaustion
does not explain this pool's missed5-bus competence target. Crucially, it kept
only113/5882 flexible modes (~1.92%), versus the old learned selector's roughly
30% plus floors. This is a candidate-density confound, not evidence that
matching or classical methods are inherently inferior. The next separate control
matches exact K and a common backbone for CA1 alone versus cover-preserving CA1
fill. No pool expansion or retry followed. See matching_pool/RESULTS.md,
DIAGNOSIS.md and NEXT_CONTROL_DECISION.md; a broad ML study remains gated.

The separate exact-density control now supplies a competent conventional arm.
All four decisions independently replayed. At identical flexible quotas429/1765,
CA1 versus Cover+CA1 used4 versus3 buses on40 trips and5 versus5 on80. Native
restricted fleet bounds matched each incumbent; system costs were evaluated
rather than optimized. Cover+CA1 meets the exposed3/5 gate, ordinary CA1 misses40,
and the aggregate all-four gate remainsfalse. Pool substitutions were47/6 modes.
This supports a fairer next comparison, not an ML advantage: conventional scoring
also finds the five-bus80-trip plan once candidate density is comparable. These
are one-seed exposed cases. Keep both conventional arms frozen in independent,
repeated-seed/equal-budget comparisons, including a common feasible fallback and
paid preparation. See density_control/RESULTS.md, SCIENTIFIC_INTERPRETATION.md
and NEXT_STUDY_REQUIREMENTS.md. No broad comparison or new training ran here.

The first matched conditional warm study is now complete on four additional
base groups,40/80 nested variants and three native seeds. All168 endpoints were
accepted;167 met method_success, with one CatBoost run retaining an earlier
improved result after a later timeout. Holding fleet count fixed and deadhead
cost zero removed the previous fewer-vehicles explanation. GNN passed the frozen
diagnostic rule: mean paired gain1.2318882% of prior late electricity cost versus
CoverCA1,12.0116748% versus the four-round fixed-route control, positive group
medians4/4 for each. CatBoost failed versus CoverCA1 (mean−1.0282453%,positive2/4).
The four groups are not24 independent timetables; no price-information causality,
SOTA, significance, cold speedup or unrestricted certificate follows. The small
Cover margin needs replication. See warm_replanning/RESULTS.md and critique.

A new important control issue was found before the next launch: fixed-route
charging stops at four tangent rounds with unused time and nonzero finite-envelope
gap. A direct convex-QP fixed-topology check is next, before the prepared eight-
group GNN_day replication. The old four-round results and gate stay unchanged;
no retroactive replacement of a comparator. This is strengthening the classical
control rather than manufacturing a learned advantage.
