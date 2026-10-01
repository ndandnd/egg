# Related-work prose for adaptation into the manuscript

Drafted September 27, 2026. The cited papers and access limitations are recorded
in [RELATED_WORK_MATRIX.md](RELATED_WORK_MATRIX.md). Citation keys below match
[references.bib](references.bib). This text describes EGG's research question and
methodological boundary, not an uncompleted operational result.

Electric-bus scheduling already combines discrete duty construction with
charging decisions and electricity-related objectives. Wu et al. formulate a
multi-depot problem with time-of-use tariffs and peak-load reduction, using
branch-and-price and a reusable trip-chain pool (`wu2022grid`). De Vos et al.
model partial charging and limited charging-station capacity in a path-based
formulation (`devos2024capacity`). Parmentier et al. develop scalable route and
recharge column generation (`parmentier2023fleets`), while ten Bosch et al.
generate schedules through simulated annealing and recombine them using integer
programming (`tenbosch2026scheduling`). These studies establish the operational
importance of feasible duties and charging infrastructure. Our question concerns
the economic support of complete fleet plans: whether a realizable daily plan
can be a best response to the marginal energy prices associated with its own
load. This requires distinguishing vehicle-duty relaxations from convexification
over complete fleet schedules.

Bus participation in electricity markets is also an established subject.
Zoltowska and Lin aggregate detailed bus and charger restrictions into hourly
auction bids and disaggregate accepted plans into charging schedules
(`zoltowska2021auction`). Maldonado and Saumweber discuss pricing rules and
evaluate IP and extended locational marginal pricing with EV participants
(`maldonado2022pricing`). More recently, the preprint of Manzolli et al. combines
bus/V2G optimization with supervisory agents that trigger reoptimization,
propose tariffs and evaluate schedules (`manzolli2026agents`). We therefore do
not claim fleet aggregation, tariff-aware scheduling or agent orchestration as
new. Instead, the complete physical schedule set is made explicit so that a
convexified planning objective can be interpreted without assuming that its
mean charging profile is implementable on a single day.

The connection between nonconvexities, supporting prices and compensation has
long been studied in electricity-market optimization. Madani et al. include
nonconvex demand bids and connect dual-optimal prices to minimum aggregate
lost-opportunity compensation (`madani2018pricing`). Andrianesis et al. derive
convex-hull prices through Dantzig–Wolfe decomposition and schedule column
generation (`andrianesis2022hull`). Hümbs et al. show why complete participant
descriptions are essential when using a centralized relaxation to characterize
price-supported equilibria (`huembs2022complete`). Our price-support proposition
is a specialization of this established logic to the stated fleet and convex
supply-cost model. Its role is to translate objective bounds into conditional
statements about incentives, with attainment, model identity and numerical
allowances stated explicitly.

The interpretation depends on the price and institutional setting. Bichler et
al. distinguish stability, individual rationality and budget balance when
demand is flexible (`bichler2023pricing`). Accordingly, we separate regret at a
physical schedule's own marginal price from fleet and supplier lost-opportunity
costs at a common convex-hull price. Neither a small planner gap nor a
compensation identity alone specifies a funded, truthful or voluntarily
participatory mechanism. Likewise, a within-fleet shared charging limit differs
from a resource contested by independent operators; their feasible deviations
must be defined before drawing equilibrium conclusions.

Aggregation may reduce nonconvexity, but its meaning and scale require care.
Hreinsson et al. apply Shapley–Folkman arguments to aggregated dispatchable
demand (`hreinsson2021aggregation`), while Bi and Tang refine nonconvexity-based
duality-gap bounds (`bi2020duality`). Our controlled examples distinguish
relabeling the same independent participants from changing duty indivisibility,
total service or supply curvature. They also distinguish relative planner
efficiency from absolute individual incentives. The convex flexible-load
framework of Gu and Qin assumes a compact convex decision set and strictly
convex collective disutility (`gu2026equilibrium`); indivisible fleet duties
lie outside that response premise rather than contradicting its conclusions.

Finally, the computational value of prediction must be assessed against strong
reuse. Sugishita et al. compare learned dual warm starts with column
prepopulation, LP initialization and cold start in unit commitment
(`sugishita2024warmstart`), and Shen et al. develop learned-reference adaptive
stabilization (`shen2024stabilization`). These precedents motivate testing
whether prediction improves the complete cost of reaching the same certificate
after retaining feasible columns and applying the known tariff translation.
Proposals may aid discovery; they do not replace current-state pricing bounds,
physical replay or clean final verification.

## Editing instructions

Use the scheduling and economics paragraphs in the main paper even if the ML
workstream is dropped. Move the last paragraph to a computational subsection if
reuse is only an engineering component. Keep the two recent arXiv sources labeled
preprints; recheck their versions at submission. Do not convert the matrix's
abstract-only access into full-paper claims. Avoid a long table of check marks
asserting all other studies lack EGG's features: the inspected formulations
support narrower comparisons only.
