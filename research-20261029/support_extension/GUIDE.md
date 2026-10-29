# EGG self-study guide

Companion to the 22-slide **Understanding EGG** learning deck, prepared 29 October 2026. This guide explains the current evidence; it is not an independent reproduction. The support extension has completed exact implementation qualification, and its written proof establishes its continuous-domain claims. Sources are repository-relative to `ml-prediction-20261017`. See the extension's [proof](PROOF.md) and [results](RESULTS.md).

## Start with the question

A bus fleet can minimize total operating and electricity supply cost while wanting to change its schedule at the marginal electricity prices associated with its own load. The current research establishes this possibility in explicit small models. It has not established how common or economically important it is in operating fleets.

Read the guide in order. First explain the three objectives without equations; then work through the numerical example; finally interpret the experiments and open questions.

## Glossary

| Term | Meaning here |
|---|---|
| EVSP | Electric vehicle scheduling problem: assign services, connect them with feasible movements, and schedule charging. |
| Service | A mandatory passenger movement with fixed timing and declared energy use. |
| Duty | One bus's sequence of services, movements and charging. |
| Complete fleet plan x | Duties jointly covering every mandatory service while respecting battery and shared charging constraints. |
| X | The full admissible set of complete plans under one declared model. |
| e(x) | Purchased grid energy by market interval. |
| c(x) | Intrinsic fleet operating cost, including the declared vehicle fee. |
| F(e) | Incremental supply cost of providing fleet load e. |
| U | Background grid demand in the learning pilot; not battery inventory. |
| Marginal price p | A gradient of differentiable supply cost, or an admissible subgradient where supply cost is nonsmooth. |
| D | Minimum physical planning cost. |
| CH | Minimum planning cost over the convex hull of complete plans' energy/cost pairs. |
| Δ | Physical–hull gap D−CH. |
| Regret r(x;p) | Gain available by changing the entire fleet while holding posted p fixed. |
| Column | A variable representing an option in a restricted optimization model. Physical EVSP columns can represent one-bus duties; the economic hull here instead uses columns representing whole feasible fleets. A collection of duty columns must still satisfy service coverage and shared-resource constraints. |
| V2G | Vehicle-to-grid export. It is not implemented in the inspected current experimental path. |

Source: `paper/latex/model_theory.tex`; `research-20261028/paper_core_verification/STATE.md`; `research-20261027/grid_information_pilot/RESULTS.md`.

## Three objectives, three questions

**Planner:** choose x to minimize c(x)+F(e(x)). This measures operating cost plus electricity provision cost.

**Posted-price fleet:** choose x to minimize c(x)+p·e(x). The announced p stays fixed while comparing all admissible alternatives. Define V(p) as this minimum. A candidate's regret is c(x)+p·e(x)−V(p).

**Strategic fleet:** choose a plan anticipating how that choice changes the eventual price and payment. A schematic expression is c(x)+p_x·e(x), but a real strategic model needs its settlement and interaction rules specified. EGG's posted-price support test does not solve that game.

Supply cost and the electricity bill are different functions. Calling an operator large enough to influence demand does not remove the need to specify which objective and price-setting rule it faces.

For the manuscript's separable quadratic convention, F(e)=Σ(a_t e_t+b_t e_t²/2), so marginal price is a_t+b_t e_t. Background demand enters an incremental model through C(U+e)−C(U). Predicting U can improve charging decisions without improving routing. The pilot RESULTS identifies U and curvature b but does not reproduce its full coefficient table; do not transfer coefficients from a different experiment or forget the quadratic half-factor convention.

Source: `paper/latex/model_theory.tex`; `research-20261027/grid_information_pilot/RESULTS.md`.

## Work through the nominal exact example

Two mandatory services A and B run during [0,1] and [2,3]. Each consumes 15 kWh. Every used bus starts with a full 20 kWh battery and must finish full by hour 4. The early charging window [1,2] permits 10 kW; the terminal window [3,4] permits 30 kW. Charging is lossless and continuous, with the other simplified physical assumptions stated in the manuscript. Each used bus costs 7 synthetic units.

One bus covering both services must charge 10 kWh early and 20 terminally. Two buses covering one service each can charge q early and 30−q terminally for any q∈[0,10]. Both structures purchase 30 kWh: full terminal replenishment prevents either from benefiting from unpaid depletion of initial inventory.

Supply cost is F(q,z)=4q+(q²+z²)/10. The one-bus plan costs 97. The cheapest two-bus plan charges (5,25) and costs 99. Thus the physical planner chooses one bus and D=97.

At its load (10,20), the marginal price is (6,4). Its posted-price objective is 147. Holding that price fixed, two buses charging (0,30) have objective 134. Therefore the planner-optimal fleet has regret 13. The fleet's profitable fixed-price deviation does not mean it lowers system supply cost.

Source: `paper/latex/exact_results.tex`. These are synthetic exact-model calculations, not observed monetary savings.

## The hull is a bound, not a fractional operating fleet

The complete-fleet hull takes convex combinations of the pairs (e(x),c(x)) for physically admissible complete plans. Supply cost is then evaluated at the mean load. It yields a lower bound because the physical pairs are included in their hull.

For the nominal example, the hull optimum mixes weight 27/40 on the one-bus plan (10,20) and weight 13/40 on the two-bus plan (0,30). CH=7591/80=94.8875, so Δ=169/80=2.1125.

Running these two plans on different days is a different calculation. Its mean physical system cost is 99.275, not 94.8875. Convexity makes supply cost at the average load smaller than the corresponding average supply cost. A mean load therefore cannot automatically be interpreted as either an executable daily schedule or the expected cost of randomized daily operation.

The unit of convexification matters. A hull of whole fleets retains each component plan's shared-charger feasibility. A relaxation based on separate duties can have a different feasible region and bound.

Source: `paper/latex/exact_results.tex`; `paper/latex/model_theory.tex`.

## What the support theorem establishes

Under the manuscript's common feasible-set, compactness and duality/attainment qualifications, an admissible own marginal price gives

    r(x;p) ≥ c(x)+F(e(x))−CH ≥ D−CH.

A positive physical–hull gap rules out own-price support. Zero gap permits support under the stated qualifications. Where supply admits several prices, existence of support concerns the full admissible price set; one unfavorable solver-selected multiplier cannot exclude all others.

The planning gap and regret are different. At a hull-optimal common price, the total lost opportunity can be allocated differently between fleet and supply. At the physical plan's own marginal price, supply lost opportunity is zero and the fleet bears the regret. These accounts alone do not create a payment institution or prove budget balance.

Source: `paper/latex/model_theory.tex`.

## What is distinctive, and what is prior art

General linear-price support, participant convexification, duality and lost-opportunity accounting are established theory. Entire feasible schedules as columns, self-scheduling pricing oracles and column generation for convex-hull prices also have direct precedents. Ramping constraints and bus participation in electricity auctions are not new by themselves.

The plausible narrow contribution is a physically explicit construction with endogenous bus assignments and compulsory full replenishment, plus precise conditions and participant-rights distinctions. The source check is bounded, not an exhaustive novelty clearance, and supports no “first” claim. Hreinsson et al. was inspected only at abstract level; absence of a whole-owner result there is unverified.

Small exact examples demonstrate possibility. They do not measure prevalence, calibrated losses, operational savings or the performance of a scalable new algorithm.

Source: `research-20261028/paper_core_verification/PRIOR_ART.md`; `research-20261028/paper_core_verification/STATE.md`.

## Completed capacity/fee characterization

The 28 October result varies terminal charging power K and positive per-vehicle fee f within the lossless two-service model. For 20<K≤30, let l=30−K and d=K−20. Its physical–hull gap is positive exactly when

    max(0,(2/5)d(l−5)) < f < 2d.

K is terminal power, not battery capacity; the terminal window lasts one hour. Boundary, zero-fee and infeasibility cases have separate handling. The result shows that charging flexibility and vehicle cost jointly determine support. Increasing charging capacity can create a support failure while never increasing optimal system cost. It does not imply that better chargers worsen welfare.

The completed implementation check matched all 20 predeclared exact cases, including infeasible and zero-gap cases. The derivation supplies the continuous-domain proof; finite agreement qualifies implementation. These cases are not a statistical sample of fleets.

Source: `research-20261028/paper_core_verification/RESULTS.md`.

## Why ownership matters in replication

The manuscript replicates service pairs and charging resources while scaling supply curvature. The physical planning gap is at most 5/n and tends to zero. Along n=40k+1, absolute whole-owner regret tends to 351/40 rather than zero. One owner can coordinate a deviation of its entire fleet.

If each owner instead controls one service pair with reserved connectors, each owner's regret is at most 20/n. These individual incentives vanish. Per-bus and relative whole-fleet regret also vanish in this family. Thus approximate aggregate convexity does not by itself answer the question about an absolute deviation gain for one owner controlling the aggregate.

Reserved resources make unilateral deviations well defined. Separate owners sharing an unallocated connector need an explicit rights or congestion model before their deviation sets can be assumed independent.

Source: `paper/latex/exact_results.tex`.

## What the public case leaves unknown

The manuscript uses one 37-service public timetable in two separate one-depot variants. Scenario energy, charging and monetary assumptions are partly synthetic; these are not two independent timetable samples.

The nonlinear depot-15 bounds are

    429.22 ≤ CH ≤ D ≤ 512.77,
    0 ≤ Δ ≤ 83.55.

The interval includes zero, so support failure at the public optimal fleet remains unresolved. A feasible fleet establishes an upper bound, not optimality. Its positive regret would establish an incentive for that incumbent, not automatically the optimal fleet. The flat-price case cannot exhibit a physical–hull objective gap because its objective is linear over the energy/cost pairs.

Source: `paper/latex/public_case.tex`; `research-20261028/paper_core_verification/STATE.md`.

## Conventional recovery: a strong control matters

Independent fixed-duty F delivered all eight tested cases. Full discovery N and simple diving D each strictly delivered four; all their failures occurred in the larger 24-service cases. Those failures were selection-policy failures rather than proof of physical infeasibility, because F supplied feasible fleets.

Ordinary joint finite-bank completion delivered every tested assignment, but no improved larger-case retained value. Its approximately 0.225% mean paired grid-electricity improvement is neither total-bill savings nor universal realized-energy savings. On one smaller case the grid objective improved while realized electricity cost increased.

This closed learned selection acceleration for those tested finite banks. It does not certify omitted routes, unrestricted physical optimality or nonlinear/V2G decisions. End-to-end costs include discovery and physical admission, not only the final native optimization call.

Source: `research-20261027/conventional_recovery_continuation/RESULTS.md`.

## Learning pilot: information value without neural advantage

This synthetic study used eight evaluation timetable groups with eight contexts per group. Its 768 strict physical deliveries are repeated method/context assignments, not 768 independent instances.

Conditional background information improved on the unconditional policy by about 0.995% mean paired electricity cost. The fixed-route conditional reference matched the joint-routing reference, so the study demonstrated no additional routing-value mechanism.

Quadratic ridge had the lowest expected cost among fitted methods: 71.352922. The conditional-mean reference was 71.276929; the larger neural MSE model reached 71.368882 and the same-size decision-focused model 71.621344. Constant operations of 400 are excluded. The remaining reference headroom above quadratic ridge was only about 0.105% in the study's paired unconditional-electricity units.

A wider MSE network improved over the smaller network in seven of eight group means. Capacity therefore mattered in this current pilot. A separate privileged noiseless diagnostic demonstrated bounded interpolation, but not generalization or convergence of every production model. Main MSE fitting hit the 500-update ceiling. The old GNN belongs to a different task with small architecture, incomplete economic inputs, incumbent-membership supervision and unknown convergence. The current pilot cannot retroactively resolve that diagnosis, and neither study establishes that all larger models would fail. The current limit is the absence of an advantage over strong controls and of demonstrated extra routing value, not proof of universal model adequacy.

The decision-focused recipe used a finite-bank surrogate and excluded epoch 0 from checkpoint selection. Its loss supports closing that tested recipe without claiming that every decision-focused method fails. Increasing width alone would not establish a contribution beyond strong controls.

Source: `research-20261027/grid_information_pilot/RESULTS.md`.

## Completed 29 October extension: what survives richer choices

The written [proof](PROOF.md) supplies the continuous-domain claims. Independently written raw physical enumeration matched the analytic implementation in all 14 prospectively fixed cases; all 17 negative controls were rejected and the arithmetic smoke passed. There were no failed, late, missing or unattempted cases. This qualifies the exact-model implementations; it is not statistical replication or fleet-population evidence. See [RESULTS.md](RESULTS.md).

**An old plan cannot be rescued just by adding alternatives.** Retain the same supply function and let Z=X∪Y enlarge the old complete-plan set. At any unchanged price, the cheapest alternative can only become cheaper, so a retained plan's regret cannot decrease. Nevertheless a newly admitted plan can become a supported optimum. Global disappearance of the gap concerns the new optimum, not rehabilitation of the old one.

**A useful sufficient survival condition** is min(D_X,D_Y)>CH_X. The enlarged hull cannot exceed the old hull, while every new or old physical plan still costs more than that old bound. The converse shortcut fails: D_Y≤CH_X is necessary for erasure, but not sufficient.

**A sharper dual certificate** uses an attained old hull-dual price p*. If every added plan satisfies c(y)+p*·e(y)≥V_X(p*), the old hull value is preserved. Erasure then requires one added plan to make both the fleet bill inequality an equality and the supply Fenchel inequality an equality: p* must also be a supply subgradient at that plan's load. If the added-plan bill inequality instead has a uniform strictly positive margin ε, the expanded gap is at least min(old gap,ε)>0. For strictly convex supply, the two equalities require implementing the old hull-optimal projected load and operating cost. These conclusions assume the compactness and duality/attainment conditions in the proof; arbitrary expansions need not satisfy the certificate.

**Movement-only expansion preserves this example.** Keep the original services, battery20 buses, fees, charging windows and power, full refill and no V2G. Permit extra movements with nonnegative energy and extra operating cost, without adding energy recovery, inventory transfer or charging access. Every feasible added plan is dominated by an old plan with no greater operating cost or energy in either window. The same replacement argument applies to hull mixtures. Therefore D=97, CH=7591/80 and gap169/80 remain unchanged for this stated class. This does not cover arbitrary extra duties, changed services or equipment.

**Changed equipment can erase the obstruction.** Retain old buses and add battery-B buses at fee7 under the proof's availability and charging assumptions, with 20≤B≤30. Support is restored exactly when B≥(55−√95)/2, approximately22.6266. At B=25 the new one-bus plan charges (5,25), fully replenishes and attains D=CH=92, supported at price (5,5). It starts at25, uses15 on A, charges5 early, uses15 on B and charges25 terminally. The old one-bus plan still has regret13 at its own price (6,4).

**The fee-8 counterexample prevents a tempting shortcut.** For the added battery25 bus at fee8, D=93 lies below the old CH94.8875, but the new CH is92.95. Gap0.05 and own-price regret1 remain. The enlarged hull also improves, so beating the old hull physically does not settle support in the enlarged model. For battery25 and fees h≥7, erasure occurs only at h=7. The proof supplies the fuller battery/fee region and retains planner ties; a selected optimum's regret is not necessarily every optimum's regret.

These are a physical stability class, a changed-equipment region and a counterexample within the declared synthetic model. They establish no unrestricted larger-EVSP theorem, calibrated welfare effect, public-fleet prevalence, V2G result or new ML advantage. General support/convex-hull theory remains attributed prior art.

## Study questions and answers

1. **Why impose full terminal replenishment?** To charge the modeled horizon for replacement energy rather than letting it consume free initial inventory. It does not make service assignments divisible.
2. **Why are 97, 94.8875 and 13 different?** They are respectively physical optimum, convexified planning optimum and fixed-price deviation gain at the physical optimum's marginal price.
3. **Can randomizing daily schedules implement CH at the same expected cost?** Generally no. CH evaluates supply cost at the mean load; random daily operation incurs the mean of physical supply costs.
4. **Does one large regret at a solver price prove no supporting price exists?** Not with nonunique prices. Support existence requires considering every admissible candidate price, or an appropriate certificate over that set.
5. **Does Δ→0 make all incentives vanish?** Not necessarily for absolute whole-owner regret. The replicated example separates it from vanishing individual and per-bus incentives.
6. **Has the public case established support failure?** No. Its certified gap interval includes zero.
7. **Did larger neural capacity help?** Yes in the new pilot. It still did not beat the best fitted classical baseline, and the old GNN remains a separate unresolved diagnosis.
8. **If a new physical plan beats the old CH, is the enlarged model supported?** Not necessarily. Compare the enlarged model's D with its own CH; both may decrease. The verified fee-8 extension has D93 below old CH94.8875, yet new CH92.95 and positive gap0.05.

## What would materially strengthen the research

A stronger analytical contribution would characterize preservation or disappearance of the obstruction within richer physically admissible duty sets, with precise assumptions and meaningful counterexamples. A stronger operational contribution would specify the participant and tariff institution, provide independent timetable evidence and obtain informative global support bounds. A stronger ML contribution would identify a valuable attainable decision beyond competent classical controls and demonstrate complete end-to-end gains.

The current state supports an analytical mechanism, the completed capacity/fee characterization and the completed support-extension qualification. Practical prevalence, calibrated magnitude, public optimal-fleet support and a competitive neural method remain absent or unresolved. The extension's proof and bounded exact qualification do not resolve those external-evidence questions.

Source: `research-20261028/paper_core_verification/STATE.md`; `research-20261028/paper_core_verification/RESULTS.md`; `paper/latex/main.tex`.
