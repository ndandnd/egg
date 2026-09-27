# When marginal electricity prices cannot coordinate electric-bus schedules

## Complete-fleet certificates and a replenished-fleet counterexample

Research draft 0.3 | 27 September 2026 | Analytical extensions independently verified; operational study in preparation

### Abstract

Electric-bus charging combines continuous energy decisions with indivisible service assignments. A smooth electricity supply cost therefore need not admit marginal prices that support a physically implementable fleet schedule. We compare physical planning with the convex hull of complete fleet schedules under the same physical and operating-cost assumptions. A classical convexification argument lower-bounds every physical schedule's regret at its own marginal price. A fully replenished two-service construction has exact physical and convexified costs of 97 and 94.8875 synthetic currency units. Its own-price fleet regret is 13; at the common hull price, fleet lost-opportunity cost is zero and supplier lost-opportunity cost is 2.1125. A modified construction retains a positive gap with a battery reserve, 5% charging loss and one finite connector. Scaling service demand and supply capacity together makes the absolute planning gap vanish, while whole-operator own-price regret need not vanish; per-bus regret does. These results distinguish physical dispatch, mean-load cost and incentive normalization. A complementary synthetic reoptimization diagnostic preserves 44 certified cells and one failed pricing solve from a fixed 45-cell design. Operational prevalence, market calibration and a funded coordination mechanism remain open.

Keywords: electric-bus scheduling; convex-hull pricing; charging coordination; lost-opportunity cost; column reuse; physical feasibility.

### 1. Introduction

An electric-bus operator must deliver mandatory passenger services while choosing vehicle duties and charging schedules. Even when the amount of electricity charged in each interval is continuous, moving a service between vehicles changes a discrete duty structure. Electricity prices can encourage a different charging pattern or fleet assignment, but the resulting pattern changes the marginal system cost that motivated those prices. This raises a question distinct from finding a low-cost schedule under an exogenous tariff: can a realizable fleet plan be a best response to the marginal electricity prices associated with its own load?

This paper studies that question through complete fleet schedules. A complete schedule contains all mandatory services, their assignment to vehicles, physically feasible charging and the associated intrinsic operating cost. Its convexification permits averages of these complete plans. Such an average is useful for lower bounds and pricing analysis, but need not be a daily dispatch. In particular, evaluating a convex electricity cost at the average load is not the same as averaging the costs of physical daily loads.

The economic principle is established in nonconvex market optimization. Our contribution is a transparent fleet interpretation, fully replenished physical counterexamples with explicit resource and efficiency assumptions, and an exact replication family separating cost-gap convergence from whole-operator incentive convergence. The evidence distinguishes exact arguments, numerical optimization and operational assumptions. We also evaluate simple schedule reuse before proposing a learned acceleration. The paper does not claim a new general welfare theorem, a new principle of convex-hull pricing, or a demonstrated learning improvement.

The distinction is practically relevant for interpreting optimization output. A small convexified objective does not by itself establish an implementable low-cost plan. A small system-cost gap need not imply a similarly small incentive at the realized marginal price. A payment equal to a fleet's lost opportunity does not by itself fund the supply side or define a budget-balanced institution. Each statement requires a specified physical model, price and deviation right.

### 2. Relation to existing work

Electric-vehicle scheduling with charging and electricity-related objectives is a developed field. Wu et al. [1] consider multiple depots, time-of-use prices and peak-load reduction, with branch-and-price and trip-chain reuse. De Vos et al. [2] incorporate partial charging and capacitated charging stations. Parmentier et al. [3] develop scalable route and recharge scheduling through column generation, and ten Bosch et al. [4] combine simulated annealing with integer-programming recombination. These works establish important operational and algorithmic precedents. Our central relaxation uses complete fleet plans, which must be distinguished from a master whose columns are individual vehicle duties. Charging fidelity is also consequential: Löbel et al. [12] analyze how charge-curve approximation can distort energy feasibility and model dynamic power under grid limits. Our constant-efficiency constructions therefore make no claim to cover nonlinear tapering.

Bus aggregation and electricity-market participation are also established. Zoltowska and Lin [5] aggregate bus charging constraints into auction bids and disaggregate accepted plans. Maldonado and Saumweber [6] examine pricing rules with electric-vehicle participants; their empirical comparison concentrates on IP and extended locational marginal pricing. We do not describe that comparison as an empirical exact-convex-hull benchmark.

Madani et al. [7] connect nonconvex bids, dual prices and aggregate lost-opportunity compensation. Andrianesis et al. [8] compute convex-hull prices using Dantzig-Wolfe decomposition over complete participant schedules. Hümbs et al. [9] emphasize the importance of complete participant descriptions for equilibrium interpretation. These are direct antecedents for our certificate perspective. Bichler et al. [10] distinguish stability, individual rationality and financial balance; we retain that distinction when reporting fleet and supply accounting.

For repeated optimization, Sugishita et al. [11] compare learned warm starts with strong initialization and column-prepopulation baselines. That motivates a conservative computational question: after retaining replay-valid physical columns, how much useful work remains before a fresh certificate is obtained? An analytic tariff shift is another inexpensive conceptual baseline, although solving its proposal oracle still has a computational cost. The full source matrix records inspected versions and access limits; this focused review is not an exhaustive novelty census.

### 3. Physical and economic model

Let S be the same nonempty compact set of complete physically feasible schedules in every model. A schedule s has intrinsic operating cost c(s) and charging load L(s), measured in kWh per modeled interval. The load vector and cost are continuous on each discrete duty structure; finitely many structures with bounded charging give a sufficient compactness condition. Mandatory service cannot be discarded to improve the objective.

Let F be a supply-cost function defined on the nonnegative supply domain. Assume that its restriction to that domain is proper, closed and convex, and that it admits a differentiable convex extension to an open neighborhood of the feasible fleet-load hull. These global supply-domain assumptions support the conjugate accounting below; the price-support inequality itself uses only convexity and differentiability near the feasible hull. Define h(s)=c(s)+F(L(s)). The physical planner value is D=min h(s). The complete-schedule convexified value CH minimizes c+F(L) over the convex hull of all physical pairs (c(s),L(s)). The planning gap is Delta=D-CH, which is nonnegative. This hull retains within-fleet resource constraints in every component before mixing.

At a posted price p, the fleet response value is V(p)=min over S of c(s)+p.L(s). At a physical schedule's own price p_s=grad F(L(s)), define r(s)=c(s)+p_s.L(s)-V(p_s). This is price-taking regret: the alternative schedule is evaluated while the posted price stays fixed. It is not a strategic bill comparison in which the operator anticipates the change in price caused by its alternative load.

The single-fleet interpretation is deliberate. If independent operators share chargers, a unilateral deviation must specify whether residual physical capacity is reserved, whether capacity rights are traded, or whether congestion is priced. The convex hull of jointly feasible whole-fleet plans cannot silently substitute for each independent operator's unrestricted opportunity set.

### 4. Price-support and accounting diagnostics

The following fleet specialization uses the classical convexification and duality perspective of [7–9]; it is not a new general pricing theorem.

**Proposition 1.** Under the stated common-model, compactness and convexity assumptions, every physical schedule satisfies r(s) >= h(s)-CH >= D-CH. Moreover, D=CH if and only if a physical schedule is a best response at its own marginal price. When D=CH, every physical planner optimizer has that property.

$$r(s)\geq h(s)-{\rm CH}\geq D-{\rm CH}=\Delta.$$

**Proof.** A linear functional has the same minimum over the physical cost-load set and its convex hull. For any hull point (c_bar,L_bar), its linear private objective is at least V(p_s). The supporting-plane inequality gives F(L_bar) >= F(L(s))+p_s.(L_bar-L(s)). Adding these inequalities and minimizing over the hull yields CH >= h(s)-r(s). If r(s)=0, the chain CH >= h(s) >= D >= CH forces equality. Conversely, a physical planner optimizer is also a hull optimizer when the values agree. The directional derivative of the convex objective toward every physical point is then nonnegative, which is exactly the global best-response inequality at its marginal price.

Attainment is essential to the converse. Equality of infima alone need not produce a physical optimizer. Likewise, support of a best-response correspondence does not prove convergence of an iterative rule that selects one optimizer at every price, or uniqueness of that optimizer.

For numerical work, let [L_D,U_D] and [L_CH,U_CH] be valid objective enclosures. The planning gap lies in [L_D-U_CH,U_D-L_CH].

$$\Delta\in[L_D-U_{\rm CH},\; U_D-L_{\rm CH}].$$

A positive lower endpoint is the relevant nonexistence diagnostic. A restricted pool's replay-feasible mixture can provide U_CH, but its objective is generally not a lower bound for the complete hull. An interval crossing zero leaves the sign unresolved. Numerical enclosures conditional on solver and replay tolerances are not formal exact-arithmetic certificates.

For participant accounting, the supplier may choose any nonnegative load vector, independently of the fleet charging-resource limits. At a common price p for which the conjugate is finite, define the nonnegative-load supply conjugate F*(p)=sup over L>=0 of p.L-F(L). Fleet LOC is c(s)+p.L(s)-V(p), and supply LOC is F(L(s))-p.L(s)+F*(p). Their sum is h(s)-[V(p)-F*(p)]. At a physical planner optimizer and a dual-optimal hull price, under strong duality, this sum equals Delta. At the schedule's own gradient price, supply LOC is zero and fleet LOC equals r(s). These statements condition on different prices. Neither identity proves budget balance, truthfulness, voluntary participation or convergence.

$$\mathrm{LOC}_{\mathrm{fleet}}+\mathrm{LOC}_{\mathrm{supply}}=h(s)-[V(p)-F^*(p)].$$

### 5. A fully replenished continuous-charging construction

Two mandatory depot-to-depot services consume 15 kWh each. Service A occurs in hour 0-1 and service B in hour 2-3. At most two identical used buses are available. Each starts and ends with 20 kWh, which is also its battery capacity; the reserve is zero. Charging is continuous and lossless. The early window, hour 1-2, permits 10 kWh in total and 10 kW per bus. The native terminal window, hour 3-4, permits 30 kWh in total and 30 kW per bus. There are enough connectors. No other charging, deadheads, auxiliary load or battery degradation is modeled.

These are explicit synthetic assumptions. The terminal window is part of the physical model, rather than a zero-energy passenger service. An unused bus contributes neither energy nor cost. Every used bus must cover a service. With two unsplittable services there are exactly two unlabeled partitions: one bus serves both, or two buses serve one each.

For one bus, early charge x must satisfy x>=10 to make service B feasible and x<=10 from shared power, so x=10. It charges 20 kWh in the terminal window. For two buses, the bus serving A can charge any x in [0,10] early and 15-x at the end; the bus serving B charges 15 at the end. Every bus finishes at its starting SOC. Both structures therefore purchase exactly 30 kWh. The extra bus cannot donate net initial energy.

![Figure 1](figures/cyclic_energy_accounting.png)

Figure 1. One feasible continuously charged one-bus trajectory. The two services each consume 15 kWh; early and terminal charging add 10 and 20 kWh. The line uses constant consumption and charging rates within each one-hour period, consistent with the stated energy model. Initial and final battery energy are equal. This is an explanatory construction, not a measured bus trace.

For this construction, define the global supply function F(e,l)=a*e+0.1*(e^2+l^2) for all nonnegative early and terminal supply quantities e,l. With total fleet recharge 30, its restriction is G(x)=F(x,30-x). For used-bus cost f=7 and early intercept a=4, the one-bus cost is 97. The two-bus branch has cost 14+G(x), minimized at x=5 with value 99. The physical optimum is D=97.

$$D=97,\qquad {\rm CH}=94.8875,\qquad\Delta=\frac{169}{80}=2.1125.$$

Let lambda be the weight on the one-bus structure. The complete projected hull has 0<=lambda<=1, 10lambda<=x<=10 and intrinsic cost 14-7lambda. These conditions are necessary by convex combination. For lambda<1 they are sufficient by assigning the remaining two-bus component early charge (x-10lambda)/(1-lambda). At lambda=1, the constraints force x=10, which is the physical one-bus point. At fixed x the cheapest mixture uses lambda=x/10. The convexified objective is therefore 104-2.7x+0.2x^2, or 7591/80+(x-27/4)^2/5.

$${\rm CH}=\min_{0\leq x\leq10}\left[\frac{7591}{80}+\frac{(x-27/4)^2}{5}\right]=\frac{7591}{80}.$$

Its minimum occurs at x=6.75 and lambda=0.675, giving CH=7591/80=94.8875 and Delta=169/80=2.1125.

A supporting mixture puts weight 27/40 on the one-bus schedule with load (10,20) and weight 13/40 on the two-bus schedule with load (0,30). Both components individually obey the shared limits and full replenishment. The mean load (6.75,23.25) is not assigned a fractional physical fleet in the interpretation. Randomizing those components on different days costs 99.275 on average, rather than 94.8875; Jensen's inequality explains the difference.

![Figure 2](figures/cyclic_gap_and_prices.png)

Figure 2. (a) Physical branches and the lower-cost boundary of the complete-schedule hull. (b) Fleet and supplier LOC for the same physical planner optimum, evaluated at two different prices. Prices are synthetic currency/kWh and costs are synthetic currency. The physical point and hull minimum are exact rational results. A hull optimizer is a pricing/lower-bound object, not a realizable fractional bus plan.

At the physical optimum, marginal prices are (6,4). Its private objective is 147; two buses charging only in the terminal window have private objective 134. Thus own-price regret is 13. At the hull price (5.35,4.65), both supporting physical components have private objective 153.5. The physical planner's fleet LOC is then zero. Supply LOC is 2.1125, accounting for the whole planning gap. The supply-side calculation uses F*(p)=58.6125, so the common-price dual value is 153.5-58.6125=94.8875.

### 6. Exact parameter checks and evidence quality

The protocol fixed 24 constructed cases before execution: f in {1,3,7,10,15,20} and early intercept a in {0,2,4,6}, holding physics and quadratic coefficient fixed. For each case, the two-bus branch minimizes G(x)=a*x+[x^2+(30-x)^2]/10 on [0,10]; the hull minimizes 2f-f*x/10+G(x). A Fraction-arithmetic driver records both physical schedules and the hull mixture.

An independent implementation reconstructs the same optimization using three physical vertices and quadratic interpolation on the hull edges. It imports no author code and invokes no solver. It checks the full parameter grid, physical coverage, every saved event SOC, individual/shared power limits, exact terminal energy and mixture accounting. All ten deliberate corruptions are rejected. The 24-case grid has 11 positive gaps and 13 exact zeros; these counts describe a fixed analytical design, not a population frequency or a statistical sample.

![Figure 3](figures/cyclic_gap_grid.png)

Figure 3. Gaps on the prospectively fixed analytical grid. Labels are rounded; exact rational values are archived. Fleet cost and early supply intercept vary; service demand, charging windows, shared power and boundary energy stay fixed. Values are synthetic currency. The categorical grid is for mechanism inspection and includes all declared cases, including zeros.

The construction establishes existence under fair boundary-energy accounting. Its operational magnitude remains unknown. The following extensions address reserve, constant charging loss, finite connectors and replication within an exact reference model. Time-dependent travel, nonlinear tapering and operational calibration still require separate qualification; no production-adapter equivalence is inferred from these examples.

### 6.1. Reserve, losses and a finite connector

The nominal point sits on a binding early-power boundary. With the same 20 kWh battery and 10 kW early limit, any positive reserve or efficiency below one removes the one-bus option. When two buses remain feasible, their charging interval is convex and the gap is zero. Adding reserve while also increasing battery capacity by the same amount is an exact SOC translation, but it does not demonstrate robustness at fixed installed capacity.

To examine genuine perturbations, retain battery capacity 20, service energy 15 per trip and the grid-side supply cost F(e,l)=4e+0.1*(e^2+l^2). Let r be the reserve, η the constant grid-to-battery efficiency, P the early power limit and K the power of a single terminal connector. Both windows last one hour. Gross grid purchases total T=30/η for either fleet structure. For 0<=r<=5, define lower early bound l=max(0,T-K), upper bound u=min(P,15/η), and h=max(l,(10+r)/η). The complete two-bus interval is [l,u], and the complete one-bus interval is [h,u]; an interval with lower bound above u is infeasible.

These intervals have explicit connector-feasible realizations. Only A's bus charges early. At the terminal window, use constant aggregate power T-x and serve A's and B's buses consecutively in proportion to their required terminal energy. There is one occupied connector at a time, and every battery finishes full. This assumes zero switching time, constant efficiency and no taper; it is not an assertion about every physical charger.

With r=1, η=19/20, P=12 and K=30, the one-bus optimum buys 220/19 early grid kWh and 20 terminal grid kWh. Its battery trace is 20→5→16→1→20. The early-power slack is 8/19 kWh. The hull mixes that schedule with a two-bus schedule buying 30/19 early and 30 terminal grid kWh, with one-bus weight 453/760. The two terminal sessions occupy 9/19 and 10/19 of an hour. The exact gap is positive:

$$D=\frac{38527}{361},\qquad {\rm CH}=\frac{2987911}{28880},\qquad\Delta=\frac{94249}{28880}\approx3.26347.$$

Strict feasibility and optimization inequalities in the supplementary derivation give an open neighborhood in reserve, efficiency and early power around this modified construction, holding K=30 fixed. This is stronger than a single boundary point, while remaining a synthetic existence result. With vehicle acceptance capped at 30 kW, terminal-resource sensitivity is stated only for K<=30: the original lossless case is infeasible below K=20, has zero gap for 20<=K<=23.5, and has positive gap for 23.5<K<=30.

![Figure 4](figures/cyclic_robustness.png)

Figure 4. All 16 prospectively fixed reserve/loss/connector cases: nine positive gaps, six zero gaps and one infeasible case. Panel (a) crosses reserve, efficiency and early power; panel (b) changes terminal power under the nominal remaining assumptions. The nominal 30 kW case appears in both panels and is executed once. Values are synthetic currency, rounded for display; infeasibility has no numerical gap. An independent exact audit checks the complete intervals, all endpoint and supporting schedules, energy conversion, prices and connector sessions under zero switching time; all 22 corruption controls are rejected.

### 6.2. Replication and the scale of incentive error

Replicate the timetable to n simultaneous A services and n simultaneous B services. Keep individual battery and energy requirements fixed, with n early connectors at 10 kW and n terminal connectors at 30 kW. Scale supply cost as F_n(E,L)=4E+(E^2+L^2)/(10n), preserving marginal prices at fixed per-copy demand. This specifies market growth; holding supply curvature fixed would answer a different question.

If m buses each serve A and B, there are n-m A-only and n-m B-only buses, for 2n-m used buses. Complete physical early loads range from 10m to 10n. Every load in this interval has a replenished physical realization: give each paired bus 10 early kWh and share the remainder among A-only buses. Terminal charging can pair each A-only/B-only pair on one connector, with the m paired buses using the remaining connectors. The projected complete hull is a triangle; its lower boundary has intrinsic cost 14n-0.7E.

The hull optimum is CH_n=7591n/80. Every physical optimizer chooses an integer m nearest to 27n/40, with both choices retained at ties. Writing δ=m-27n/40 gives the exact bound

$$\Delta_n=\frac{20\delta^2}{n}\leq\frac{5}{n}.$$

At that physical optimum's own marginal prices, the whole operator can reconsider all service assignments. Along n=40k+1 its regret r_n satisfies

$$\Delta_n=\frac{169}{80n}\longrightarrow0,\qquad r_n=\frac{351}{40}+\frac{169}{40n}\longrightarrow8.775.$$

This incentive belongs to the operator controlling the entire growing fleet. Regret per used bus and regret divided by total physical cost both vanish. There is no positive regret limit over every size: when n is divisible by 40, the physical and hull optima coincide and regret is zero. At n=20, two equally good physical planners have own-price regrets 7 and 14; selecting one silently would conceal a relevant tie.

An explicit alternative institution clarifies the participant interpretation. Give each of n operators one mandatory A/B pair, a reserved early 10 kW connector and a reserved terminal 30 kW connector. Its complete choice is one bus with load (10,20), or two buses with load (x,30-x) for x in [0,10]. These choices are independently feasible under the reserved rights. At the original physical optimum's posted prices p=(4+2m/n,6-2m/n), the one-bus private cost exceeds the best two-bus private cost by 40δ/n. Because m/n>=1/2, the latter uses x=0, with indifference over x at equality. Each participant's current-plan regret is at most 20/n and therefore vanishes. Their summed regret equals the whole-fleet regret in this symmetric family. Along n=40k+1, each dissatisfied one-bus participant has regret 13/n, although the sum approaches 8.775. This post-result derivation has been independently checked against all 88 archived physical optima. It requires the stated partition and reserved resource rights; it is not a conclusion about arbitrary shared-charger games or a counterexample to large-market convexification.

![Figure 5](figures/cyclic_replication.png)

Figure 5. Exact replication results for n=1 through 80, covering two integer-rounding cycles; six larger predeclared sizes are also archived. The absolute planning gap decreases under the proved 5/n envelope, while whole-operator regret depends on rounding and need not converge to zero. Vertical segments connect both planner optima at ties. Costs and regret are synthetic currency. The independent audit reconstructs all 86 cases, 6,448 continuous branch minima and 88 physical optima, including finite-connector schedules and all price accounts; 21 corruption controls are rejected.

The welfare gap is therefore not a substitute for a price-response metric. In this family, every physical planner optimum still has zero fleet LOC at the common hull price, with supply LOC equal to the planning gap. The comparison concerns both which price is posted and how the incentive is normalized.

### 6.3. Qualification of a common native recharge model

A separate native implementation uses the same complete-fleet feasible-set builder for physical planning and price response. Its declared movement graph contains directed, timestamped travel modes and verified depot visits. An elementary interval grid respects every availability and resource boundary; a serial decoder assigns at most one bus at a time to the homogeneous connector. Continuous grid energy, charging efficiency, service and travel consumption, reserve and full terminal replenishment are checked by an independent event replay. This representation assumes zero switching time and no taper, and supports only the explicitly declared directed movement modes.

Fifteen predefined controls cover analytical cyclic prices and physical optima, reserve and efficiency, directed multi-leg travel, fractional availability windows, serial connector use and three infeasibility cases. The first frozen CBC implementation passed twelve controls and encountered three witness-extraction or replay exceptions. A separately frozen revision captured every raw native variable before decoding and imposed an explicit whole-incumbent roundoff budget of 1e-8 kWh. It preserves positive charge energy and records any negative-to-zero correction and session-capacity excess. Neither failed artifacts nor unavailable failed incumbents were reconstructed retrospectively.

The corrected revision passed all fifteen controls on CBC and on a separate Gurobi replication with unchanged physical inputs, targets and numerical policy. Each run returned thirty native calls, comprising twenty-seven finite optima and three infeasibilities. Independent solver-free audits reconstructed raw model constraints, every physical witness, all twenty-seven finite fixture objective minima and the expected infeasibilities. All twelve final intervals in each run contained the independently calculated optimum; their approximately 2e-6 widths reflect the declared two-sided numerical guard. Sixteen CBC and eighteen Gurobi corrupted-copy checks were rejected. This is qualification of small declared fixtures, not a proof of arbitrary floating-point oracle correctness or an operational performance comparison. A subsequent source-time extension retained all fifteen inputs and added four half-minute timing controls. All nineteen passed; an independent audit checked every result and rejected twenty-two corruptions. Exogenous timestamps are preserved on an exact half-minute lattice within a declared bounded horizon, while charging remains continuous. Convex-hull machinery and the public timetable remain separate gates.

### 7. Reoptimization before learning

Repeated certified hull and pricing calculations motivate a computational diagnostic: whether previously feasible complete schedules remain useful when only the tariff intercept changes. This is a baseline study, not a second claimed methodological breakthrough. It compares cold initialization, retention of the same arm's previous physical columns, and retention plus one proposal priced at the previous clean price plus the known intercept change. All arms rebuild tangents, duals and objective bounds. Only fresh clean pricing contributes to the lower certificate; proposal calls count even when they produce duplicates.

The earlier two-service qualification contained four tariff states and three arms. Total pricing calls were 12, 6 and 9 for cold, retained and retained-plus-shift. After initialization, the retained arm needed only the mandatory clean verification. This motivated a harder fixed design rather than immediate learner training.

The new design contains three hand-authored three-service fixtures, five tariff states and three arms, for 45 cells. Two fixtures allow one-/two-bus competition and battery depletion, with different vehicle costs. A third fixes two buses using explicit simultaneous terminal markers and restores both batteries; it is an inventory control, not a native overnight adapter or a variable-fleet cyclic example. Each trajectory contains an unchanged state, early-cheap and late-cheap changes, and a return to the initial tariff. All cases use continuous charging and multiple opportunities. They do not include shared-power or plug-count constraints.

The acceptance contract uses a fresh clean restricted master, a complete pricing bound, and a replayed true quadratic upper bound, with objective width at most 0.01. Each pricing solve has a ten-second cap and must return OPTIMAL. The total admission budget is 900 seconds, with one solver thread. After the arms finish, a separate complete-structure formulation supplies 15 reference intervals; those solutions never seed the comparison. The reference shares enumeration utilities and the CBC backend, so it is a formulation cross-check, not independent solver software.

All 45 cells were attempted in the first frozen execution. Forty-four certified cells passed their reference overlap checks, and all 15 references completed. The cold return-to-base cell in the lower vehicle-cost depleted fixture returned FEASIBLE at the pricing time cap and remains failed under the protocol. A narrow pricing bound is not substituted retrospectively for its OPTIMAL gate.

An independent implementation, importing no author code or optimization software, reconstructs all 223 pricing attempts with exact rational inventory-flow dynamic programming. Integral flow supplies and capacities make this exact for these continuous linear pricing problems. Exact Fenchel lower bounds computed from the completed clean prices independently support all 44 successful cells, with objective widths below 0.000913. Physical witnesses are checked at a 0.0000001 kWh tolerance. All 19 corruption controls are rejected. The reference witnesses and complete structure enumeration pass, although their tighter native lower bounds remain conditional solver evidence. This audit is specific to the frozen fixtures, not a certification of the general production adapter.

| Fixture | Cold pricing calls by state | Retained calls | Retained + shift calls |
|---|---|---|---|
| Depleted, f=20 | 7, 7, 5, 6, 7 failed | 7, 1, 2, 3, 1 | 7, 2, 3, 4, 2 |
| Depleted, f=26 | 6, 6, 4, 6, 6 | 6, 1, 1, 2, 1 | 6, 2, 2, 3, 2 |
| Replenished, fixed two buses | 14, 14, 11, 10, 14 | 14, 1, 1, 2, 1 | 14, 2, 2, 3, 2 |

Table 1. Pricing calls include initial seeds, proposals and clean verification. The failed cell includes attempted work and is not a certified time-to-solution observation. States are base, unchanged, early-cheap, late-cheap and return-base, in that order. Dependent states and hand-built fixtures are not independent population samples.

Across all attempts, the arms use 123, 44 and 56 pricing calls and 99.593, 28.062 and 31.881 complete cell seconds, respectively. At the 14 fixture-state keys where all three arms succeed, the corresponding totals are 116, 43 and 54 calls and 78.506, 27.656 and 31.375 seconds. The cold failure contributes seven attempts and 21.088 seconds to the first view. These are single-run descriptive totals, with success conditioning explicit; they do not estimate a general runtime speedup.

Some retained transitions require two or three clean calls, establishing remaining work on this diagnostic. The analytic proposal did not reduce the subsequent clean-call count in these trajectories. Across twelve warm transitions, retention uses 17 pricing calls. An architecture that always adds one full-pricing proposal and still requires one clean pricing verification has a lower limit of 24 calls, even if every proposal is useful. It therefore cannot improve this pricing-call metric on the observed fixed trajectory. Direct learned schedule proposals or selective triggering are different architectures; neither is tested here. The remaining discovery work is not evidence that a learner can remove it. A learning experiment would need a separate frozen development/evaluation design, equal final certificates and full offline/online accounting.

### 8. Operational interpretation and remaining evidence

The intended transportation contribution needs a timetable-based study in addition to exact constructions. That study must identify mandatory trips separately from a provider's solved vehicle blocks; preserve source-row lineage; specify directed and time-dependent deadheads; and state vehicle energy, reserve, terminal recharge and charger-resource assumptions. Historical block membership can provide a feasible reference or warm start, but cannot establish a globally optimal schedule or reveal the provider's objective weights.

A local GIRO audit has matched mandatory services to source rows and separated historical vehicle assignments from trip requirements. A proposed 17-service historical pair has observed trip and movement energies, but further inspection found off-depot charging and gaps without explicit movement records. The presence of recorded energies does not establish a complete, source-faithful path. This candidate is not admitted to the depot-only native model, and most counterfactual cross-run movements also lack matching directed records. Battery, replenishment and charger assumptions require explicit declaration. Private source rows, identifiers and hashes remain outside the public artifact.

A public 100-service column-generation benchmark has been pinned and parsed independently. Its energy and time units are abstract, and finite charger capacities and a grid-cost model are not supplied. It can test parser and route feasibility, but does not supply operational calibration for the price-support question. Sistig et al. [13] provide a more directly useful public intake candidate: processed timetables, possible deadheads and heuristic schedules from a twenty-network electrification study, with versioned CC BY data [14]. The smallest complete case has 37 mandatory services and a complete directed deadhead matrix. Its 30-second travel-time offsets are preserved, and energy is reconstructed from declared traction and auxiliary rates rather than treated as telemetry. The two declared one-depot, single-connector variants have passed source and feasibility review; pricing and hull experiments remain. They do not reproduce the source two-depot or multi-output charger design. Neither source description nor a published historical schedule establishes an optimal EGG response or an operational economic effect.

An independent source audit reconstructs all 37 services, the directed matrix and every emitted movement mode. A deliberately simple one-service-per-bus construction establishes feasibility of both depot variants under the declared 400 kWh usable inventory, one 360 kW connector and 30-hour replenishment horizon. Its total modeled energy is 2,089.876 kWh for depot 15 and 2,769.814 kWh for depot 16. Each reference includes one modeled pullout and pullin per service; they are feasibility references, not recommended fleets or estimates of optimized consumption.

![Figure 6](figures/public_case_intake.png)

Figure 6. Public timetable and modeled energy for the complete 37-service Hildenbrand intake, adapted from Sistig et al. [13,14] under CC BY 4.0. (A) Each bar retains the source departure, arrival and next-day offset; rows are services, not assigned vehicles. (B) Service and pullout/pull-in energy for constructed, replay-checked 37-bus references under two separate one-depot scenarios. Both restore full 400 kWh usable inventory by 30:00 using one 360 kW connector. These are not optimized results; energy comes from declared EB-3 assumptions and is not source-observed telemetry.

A timetable alone does not identify the supply curvature. Exogenous time-of-use tariffs, a convex incremental supply cost, contractual demand charges and charger scarcity rents are different economic objects. The first operational sensitivity study should report energy, bus count, physical cost bounds, hull bounds, regret bounds and the stated curvature scale separately. Until calibration is defensible, monetary magnitudes must be labeled stylized.

### 9. Discussion and limitations

The constructions show that continuous charging does not erase duty indivisibility, even when all net service energy is purchased, every used battery is replenished and one finite connector must be scheduled explicitly. The original boundary point is fragile at fixed hardware; a modified point remains positive under reserve and efficiency perturbations. This establishes existence within declared physical assumptions, not prevalence or materiality in real bus systems.

Replication makes the normalization particularly important. Scaling supply capacity with demand yields an absolute planning gap approaching zero, yet whole-operator own-price regret stays positive along a specified subsequence. Per-bus and relative regret vanish, and some fleet sizes have exact price support. When the same services instead belong to bounded pair-level operators with reserved connector rights, every individual's regret also vanishes. Small system-cost gaps, individual incentives and their aggregate must be reported with their respective denominators and ownership assumptions.

The certificate interpretation is strongest when physical models match exactly. An easier duty-level relaxation, a partially enumerated schedule menu or an aggregate-only capacity constraint can answer a different question. For large cases, it may still be possible to certify a positive gap without enumerating the entire hull: a valid physical lower bound and a replay-feasible mixture upper bound suffice. Failure to prove a positive gap is not proof of equilibrium existence.

The numerical reuse study has a different purpose. It is a development diagnostic, with one execution, small fixtures and strict native-solver termination. It does not estimate a runtime distribution or demonstrate learning effectiveness. The failed cold cell illustrates why full work and failures belong in any speed comparison. Future revisions should add an independent solver check and a prospectively chosen larger design only when they answer a concrete scientific uncertainty.

Finally, price support is an incentive statement under specified rights, not an implementation mechanism. A convex-hull price may support fleet behavior while leaving supplier LOC. Charging-resource scarcity may require a separate allocation or rent account. Neither can be resolved by relabeling fleet regret as a universally sufficient subsidy.

### 10. Conclusion

Complete fleet schedules provide the appropriate object for distinguishing physically implementable bus operations from convexified charging plans. Fully replenished continuous-charging constructions have exact positive planning gaps under explicit reserve, loss and connector assumptions, with different lost-opportunity accounts at own and common hull prices. Replication separates convergence of planning cost from convergence of whole-operator incentives. Reoptimization experiments show that retained schedules are a necessary baseline and that additional proposal work must justify its cost under a fresh certificate. The next empirical task is to determine the magnitude and relevance of these effects on a provenance-qualified timetable while retaining explicit energy and resource assumptions.

### Reproducibility and draft status

The original exact source and protocol were frozen at Git commit 7bf913a before execution. Replication and robustness were frozen at ce84e9e and bd022ac, respectively. Their independent auditors import no experiment-author code, reconstruct all declared cases using rational arithmetic, and preserve the first-run raw files. Separate manifests distinguish raw evidence from subsequent review artifacts.

The harder reuse source, protocol and adversarial tests were frozen at 7d3d764 before execution. All 44 successful reuse certificates passed independent reconstruction; the result retains its one failure. The audit found 145 mutable master-log snapshots. The solved tangent sets are recoverable from the frozen control flow; a prospective deep-copy repair at 78bb4c0 preserves future snapshots without replacing any first-run artifact. The independent Fenchel certificates do not depend on that log repair. Figure scripts read archived result JSON. The source-verified related-work matrix and BibTeX accompany this draft. The corrected native model has independent synthetic qualification on two backends, with its original failure preserved. This version remains a working manuscript: the native-hull extension and the public timetable study require their own evidence before broader claims. The first native-hull gate certified two cells, exhausted its restricted-master cap on four, and correctly blocked two dependent states. Its raw inner traces exposed repeated tangent refinement at numerical resolution, with useful improved mixture objectives omitted from the failed states’ final summaries. A separately frozen correction adds bounded exact arithmetic on stored column projections, while retaining numerical physical witnesses and native global bounds. Its second execution returned certificates for all eight controls; independent result review remains pending. None of the failed first-run states is reclassified as successful.

### References

[1] Wu, W., Lin, Y., Liu, R., and Jin, W. (2022). The multi-depot electric vehicle scheduling problem with power grid characteristics. Transportation Research Part B 155, 322-347. https://doi.org/10.1016/j.trb.2021.11.007

[2] de Vos, M. H., van Lieshout, R. N., and Dollevoet, T. (2024). Electric vehicle scheduling in public transit with capacitated charging stations. Transportation Science 58(2), 279-294. https://doi.org/10.1287/trsc.2022.0253

[3] Parmentier, A., Martinelli, R., and Vidal, T. (2023). Electric vehicle fleets: Scalable route and recharge scheduling through column generation. Transportation Science 57(3), 631-646. https://doi.org/10.1287/trsc.2023.1199

[4] ten Bosch, W., Hoogeveen, H., van Kooten Niekerk, M., and de Bruin, P. (2026). Scheduling electric vehicles by simulated annealing with recombination through ILP. Public Transport 18(1), 211-228. https://doi.org/10.1007/s12469-026-00424-2

[5] Zoltowska, I., and Lin, J. (2021). Optimal charging schedule planning for electric buses using aggregated day-ahead auction bids. Energies 14(16), 4727. https://doi.org/10.3390/en14164727

[6] Maldonado, F., and Saumweber, A. (2022). Why do pricing rules matter? Electricity market design with electric vehicle participants. World Electric Vehicle Journal 13(8), 143. https://doi.org/10.3390/wevj13080143

[7] Madani, M., Ruiz, C., Siddiqui, S., and Van Vyve, M. (2018). Convex hull, IP and European electricity pricing in a European power exchanges setting with efficient computation of convex hull prices. arXiv:1804.00048v1. https://arxiv.org/abs/1804.00048v1

[8] Andrianesis, P., Bertsimas, D., Caramanis, M. C., and Hogan, W. W. (2022). Computation of convex hull prices in electricity markets with non-convexities using Dantzig-Wolfe decomposition. IEEE Transactions on Power Systems 37(4), 2578-2589. https://doi.org/10.1109/TPWRS.2021.3122000

[9] Hümbs, L., Martin, A., and Schewe, L. (2022). Exploiting complete linear descriptions for decentralized power market problems with integralities. Mathematical Methods of Operations Research 95, 451-474. https://doi.org/10.1007/s00186-022-00775-z

[10] Bichler, M., Knörr, J., and Maldonado, F. (2023). Pricing in nonconvex markets: How to price electricity in the presence of demand response. Information Systems Research 34(2), 652-675. https://doi.org/10.1287/isre.2022.1139

[11] Sugishita, N., Grothey, A., and McKinnon, K. (2024). Use of machine learning models to warmstart column generation for unit commitment. INFORMS Journal on Computing 36(4), 1129-1146. https://doi.org/10.1287/ijoc.2022.0140

[12] Löbel, F., Borndörfer, R., and Weider, S. (2024). Electric bus scheduling with non-linear charging, power grid bottlenecks, and dynamic recharge rates. arXiv:2407.14446v1. https://arxiv.org/abs/2407.14446v1

[13] Sistig, H. M., Sinhuber, P., Rogge, M., and Sauer, D. U. (2025). Evaluating costs and operations of public bus fleet electrification. npj Sustainable Mobility and Transport 2, 15. https://doi.org/10.1038/s44333-025-00030-y

[14] Sistig, H. M., Sinhuber, P., Rogge, M., and Sauer, D. U. (2025). Dataset for evaluating costs and operations of public bus fleet electrification, version 1. Figshare. https://doi.org/10.6084/m9.figshare.26088190.v1
