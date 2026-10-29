# EGG self-study guide

Self-study companion to the **Understanding EGG** learning deck, updated 29 October 2026. The guide covers the public support certificate, the common-loss extension and the learning results. It explains existing evidence and is not an independent reproduction. Written proofs establish continuous-domain claims; finite exact checks qualify implementations. Sources are repository-relative to `ml-prediction-20261017`. See the support extension's [proof](PROOF.md) and [results](RESULTS.md).

## Start with the question

A bus fleet can minimize total operating and electricity supply cost while wanting to change its schedule at the marginal electricity prices associated with its own load. The current research establishes this possibility in explicit analytical models and one idealized public timetable. It has not established how common or economically important it is in operating fleets.

Read the guide in order. First explain the three objectives without equations; then work through the numerical example; finally interpret the experiments and open questions.

For the current mathematical account, use `paper/focused-theory-20261029/main.tex`
and its included sections. The older `paper/latex/` references below retain the
history of the original examples; the focused draft contains the later results.

| Question to study | Current source | What to take from it |
|---|---|---|
| What exactly does a price support? | `framework.tex` | One complete-fleet participant and a fixed tariff; the hull and strategic-reset questions differ. |
| Which assignments must be retained? | `heterogeneous.tex`, `lossy.tex`, `full_lossy_projection.tex` | Full lossy polygons retain finite cycling; the smaller efficient frontier requires monotone objectives. |
| Can more feasible alternatives remove the failure? | `complete_graph_extension.tex`, `strict_curvature_robustness.tex` | They can matter, but the obstruction can survive complete compatibility and local parameter changes. |
| Is the public result global? | `public_case.tex`, `exact_energy_extension.tex` | Yes within each separately specified model; the two consumption laws have different certificates. |
| Why did learned methods not win? | `research-20261027/grid_information_pilot/RESULTS.md` | Greater neural capacity helped, but the best fitted classical baseline remained stronger in that study. |
| What is still missing for a strong paper? | The final section of this guide | Significance, wider applicability, calibration and a substantive ML result remain separate questions. |

TeX filenames in this table are relative to `paper/focused-theory-20261029/`.

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
| V2G | Vehicle-to-grid export. The analytical sections treat lossless and common-efficiency models; the public support certificate and inspected learning experiments are charge-only. |

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

Nor must the obstruction be a missing energy load. In the two-batch class below, the attainable early-load set is an entire interval. Every intermediate load can be dispatched using enough buses, but the cheapest operating cost drops in steps as service pairing becomes possible. The hull interpolates **load and operating cost together**. At a physical intermediate load, its interpolated operating-cost label may still be unattainable. Continuous charging and a convex load-only set therefore do not settle support.

Source: `paper/latex/exact_results.tex`; `paper/latex/model_theory.tex`.

## What the support theorem establishes

Under the manuscript's common feasible-set, compactness and duality/attainment qualifications, an admissible own marginal price gives

    r(x;p) ≥ c(x)+F(e(x))−CH ≥ D−CH.

A positive physical–hull gap rules out own-price support. Zero gap permits support under the stated qualifications. Where supply admits several prices, existence of support concerns the full admissible price set; one unfavorable solver-selected multiplier cannot exclude all others.

The planning gap and regret are different. At a hull-optimal common price, the total lost opportunity can be allocated differently between fleet and supply. At the physical plan's own marginal price, supply lost opportunity is zero and the fleet bears the regret. These accounts alone do not create a payment institution or prove budget balance.

Source: `paper/latex/model_theory.tex`.

## What is distinctive, and what is prior art

General linear-price support, participant convexification, duality and lost-opportunity accounting are established theory. Entire feasible schedules as columns, self-scheduling pricing oracles and column generation for convex-hull prices also have direct precedents. Ramping constraints and bus participation in electricity auctions are not new by themselves.

The strongest current candidate contribution is an explicit assignment-dependent **joint load–operating-cost projection**. For a restricted two-batch class, one classical matching value per fleet size determines an exact polygon with at most five vertices, even with common conversion losses and finite sequential cycling. This preserves arbitrary period-price responses, including negative prices. Monotone objectives need only a smaller efficient frontier, with at most two segments per fleet size. The result avoids enumerating complete fleets under its specific physics; it is not a new matching, generic aggregation or price-support theorem.

Joint EV scheduling, V2G and electricity pricing already appear in prior work. Zhou, An and Schmöcker model bus connections with charging and export; Wu and colleagues connect scheduling and distribution-grid prices. Al Taha and Bitar give lossy-storage reformulations. Our distinction must therefore be the specific physical classification and its consequences. The source check is bounded and supports no “first integration” claim. See the focused draft's related-work comparison and `LOSSY_NOVELTY_REVIEW.md`.

Small exact examples demonstrate possibility. They do not measure prevalence, calibrated losses, operational savings or the performance of a scalable new algorithm.

Source: `research-20261028/paper_core_verification/PRIOR_ART.md`; `research-20261028/paper_core_verification/STATE.md`.

## Completed capacity/fee characterization

The 28 October result varies terminal charging power K and positive per-vehicle fee f within the lossless two-service model. For 20<K≤30, let l=30−K and d=K−20. Its physical–hull gap is positive exactly when

    max(0,(2/5)d(l−5)) < f < 2d.

K is terminal power, not battery capacity; the terminal window lasts one hour. Boundary, zero-fee and infeasibility cases have separate handling. The result shows that charging flexibility and vehicle cost jointly determine support. Increasing charging capacity can create a support failure while never increasing optimal system cost. It does not imply that better chargers worsen welfare.

The completed implementation check matched all 20 predeclared exact cases, including infeasible and zero-gap cases. The derivation supplies the continuous-domain proof; finite agreement qualifies implementation. These cases are not a statistical sample of fleets.

Source: `research-20261028/paper_core_verification/RESULTS.md`.

## Fixed shared connectors and heterogeneous assignments

The richer two-batch theorem keeps one early connector of power K for one hour and one terminal connector of power H for one hour. These resources do not scale with fleet size. Here K means **early** power; in the preceding two-service characterization K meant terminal power. Buses have common battery capacity B, start and end full, and service energies lie in (0,B]. Services occur in two batches around the common charging windows. Permitted transitions consume no time, energy or operating cost, and each service retains a standalone-bus option.

An allowed bipartite successor graph declares which first/second services can share a bus. A pairing with energies a and b needs at least [a+b−B]+ early energy and can buy at most a. Let r_m be the minimum sum of those lower bounds among allowed matchings of size m, and ν the maximum matching size. With total service energy S, define

    L=max(0,S−H),   U=min(sum of first-batch energies,K).

At cardinality m the exact physical early-load interval is [max(L,r_m),U], with operating cost f(2n−m), whenever its lower endpoint does not exceed U. An empty interval is infeasible; clipping its lower endpoint to U would invent a schedule. Serial charging implements each permitted early and terminal quantity because the relevant buses share their respective windows. Full refill fixes late load at S−E.

The thresholds r_m are nondecreasing and discretely convex on m=0,…,ν. For positive fee, the hull's lowest operating-cost frontier starts at the clipped left endpoint L, passes through retained assignment thresholds, and ends with a horizontal segment up to U. With strictly convex supply along (E,S−E), find its unique hull-minimizing E. The gap is zero exactly when that E is L, a retained physical threshold, or on the final horizontal segment. Strictly between retained thresholds the gap is positive. Keep intermediate physical thresholds even when adjacent hull edges are collinear. At zero fee, every feasible load has zero operating cost and the gap is zero.

This projection and support criterion apply to an arbitrary fixed allowed graph under the stated physics. Only the shortcut using the smallest energies and opposite-order pairing requires complete crossmatching. Nonzero transition consumption or different windows can change total energy or serialization and are outside this result.

The separate 14-case exact qualification covers complete crossmatchings using raw SOC enumeration and serial witnesses, including infeasibility, zero powers/fees and continuous ties. All 24 negative controls and the smoke check passed. It includes a physical collinear threshold E=20 and a clipped physical boundary E=5. It does not numerically qualify every sparse graph. The older eight-case qualification concerns a different policy with resources scaled by n; keep its denominator and hardware assumptions separate.

Sources: `paper/focused-theory-20261029/heterogeneous.tex`; `research-20261029/shared_connector_support/RESULTS.md`; `research-20261029/public_support_resolution/ALLOWED_GRAPH_EXTENSION.md`.

## Why ownership matters in replication

The manuscript replicates service pairs and charging resources while scaling supply curvature. The physical planning gap is at most 5/n and tends to zero. Along n=40k+1, absolute whole-owner regret tends to 351/40 rather than zero. One owner can coordinate a deviation of its entire fleet.

If each owner instead controls one service pair with reserved connectors, each owner's regret is at most 20/n. These individual incentives vanish. Per-bus and relative whole-fleet regret also vanish in this family. Thus approximate aggregate convexity does not by itself answer the question about an absolute deviation gain for one owner controlling the aggregate.

There is a useful qualification. For a fixed family with bounded load diameter R, supply gradient Lipschitz constant L, and strong-convexity constant μ bounded away from zero, a physical planner's own-price regret is at most Δ+LR√(2Δ/μ). It therefore vanishes as Δ does. This follows from classical convex analysis; it is not a new pricing theorem. Our replication changes the family: load diameter grows with n while supply curvature decreases as 1/n. Those changing constants allow the absolute whole-owner incentive to persist. At the hull price, the fleet's regret is exactly Δ minus the supply Bregman difference; moving to the physical plan's own price changes that allocation.

Reserved resources make unilateral deviations well defined. Separate owners sharing an unallocated connector need an explicit rights or congestion model before their deviation sets can be assumed independent.

Source: `paper/latex/exact_results.tex`.

## The public case: a resolved sign, a small model-specific gap

The manuscript uses one 37-service public timetable in two separate one-depot variants. Scenario energy, charging and monetary assumptions are partly synthetic; these are not two independent timetable samples. The certified model admits the pinned descriptor's finite movement graph, fixed travel-leg times and declared depot/terminal charging windows. Charging inside those windows is continuous. A complete directed travel matrix does not prove completeness over arbitrary unlisted paths, extra depot visits, retiming or other charging locations. The support result is global within the declared graph and fleet cap.

For the nonlinear depot-15 ideal model, the new exact certificates establish

    CH ≤ 441.142238 < 441.532912 ≤ D ≤ 441.532913,
    Δ ≥ 0.390674.

These are conservative outward displays of exact rational certificates. The gap shown is a valid lower bound from subtracting an upward hull endpoint from a downward physical endpoint. The hull upper comes from a feasible mixture of two separately admitted physical plans. An independent checker first verified a complete 303-node binary tree, then accepted a refinement with 72 new descendants and all original regions retained. A qualified physical floor excludes fleets of three or more buses. The physical optimum is now enclosed within 0.000001 model units. Its exact value and the exact hull optimum remain unknown.

A separate local portable package has now verified the complete retained result in one fresh standard-library Python process, with no solver. It rechecked both physical plans, the fixed mixture, fresh fleet exclusions and one combined 375-node proof tree. The complete construction/check took about 33 seconds. This is author-run verification on the same host, not external replication; the bundle remains local pending redistribution review. The manuscript's certificate index gives the exact input/source identities and verification recipe.

A cheaper fixed-price response had already proved that the protected incumbent was unsupported at its own prices. That alone did not settle global support. The new strict separation now proves that no globally optimal physical fleet in this declared model has own-price support, under the stated price/duality qualifications. The admitted physical upper remains a feasible plan, not an assertion that its exact global optimality is known.

The certified gap lower is small in synthetic cost units. It establishes a sign and a mechanism in one idealized timetable variant, not operational prevalence, calibrated losses, a large practical effect, or an ML advantage. A separate exact fee argument shows that every vehicle fee at least the nominal 100 preserves the positive lower-gap guarantee; a sufficient open interval also extends below 100. This is fee stability with the physical model held fixed, not robustness to reserve, losses, access or delays. The flat-price variant still cannot have a physical–hull objective gap because its objective is linear over the energy/cost pairs.

Two further exact checks now bind the model to its source construction. All directed time/distance triangle inequalities passed on the five public locations. A separately written comparison verified all 37 services, 1370 canonical movement modes and 2648 legs, including missing modes that should be time-infeasible. That removes an input-correspondence concern. It does not prove that arbitrary extra walks or retimed waits are dominated: the exact stored energy law and charging access also matter. Tiny changes can cross a battery or charging-feasibility threshold, so the positive gap alone is not permission to smooth over rounding. The public conclusion remains global within its declared graph.

The exact certificate index maps each inequality to its immutable evidence and checking source. These checks were independently formulated within this project. The standalone solver-free bundle has completed its local author-run verification; reader redistribution remains pending, and no independent external replication is claimed.

Sources: `research-20261029/public_support_tree/attempt01/results.json`; `research-20261029/public_price_witness/RESULTS.md`; the current focused-theory public-case discussion. The price-witness RESULTS describes its own earlier package boundary as unresolved; the subsequent independently checked tree resolves the sign.

## A broader public model now has its own certificate

The original result used stored floating-point consumption values as exact
coefficients. We separately defined a model using exact additive travel and
waiting formulas, keeping the timetable, fleet/resources and supply cost fixed.
This distinction matters: even tiny coefficient changes can affect feasibility.

Fresh checks give **441.532912 ≤ D ≤441.532913**, **CH ≤441.142238**, hence
**D−CH ≥0.390674** for the new model too. The displayed numbers coincide, but
the exact fractions differ. The new argument did not assume the old gap survived.
Two reconstructed physical plans and the complete retained branch partition
were checked under the new energy law. A diagnostic-key error stopped the first
final comparison; a separately checked summary-only consumer completed it,
without repeating those successful calculations. The failed attempt remains.

Why does this extend the opportunity set? In the defined directed-arc model,
time and energy triangle inequalities let us shorten a noncharging detour, or
stay at the selected depot instead of making intermediate excursions. We can
retain the original charging times and curtail purchases when the battery is
full. This preserves feasibility while decreasing each period's purchases.
Thus arbitrary finite walks and continuous waiting cannot beat the canonical
model's physical or convexified planning values under monotone supply costs.

The proof needs the exact waiting law, complete canonical access, one charging
depot, nonnegative consumption and ideal charging. It does not certify that
every paired time/distance arc is an actual road path, add public V2G, estimate
prevalence or establish calibrated savings. See `exact_energy_extension.tex` and
`public_exact_energy_comparison/RESULTS.md` for the precise statement.

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

These are a physical stability class, a changed-equipment region and a counterexample within the declared synthetic model. This particular implementation qualification establishes no unrestricted larger-EVSP theorem, calibrated welfare effect, public-fleet prevalence, V2G experiment or new ML advantage. General support/convex-hull theory remains attributed prior art.

## Lossless V2G: persistence and restoration

The newer V2G result is analytical, not an implemented learning experiment. It permits lossless bidirectional early charging, uniform acceptance, compulsory full terminal refill, and the same posted rate for purchases and exports within an interval. Supply must be defined on every admitted signed net load, or through an explicit background-demand model. Losses and asymmetric buy/sell tariffs require different analysis.

Connector use depends on gross energy. Buying 1 and exporting 1 has net load 0 but consumes 2 units of connector throughput. Checking only the absolute net total would create fictitious capacity. Full terminal refill still charges the horizon for energy replacement; export does not create free initial inventory.

V2G can preserve the obstruction: in the two-by-two example with early power K=15 and terminal power H=49, the relevant thresholds stay 0,0,9, so the same positive gap persists. More battery actions need not change the joint load–cost frontier.

It can also restore support. In the stated three-by-three example, one assigned bus buys 1 early while another exports 1. Net early energy is 0, gross throughput is 2, and all buses finish full. Under that example's supply function, the charge-only gap 1/4 disappears and D=CH=67/5, supported at prices (1/5,1/5). The mechanism changes when assigned inventories are available; it does not cancel connector time.

Paid idle buses need an explicit availability rule. With at most 2n buses total, deleting matching edges and using standalone service buses already represents their entire load–cost projection. In the examples with H=S, fleets above 2n are also dominated by cheaper standalone fleets at the same load. This uncapped dominance is not general when H>S: extra idle inventory can permit useful negative early net load. Idle buses are therefore not universally irrelevant.

Source: `paper/focused-theory-20261029/v2g.tex`. These are exact statements for declared ideal physics and settlement, not field evidence or a qualified V2G software result.

## Common conversion losses: why two load coordinates matter

Let alpha be charging efficiency, delta discharging efficiency, C early grid purchases and X early grid exports. The battery gains alpha*C−X/delta, while the grid sees E=C−X. If total service energy is S and every bus finishes full, terminal purchases satisfy

    L = S/alpha − E + (1/(alpha*delta)−1)*X.

The same early net load can therefore require different terminal purchases. Replacing S by S/alpha in a lossless formula misses export losses and gross connector use.

For a fixed matching, let R be its total mandatory early battery recharge. The least export needed at early net load E is max(R/alpha−E,0). Substituting that quantity above produces a continuous curve with at most two straight pieces. Inventory, gross early throughput and terminal capacity determine its feasible endpoints. Among matchings with the same number of paired services, the matching minimizing R has the best such curve.

Thus one classical matching value per cardinality still describes the efficient joint load–cost set. This smaller curve does **not** describe every physical allocation: battery-neutral charge/export cycles can create dominated points. For coordinatewise nondecreasing supply cost, removing those points preserves the physical and hull planning values. Negative prices may require those omitted alternatives. At zero prices some removed plans can tie, so the smaller reduction gives response values without enumerating all responses.

The efficient-frontier theorem has an independent proof review. Ten prospectively fixed cases also matched a separate raw SOC/sign-polytope enumeration, with complete frontier-segment attainment and physical replay. This is a finite implementation qualification, not ten independent real fleets, empirical validation, or public-case V2G. See `lossy_projection_qualification/RESULTS.md` and the focused draft's common-loss section.

There is now a stronger **complete projection**, under explicit ideal cycling
rules. For each matching size, keep total early purchases C and exports X.
Let Q=alpha*C−X/delta be battery exchange. Five linear inequalities suffice:
mandatory purchases C>=r_m/alpha; X>=0; the lower and upper inventory/refill
bounds on Q; and shared gross use C+X<=K. The resulting polygon has at most
five vertices. It maps exactly to early net load, terminal refill and vehicle
cost, including the alternatives the efficient curve discarded.

The constructive proof matters. First realize the required Q with one action
direction per bus. Any residual totals are battery-neutral cycles, with exported
energy alpha*delta times purchased energy. Split them into finitely many safe
charge/discharge pairs on one available bus, then serialize all actions on the
single connector. No bus charges and discharges simultaneously. This construction
requires unrestricted finite switching, no minimum session or cycling cost,
adequate common power acceptance and whole-window availability. Cycle count can
be large. A real degradation model or finer time-varying tariff needs new analysis.

The full polygons preserve arbitrary period-total objectives and negative-price
queries; convex objectives use ordinary convex optimization on each polygon and
their complete-plan hull. The smaller efficient curve still needs monotonicity.
The full theorem has independent analytical review and a separate eight-case
exact implementation qualification: all34 partial matchings,20 cardinality
layers and85 vertex schedules were retained, including infeasible layers.
All12 corruption controls behaved as expected. Independent raw bus polygons
and serial physical replay agreed with the formula. These small cases are
implementation checks, not a population or speed benchmark. They do not turn
the public timetable into a V2G experiment or establish an ML advantage. See
`full_lossy_projection.tex` and `full_lossy_polygon_qualification/RESULTS.md`.

A concrete negative-price example shows the distinction. With one paired bus,
B=1, service energies3/4 each, charging efficiency1/2, export efficiency1,
early budget2 and terminal budget3, a neutral cycle can buy1/3 and export1/6
without changing stored energy. Later early charging buys3/2. Total early net
load is5/3, terminal load3/2 and bus cost2. At prices(-3,1), the total private
score is−3/2. Keeping only the efficient curve gives−1. Both values are exact.
The negative price rewards an otherwise wasteful cycle under this ideal
settlement model. Because this is a linear price query, physical and hull
minima agree: it is **not another positive support gap**.

Two useful extensions also have independent proof review. Charging and export
may have different common power limits: replace the gross-energy bound by
the exact occupied time C/K_charge + X/K_export <= 1. Common linear wear
charges on purchased, exported and terminal energy can remain in the joint
cost coordinate. With lossless conversion, equal net loads may still have
different wear because gross cycling differs; net energy alone loses that cost.
The constructive early schedule needs at most N+2*ceil(2*alpha*K_charge/B)
actions, plus at most N terminal actions. Allowing at least this many preserves
the complete aggregate set; it is not a minimal count or runtime claim.
These extensions are analytical. The eight implementation cases used equal
directional power and no wear; switching delays and state-dependent battery
degradation remain outside the proof.

## Why the two-batch assumptions matter

The supply assumption matters just as much. Convex network dispatch does not
automatically become more costly when load increases at a particular location.
Congestion can make extra withdrawal relieve a bottleneck and replace expensive
generation with cheaper generation elsewhere. This is the established negative
nodal-price phenomenon, even with positive generator offers.

An independently checked three-bus example uses strictly increasing quadratic
generation costs and a constrained transmission line. For an extra depot load
x between 0 and 1, its exact incremental dispatch cost is −0.89x+0.05x²: convex,
yet decreasing throughout that interval. Therefore positive generator costs
alone do not justify discarding componentwise larger fleet loads. The smaller
common-loss frontier must check its load-monotonicity premise; the new full
polygons retain those alternatives under their explicit cycling assumptions.
This is an ideal DC-network illustration, not a new negative-price discovery,
an AC-grid qualification or a change to the public timetable's synthetic cost.
See `network_monotonicity.tex` and Baker–Gangammanavar (2024), Section V-B.

Zero transition energy can be relaxed in one controlled way. If every paired duty performs the same compulsory energy-consuming task after early charging, total consumption is fixed within each matching cardinality: S+m*d. The same matching statistic gives the full polygon, or at most two efficient segments under monotone objectives, with that extra energy included in terminal refill. The graph must exclude pairs whose B service plus transition cannot fit in a full battery. This abstract extension has proof review and one literal in the separate full-polygon qualification; arbitrary road transitions remain outside it.

Varying transition energy changes the answer. In a charge-only example with A and B energies (13,1) and batteries20, the identity matching needs6 early units and consumes28 overall. Cross transitions each consume6 extra units: that matching needs0 early units but consumes40 overall. Choosing only the smallest early requirement loses the identity's efficient charging branch. With a linear unit electricity price and any positive bus fee, allowing singleton duties still does not rescue that shortcut. Total energy has become assignment-dependent. This is a scope counterexample, not a measured public-route effect or a new hardness claim.

The proved reduction concerns duties containing at most one service from each of two batches. A third batch can already create a different problem: if buses cannot charge between batches, each selected triple of service energies must fit in one battery. With exactly enough total battery inventory, the triples must all sum exactly to capacity. This contains the classical strongly hard Numerical Three-Dimensional Matching problem, even with every transition available and enough terminal charging afterward.

The draft gives the short reduction and its proof. This is a boundary explanation, not a new EVSP hardness claim, evidence that every three-batch case is difficult, or a reason to prefer ML. It explains why two independently good adjacent matchings need not combine into battery-feasible complete duties.

There is a stronger analytical boundary: k independent two-by-two assignment
blocks can create **2^k efficient physical charging branches at the same fleet
size** when connection energy varies. Each branch matters for some monotone
convex supply objective. Yet all their corner points can lie on one straight
hull edge and share a single supporting price. Many physical alternatives
therefore need not mean a complicated hull or difficult price calculation.
The construction uses growing binary-encoded energy magnitudes and has a compact
symbolic description; it is not a hardness or ML-advantage result.
For the same complete family, a smooth monotone convex supply objective has
an exact physical–hull gap of **9/(2K)>0**. Thus support failure can survive
all those feasible alternatives. The gap shrinks as this family's K grows;
this proves neither a uniform loss nor that adding alternatives never helps.

The construction can also admit a **complete assignment graph with every
perfect matching physically feasible**. Added connections require enough
replacement energy that a simple assignment-potential inequality places them
above the old minimum. Enlarging terminal capacity makes every matching's
whole charging interval feasible. The exact gap remains 9/(2K), and each
original corner still matters for a suitable convex objective. Thus neither
missing assignment edges nor infeasibility of the added matchings explains
this example's support failure. These connections are compulsory abstract
energy tasks, not geographically realized road routes. The full efficient
frontier may change, and the common windows, fleet cap and scaling resources
remain limitations. The proof was derived and checked independently; no
numerical experiment is claimed.

The obstruction also survives **strictly positive curvature in both charging
periods**. Giving the added connections a small energy margin and the terminal
charger spare capacity makes every perfect matching strictly feasible in the
relevant resource inequalities. With a strongly convex separable objective,
the exact gap becomes 9/(2K)+81/(4M)>0, where M is the construction's reference
total. A continuity argument proves a positive gap in a sufficiently small
admissible relative neighborhood of each fixed finite instance. This removes
flat terminal cost and exact capacity saturation as explanations for that
example. It gives no numerical radius, uniform-in-size guarantee, empirical
road realization or perturbation certificate for the public timetable. The
proof and its physical premises were checked independently.

## Study questions and answers

A tempting computational shortcut also fails: interpolate the number of
matched service pairs first, then apply the charging formulas as though that
fractional fleet were physical. An independently derived one-pair example has
true physical and hull values both equal to 7, yet this shortcut admits 6.75.
The resource bounds combine incorrectly after averaging. This is a false gap
created by a relaxation, not a real support failure. The exact compact baseline
instead mixes the complete feasible endpoints and kinks supplied by the
frontier theorem. It remains small without inventing fractional fleet physics.

1. **Why impose full terminal replenishment?** To charge the modeled horizon for replacement energy rather than letting it consume free initial inventory. It does not make service assignments divisible.
2. **Why are 97, 94.8875 and 13 different?** They are respectively physical optimum, convexified planning optimum and fixed-price deviation gain at the physical optimum's marginal price.
3. **Can randomizing daily schedules implement CH at the same expected cost?** Generally no. CH evaluates supply cost at the mean load; random daily operation incurs the mean of physical supply costs.
4. **Does one large regret at a solver price prove no supporting price exists?** Not with nonunique prices. Support existence requires considering every admissible candidate price, or an appropriate certificate over that set.
5. **Does Δ→0 make all incentives vanish?** With uniformly bounded load range and smoothness, and uniformly positive strong convexity, planner own-price regret does vanish. Our replication changes these constants as the fleet grows, separating persistent absolute whole-owner regret from vanishing individual and per-bus incentives.
6. **Has the public case established support failure?** Yes for the original finite movement graph, and separately for the exact-additive-consumption model with arbitrary finite walks over its paired primitive arcs. Both have fresh certified positive gaps. The latter extension uses a dominance theorem and specified charging access; neither result covers every empirical road option. The small certified gap does not establish prevalence or operational magnitude.
7. **Did larger neural capacity help?** Yes in the new pilot. It still did not beat the best fitted classical baseline, and the old GNN remains a separate unresolved diagnosis.
8. **If a new physical plan beats the old CH, is the enlarged model supported?** Not necessarily. Compare the enlarged model's D with its own CH; both may decrease. The verified fee-8 extension has D93 below old CH94.8875, yet new CH92.95 and positive gap0.05.

## What would materially strengthen the research

A stronger analytical contribution would extend the precise projection and support criteria beyond the declared two-batch physics, with meaningful counterexamples where they fail. A stronger operational contribution would specify participant rights and tariff institutions, provide independent timetable evidence and calibrate the magnitude of the effect. A stronger ML contribution would identify a valuable attainable decision beyond competent classical controls and demonstrate complete end-to-end gains.

The current state supports an analytical mechanism, continuous-domain characterizations, bounded exact implementation qualifications, and a positive global physical–hull gap in one public ideal-model variant. Matching, convex QP/LP, branching and exact certificate checking are classical methods; the public separation is not evidence of ML advantage. Practical prevalence, calibrated magnitude and a competitive neural method remain absent or unresolved. None of the new theory or certificates changes the learning pilot's baseline comparison or resolves the old GNN's model-capacity diagnosis.

Source: `research-20261028/paper_core_verification/STATE.md`; `research-20261028/paper_core_verification/RESULTS.md`; `paper/latex/main.tex`.
