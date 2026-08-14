# Market Mechanisms, Strategic Pricing, and Electric-Bus Demand Response

Date: 2026-08-14

Status: full-text research notes

## Scope and evidence note

This note records a full-text audit of eight locally supplied articles. It is intended to preserve evidence and novelty boundaries for later thesis brainstorming, not to serve as a polished narrative literature review.

The papers were read from the complete local PDFs listed below, including their mathematical formulations, experiments, tables, conclusions, and, where relevant, appendices. Claims about methods and reported results are tied to those PDFs rather than to abstracts or search snippets. Page references use the journal page when one is printed clearly; otherwise they use the physical PDF page. Numerical findings are the authors' reported results and have not been independently reproduced. No supplementary data or source code was audited.

"Novelty killed" below means that a broad claim is no longer defensible as the central novelty after reading that paper. It does not establish that the eight-paper set is an exhaustive novelty search. "Atomic EVSP" means an exact, indivisible electric vehicle scheduling problem with mandatory trip coverage, vehicle-duty continuity, time-resolved battery feasibility, and explicit charging-resource conflicts, rather than an aggregate energy or route-flow model.

Local source inventory:

- `1251251.pdf`: Deori, Margellos, and Prandini (2018).
- `1245125.pdf`: Zoltowska (2016).
- `523523.pdf`: Zou et al. (2016).
- `525.pdf`: Fang et al. (2022).
- `5.pdf`: Wu et al. (2019).
- `4.pdf`: Lu et al. (2021).
- `3.pdf`: Wang et al. (2024).
- `11.pdf`: Afentoulis and Vagropoulos (2025).

## Executive synthesis

Taken together, these papers close several generic research claims:

1. Continuous EV charging games, fixed-point characterizations, and asymptotic efficiency are established.
2. Strategic multi-period storage and mobile-storage bidding through MPEC/EPEC or bilevel models is established.
3. Bus operations and charging have already been coupled to endogenous DLMPs.
4. An intercity passenger fleet has already been modeled as a price-making leader that changes routes, charging, discharging, and energy/reserve bids in response to network prices.
5. A price-to-route/station-to-load-to-price fixed-point loop has already been formulated for EV charging traffic.
6. Minimum-uplift pricing for intertemporally shiftable demand is established.
7. VCG plus Nash-bargaining settlement for storage has been proposed.
8. Strategic manipulation of common EV demand-response baselines has been demonstrated with real fleet and market data.

The remaining defensible core is narrower and stronger:

> Design and compute a power-market allocation and settlement for mandatory, indivisible electric-fleet duties, where exact trip coverage and charger feasibility determine a discontinuous load response, the fleet can affect prices, and payments are evaluated against every alternative feasible fleet schedule.

The most reusable bridge is to treat the EVSP solver as an economic oracle. It can generate duties for welfare clearing, find profitable deviations at candidate prices, calculate opportunity-cost uplift, and solve counterfactual allocations for mechanism design.

---

## 1. Deori, Margellos, and Prandini (2018)

### Verified metadata and source

Luca Deori, Kostas Margellos, and Maria Prandini, "Price of anarchy in electric vehicle charging control games: When Nash equilibria achieve social welfare," *Automatica* 96 (2018), 150-158. DOI: `10.1016/j.automatica.2018.06.043`.

Local source: `../papers/1251251.pdf`.

### Application and mathematical mechanism

The paper compares cooperative and noncooperative charging by many heterogeneous plug-in EVs over a discrete time horizon.

The cooperative benchmark minimizes

\[
F^m(x)=\sum_t p_t\left(\sum_i x_{it}+x^0_t\right)^2
\]

subject to each vehicle meeting a fixed total energy requirement and time-specific lower and upper charging bounds. See Section 2.1, journal pp. 151-152.

Vehicle \(i\)'s noncooperative payment is

\[
f_i(x_i,x_{-i})=
\sum_t x_{it}p_t\left(\sum_{j\ne i}x_{jt}+x_{it}+x^0_t\right).
\]

Each vehicle therefore internalizes its own effect on an affine aggregate-demand price. See Section 2.2, p. 152.

The central auxiliary problem is

\[
P_a:\quad \min_x F^m(x)+\sum_{i,t}p_tx_{it}^2.
\]

Proposition 4 shows that the minimizers of this problem coincide with the Nash equilibria. With \(p_t>0\), the auxiliary objective is strictly convex and the equilibrium is unique. See Section 3.2, p. 153.

### Fixed-point and convergence content

Section 3.1, pp. 152-153, defines a tie-broken best-response map \(T\) and a proximal map \(\widetilde T\) with regularization \(c\|z_i-x_i\|^2\). Propositions 1-2 and Corollary 1 establish

\[
\mathcal N=\operatorname{Fix}(T)=\operatorname{Fix}(\widetilde T).
\]

This is a fixed-point characterization, not a proof that undamped best-response or price-response iteration is a contraction. The numerical study uses a regularized Jacobi method developed in a companion paper. This paper should therefore not be cited as a general convergence theorem for arbitrary charging-price iteration.

### Price of anarchy

Under i.i.d. vehicle requirements and bounds, with finite first and second moments, Theorem 2 proves

\[
\frac{F^m(x_a^\star)}{F^m(x^\star)}\rightarrow 1
\quad\text{almost surely as }m\rightarrow\infty.
\]

See Section 3.3, pp. 153-155. The strategic correction in the auxiliary objective grows roughly as \(O(m)\), whereas aggregate electricity cost grows as \(O(m^2)\), so individual market impact disappears in a large population.

For a discrete heterogeneity distribution, Section 4, pp. 155-157, groups identical agents and proves convergence of normalized welfare to a deterministic limit.

### Experiments and reported results

The experiment is stylized rather than empirical:

- 12 time periods.
- Charging limits \(0\le x_{it}\le1\).
- Energy requirements sampled uniformly from \([0,12]\).
- 100 random population extractions at each population size.
- Figure 1, p. 155, shows the Nash-versus-social relative gap approaching zero, but not monotonically.
- Figure 2, p. 156, shows convergence of normalized aggregate profiles and valley filling.
- Figure 3, p. 157, uses a fine discrete uniform distribution and shows concentration of normalized welfare.

### Assumptions and limitations

- Continuous and convex individual charging sets.
- Cartesian-product separability among vehicles.
- Affine, time-separable price functions.
- No transmission or distribution network.
- No trip coverage, duty chaining, charger conflicts, or integer assignments.
- Independent vehicles rather than a concentrated fleet controlling all vehicles jointly.
- The efficiency result is asymptotic and does not protect a finite fleet with market power.

Fleet-wide trip-cover constraints destroy the product structure used in the analysis. Binary duties destroy the convexity that makes every Nash equilibrium the unique global optimizer of the auxiliary problem.

### Novelty killed

- A generic fixed-point formulation of price-responsive EV charging.
- Potential-game structure under affine aggregate prices.
- Uniqueness for the continuous affine-price charging game.
- Asymptotic equivalence of Nash and social welfare for many small EV agents.

### Exact atomic EVSP opportunity

For a finite set of discrete duties, affine-price algebra may still yield a finite potential game, so a global potential minimizer may be a pure equilibrium. However, uniqueness, global convergence, and the paper's price-of-anarchy proof do not carry over. Exact best response may terminate at a locally stable but inefficient duty configuration.

A useful atomic-EVSP experiment is to compare:

1. The exact social optimum.
2. The global discrete-potential optimum, when a valid potential exists.
3. Equilibria reached by sequential or damped exact EVSP best responses.

This would quantify the economic effect of fleet concentration, service coupling, and integrality rather than rediscovering the continuous fixed point.

---

## 2. Zoltowska (2016)

### Verified metadata and source

Izabela Zoltowska, "Demand shifting bids in energy auction with non-convexities and transmission constraints," *Energy Economics* 53 (2016), 17-27. DOI: `10.1016/j.eneco.2015.05.016`.

Local source: `../papers/1245125.pdf`.

### Clearing model

Consumers submit a fixed demand component, stepwise elastic demand blocks, and minimum and maximum total accepted elastic energy over the horizon. Setting \(E_d^{\min}=E_d^{\max}\) forces curtailed demand to move to another time instead of disappearing; the paper identifies EV charging as an application. No binary demand-response participation indicator is required. See Section 2, pp. 18-19.

The ISO first solves a multiperiod welfare-maximizing DC-OPF/unit-commitment MILP with:

- Stepwise demand and generator offers.
- Generator commitment costs and operating constraints.
- Nodal balance.
- Shift-factor transmission limits.

See Section 3, p. 19.

### Direct minimum-uplift pricing

After the efficient dispatch is fixed, a second problem chooses prices and uplift payments. For each shifting consumer, uplift must cover

\[
\text{best attainable benefit at the candidate prices}
-\text{benefit of the dispatched schedule}.
\]

The best intertemporal response under \(E_d^{\min}\) and \(E_d^{\max}\) is linearized using surplus and deficit price variables plus the Ogryczak-Tamir sum-of-\(k\)-largest construction. See Section 4.1, equations (10)-(16), pp. 19-21.

Generator uplift covers dispatch and commitment opportunity costs. A Bellman recursion with binary variables represents maximum attainable generator profit. See Section 4.2, pp. 21-22.

The direct minimum-uplift objective is

\[
\min \sum_d R_d^D+\sum_l R_l^S.
\]

Spatial prices retain an LMP-like decomposition through congestion-price variables. A budget-balanced variant uses different buying and selling prices; their weighted difference funds uplift. See Sections 4.3-4.5, pp. 22-23.

The computational procedure is:

1. Clear the welfare-maximizing MILP.
2. Derive conventional LMPs with commitment fixed.
3. Solve the pricing problem with those prices fixed.
4. Use that result to warm-start the unrestricted direct minimum-uplift model.

### Experiments and reported results

Three-node, two-hour case with three generators and two loads:

- Fixed demand: generator loss/uplift is $845 under LMP and $226.33 under DMU, but the consumer payment rises substantially.
- 20% shiftable demand: DMU uplift is $215.10 versus $610 under LMP, and the reported $1,200 opportunity cost is eliminated.
- 30% shiftable demand: DMU uplift is $68.97 versus $510 for the compared LMP outcomes.

See Tables 2-5 and Sections 5.1.1-5.1.4, pp. 23-24.

IEEE RTS case:

- 24 nodes and 24 hours.
- 32 generators and 17 consumers.
- Fixed, curtailable, and fully shifted demand at 10%, 20%, and 30% flexibility.
- CPLEX 12.5 solves each reported case within 70 seconds on the stated desktop.
- Table 7 shows that DMU usually, but not universally, reduces uplift; E10 and S10 are exceptions.
- Welfare-equivalent schedules can produce dramatically different prices, payments, congestion rent, and uplift.

See Section 5.2, pp. 24-26.

### Assumptions and limitations

- Flexible demand is divisible and described only by aggregate energy bounds.
- No route, trip, duty, depot, vehicle, or charger compatibility constraints.
- Make-whole payment is calculated against submitted bids; truthful bidding is not established.
- The conclusion explicitly identifies individual rationality, budget balance, payments, and incentive compatibility as topics requiring further study.
- Buying/selling price differentiation can shift uplift costs onto fixed consumers or congestion rent.
- Multiple optimal clearing schedules make settlement unstable.
- Bellman and big-M constructions add computational burden.

### Novelty killed

- Minimum-uplift pricing for intertemporally shifting demand.
- Ex-post opportunity-cost compensation for flexible demand in a nonconvex power market.
- The general use of separate market-clearing and price-support stages.

### Exact atomic EVSP opportunity

For fleet \(f\), candidate prices \(\pi\), dispatched schedule \(z_f^\star\), and uplift \(u_f\), require

\[
U_f(z_f^\star;\pi)+u_f
\ge
\max_{z\in\mathcal Z_f}U_f(z;\pi),
\]

where \(\mathcal Z_f\) is the exact set of feasible trip-covering schedules. The right-hand side is an EVSP best-response problem. It can be enforced without enumerating all fleet schedules by solving EVSP-DR as a separation oracle and adding a violated no-deviation constraint whenever a better schedule exists.

This creates a minimum-uplift settlement with a certificate that no operationally feasible rescheduling is more profitable. It generalizes simple energy shifting to exact trip coverage, vehicle continuity, battery dynamics, and charger capacity. Strategic bid manipulation remains a separate mechanism-design question.

---

## 3. Zou et al. (2016)

### Verified metadata and source

Peng Zou, Qixin Chen, Qing Xia, Guannan He, Chongqing Kang, and Antonio J. Conejo, "Pool equilibria including strategic storage," *Applied Energy* 177 (2016), 260-270. DOI: `10.1016/j.apenergy.2016.05.105`.

Local source: `../papers/523523.pdf`.

### Strategic model

The paper formulates a multi-leader, common-follower Stackelberg game:

- Thermal, hydro, renewable, and storage participants are leaders.
- Each participant chooses the intercept of its supply bid between a floor and cap.
- The market operator is the common follower and minimizes submitted production cost.

See Section 2 and Figure 1, pp. 261-262.

Storage has charging and discharging limits, energy bounds, efficiencies, and a terminal-SOC-equals-initial-SOC constraint. Thermal units have output and ramp constraints, hydro has a daily energy limit, and renewables have time-varying availability. See Section 3, pp. 261-263.

### EPEC method

For each participant, the authors:

1. Replace the continuous market-clearing problem by its KKT conditions, creating an MPEC.
2. Replace each complementarity pair with a slack variable and a Fischer-Burmeister equality.
3. Take the KKT conditions of each participant's MPEC.
4. Concatenate those conditions into an EPEC.

See Sections 4-5, pp. 263-264.

The EPEC is nonconvex and may have multiple solutions. It is solved directly with KNITRO 9.0 under GAMS. When multiple equilibria are found, the paper selects one minimizing total generation cost or maximizing total participant profit.

There is no uniqueness theorem, global-optimality certificate, or best-response convergence proof. Taking KKT conditions of nonconvex MPECs supplies stationarity conditions rather than a general exact equilibrium algorithm. The numerical outcomes should be treated as solver-found equilibrium candidates.

### Experiments and reported results

The modified IEEE 57-node dataset is used without transmission limits, so the experiment is effectively a uniform-price system:

- 24 hours.
- 850 MW installed capacity excluding storage.
- Eight thermal units totaling 730 MW.
- One 20 MW hydro plant.
- 50 MW wind and 50 MW solar.
- One 25 MW storage unit.
- Peak load 650 MW and average load 551 MW.

Three storage types are compared: PHS, CAES, and zinc-bromine flow battery.

Strategic storage cycles more than nonstrategic storage. CAES charges/discharges 270.9/219.4 MWh strategically versus 119.9/97.09 MWh competitively. See Table 2, p. 265.

Table 3, p. 266, reports:

- Strategic benchmark average MCP: $16.70/MWh.
- Strategic benchmark plus PHS: $16.09/MWh.
- Plus CAES: $15.68/MWh.
- Plus zinc-bromine flow battery: $16.42/MWh.
- Strategic profits: $609.70, $122.13, and $221.56, respectively.

Strategic outcomes are not simply higher priced; strategic hydro and storage can reshape dispatch enough to lower the average price relative to the paper's competitive case. Raising peak load to 700 MW increases average MCP to $17.58, a reported 12.1% increase. Wind profiles also alter storage profits materially. See Sections 6.4-6.5 and Table 4, pp. 268-269.

### Assumptions and limitations

- Continuous storage dispatch.
- No unit commitment.
- No network congestion or LMP differentiation.
- Deterministic renewable output.
- Uniform market price.
- Bid intercept is the strategic instrument.
- No combinatorial or indivisible offers.
- No mobility or service obligations.
- Local nonlinear solution and ad-hoc equilibrium selection.

### Novelty killed

- Generic multi-period price-making storage equilibrium.
- EPEC/MPEC representation of strategic flexible resources.
- The broad claim that strategic storage bidding and market clearing have not been jointly modeled.

### Exact atomic EVSP opportunity

KKT conversion is not available for a discrete EVSP response. That creates a legitimate methodological gap.

Possible exact or certified approaches include:

- Exact fleet best-response iteration with EVSP-DR as the oracle.
- Finite-game potential methods under restricted affine residual-price models.
- Branch-and-price equilibrium search over XOR duty packages.
- Cutting-plane methods alternating ISO clearing and exact fleet deviations.
- Upper and lower bounds on equilibrium regret rather than an unsupported convergence claim.

With multiple fleet operators, each operator could offer mutually exclusive duty packages and the ISO could clear them with generation and network constraints. This is a combinatorial analogue of an EPEC for which the paper's continuous KKT machinery is not exact.

---

## 4. Fang et al. (2022)

### Verified metadata and source

Xichen Fang, Hongye Guo, Xian Zhang, Xuanyuan Wang, and Qixin Chen, "An efficient and incentive-compatible market design for energy storage participation," *Applied Energy* 311 (2022), 118731. DOI: `10.1016/j.apenergy.2022.118731`.

Local source: `../papers/525.pdf`.

### Bidding and clearing mechanism

Storage submits:

- A stepwise degradation cost per charging/discharging mileage.
- A stepwise terminal-SOC valuation.
- Charging/discharging limits, SOC bounds, efficiencies, and energy capacity.

The ISO manages storage SOC centrally. The clearing LP maximizes consumer utility minus generator cost and storage degradation cost, plus terminal stored-energy value. It includes DC nodal balance and line limits, although the numerical analysis later omits network topology. See Section 3, PDF pp. 3-4.

Charging and discharging are represented by separate nonnegative variables without an explicit mutual-exclusion binary. Positive degradation cost and efficiency loss normally discourage simultaneous operation, but this is not a universal physical guarantee.

### Aggregate VCG and asymmetric Nash bargaining

Stage 1 treats all storage units as one coalition. Aggregate payment is

\[
R^{VCG}_{ESS}
=S_{-I}(c^0_{-I},P_I^{ESS,\star})
-S_{-I}(c^0_{-I},0),
\]

the improvement in other participants' welfare relative to excluding all storage. This requires a with-storage and a without-storage clearing. See Section 4.1, PDF pp. 4-5.

Stage 2 allocates that payment through asymmetric Nash bargaining. Each unit's disagreement point is its LMP payment:

\[
R_i^{VCG}
=R_i^{LMP}
+\left(R_{ESS}^{VCG}-R_{ESS}^{LMP}\right)
\frac{\alpha_i}{\sum_k\alpha_k}.
\]

The bargaining weight approximates contribution using the average of nodal LMPs with and without storage multiplied by net injection. See Section 4.2, PDF p. 5.

The VCG-minus-LMP deficit is charged to generators and consumers with positive surplus gains in proportion to those gains. See Section 4.4, PDF pp. 6-7.

### Properties and caveats

Appendix 1, PDF pp. 10-11, proves that non-storage welfare is concave in a fixed continuous storage-injection vector. Therefore, the VCG secant payment is at least the LMP tangent payment.

Appendix 2, pp. 11-12, uses LP KKT conditions to show that LMP revenue covers declared degradation cost and terminal-value change, supporting individual rationality in the convex continuous model.

Appendix 3, p. 12, gives the standard VCG truthfulness argument for one monopolistic storage agent or the grand coalition treated as one agent.

The paper does not rigorously establish dominant-strategy truthfulness for independently owned storage units receiving bargaining shares:

- An individual report can affect dispatch, LMP disagreement payment, bargaining weight, and total coalition payment.
- Aggregate VCG truthfulness does not automatically transfer to a non-VCG internal allocation.
- The distributed-agent argument relies substantially on a small unit having little price impact.
- The monotonicity step in equation (3.9) appears to infer payment ordering from \(\alpha_i>\alpha_j\) without separately controlling different LMP disagreement payments.
- Beneficiary-based deficit charges can create incentives for generators and consumers, who are assumed truthful.
- Grand-coalition anti-collusion does not establish coalition-proofness for every subset.

### Experiments and reported results

The test system has:

- 12,020 MW installed capacity.
- 5,980 MW thermal, 3,000 MW solar, 2,000 MW wind, and 1,040 MW storage.
- Eight storage units.
- Seven representative CAISO net-load scenarios.
- Peak net load of 5,463 MW.
- No topology in the numerical experiment.
- Truthful non-storage bids by assumption.

See Section 5.1 and Table 1, PDF pp. 6-7.

For one storage unit, ISO-managed degradation/terminal-value bidding yields weighted-average profit of $234.3, versus $96.4 for self-scheduling and $167.5 for a conventional economic bid. Welfare increments are $244.5, $110.6, and $173.9, respectively. See Section 5.2, Figures 3-5, PDF pp. 7-8.

Under LMP settlement, overstating cycling cost by 40% raises aggregate profit from $874.7 to $1,255.4. Under pay-as-bid, overstating cost by 60% raises profit from zero to $750.1. In the proposed mechanism, the tested truthful cycling-cost report yields the highest listed profit, $2,442.6. See Table 2 and Section 5.4, PDF pp. 7-9.

Average computation time is 119.06 seconds for aggregate VCG plus bargaining versus 840.44 seconds for separate classical VCG calculations, an 85.8% reduction. See Table 3 and Section 5.5, PDF pp. 7-9.

### Assumptions and limitations

- Convex, continuous clearing is essential to the concavity, tangent/secant, and KKT proofs.
- Numerical topology and unit commitment are omitted.
- Non-storage agents are treated as truthful.
- Aggregate VCG does not automatically make each bargaining recipient truthful.
- Budget-deficit allocation is not shown to be strategyproof.
- Optional storage can be excluded from the market; a mandatory transit fleet cannot simply disappear.

### Novelty killed

- Degradation-aware storage bids and terminal-SOC valuation.
- VCG settlement for storage participation.
- Aggregate VCG followed by Nash-bargaining allocation.
- The generic claim that contribution-based storage payments solve the diminishing-price-spread incentive problem.

### Exact atomic EVSP opportunity

Integrality breaks the paper's main proofs:

- Fleet injection is nonconvex.
- System welfare need not be concave in a fleet load vector.
- LMP revenue need not cover the opportunity cost of a mandatory trip schedule.
- Counterfactual clearing becomes an exact branch-and-price problem.

The outside option must also be defined carefully. A valid fleet counterfactual might be a fixed nonresponsive charging policy, replacement operator, reserve fleet, diesel service, or explicit procurement of trip coverage. "Remove the fleet" is normally infeasible because the trips remain mandatory.

For one fleet treated as a single multidimensional agent, exact VCG remains conceptually possible if the allocation is solved exactly and the outside option is well defined. For multiple fleets, per-fleet VCG, core-selecting payments, coalition stability, budget deficit, and computational reuse of duty columns become substantive research questions.

---

## 5. Wu et al. (2019)

### Verified metadata and source

Z. Wu, F. Guo, J. Polak, and G. Strbac, "Evaluating grid-interactive electric bus operation and demand response with load management tariff," *Applied Energy* 255 (2019), 113798. DOI: `10.1016/j.apenergy.2019.113798`.

Local source: `../papers/5.pdf`.

### Actual method and application

The upper level is tactical bus-service planning, not atomic vehicle scheduling. It chooses route frequencies \(f_l\) and the fraction of layover used for opportunity charging. Required buses are approximated by \(\lceil T_lf_l\rceil\), and available charging time is fitted with a convex function \(p_1/f_l+p_2\). The objective trades:

- Vehicle-km operating cost.
- Passenger revenue and waiting-time elasticity.
- DLMP charging cost.
- A battery-capacity-deficit cost for unmet daytime charging.

The lower level is a lossy DCOPF/SCED with fictitious nodal demand used to approximate losses and derive DLMPs. KKT replacement produces an MPCC. See Sections 2.1-2.5, PDF pp. 3-7.

### Experiments and reported results

The partly real test combines:

- Eight Shenzhen bus routes, GTFS, and smart-card patronage.
- 304 bus stops and 14 stations.
- An RBTS distribution network.
- Three aggregated bus charging loads.
- 300 available buses.
- 140 kW charger power, 80% grid-to-vehicle efficiency, and 1.25 kWh/km consumption.

With DLMP response:

- Distribution losses fall from about 12.4% to 5.2%.
- Charging cost falls from GBP 3,066.7 to GBP 2,273.0, a 25.88% reduction.
- Peak bus load falls 14.98%.
- 8.17% of daytime charging is removed rather than shifted.
- Required battery capacity rises 10.57%.
- Service vehicle-km and number of dispatched buses fall roughly 13-14%.

See Sections 3.2-3.3, PDF pp. 8-10. The battery-cost sensitivity study is in Section 4, pp. 10-11.

### Assumptions and limitations

- Tactical route-frequency planning rather than a fixed timetable.
- Free-flow road conditions and neglected boarding/alighting delays.
- Charging only at route-end stations.
- Layover charging availability is fitted rather than derived from exact vehicle duties.
- Aggregate route loads rather than explicit individual trip chains.
- Bus service can be reduced in response to grid conditions.
- No strategic market bid, payment design, uplift, or truthfulness analysis.

### Novelty killed

- Joint bus-service planning and endogenous DLMP congestion management.
- Bilevel bus-operator/DSO coordination.
- The observation that heavy-duty public transport may be unable to shift interrupted charging.
- Tactical adjustment of bus frequency and opportunity charging to distribution prices.

### Exact atomic EVSP opportunity

The atomic extension must hold every scheduled trip fixed, build exact duties, derive node-time charging from those duties, and forbid service reduction as a source of flexibility. It should measure the residual grid service available after enforcing:

- Exact timetable coverage.
- Vehicle continuity and deadheads.
- Battery feasibility.
- Depot and charger limits.
- Minimum operational reserve.

The economic question is then whether prices or payments adequately compensate genuine flexibility without encouraging service degradation.

---

## 6. Lu et al. (2021)

### Verified metadata and source

Zhilin Lu, Mingbo Liu, Chong Tang, and Wentian Lu, "Operational scheduling of intercity passenger transportation company participating in energy and reserve markets," *International Journal of Electrical Power & Energy Systems* 125 (2021), 106541. DOI: `10.1016/j.ijepes.2020.106541`.

Local source: `../papers/4.pdf`.

### Actual method and application

This is the closest paper in the reviewed set to the proposed problem.

It models individual vehicles with binary parking, arrival, and route-selection states in a city-level time-space network. Passenger service is represented by minimum departures on each route and sufficient vehicle presence at cities. It is not a fixed set of atomic timetabled trips. See Section 2, PDF pp. 3-4.

The merchant intercity passenger transportation company is a price-making Stackelberg leader. It jointly chooses:

- Vehicle routes and city locations.
- Charging, discharging, and SOC.
- Energy bid quantities and prices.
- Upward and downward reserve bids.
- Allocation of cleared quantities to individual vehicles.

The ISO follower clears a network-constrained joint energy and reserve market. See Section 3, PDF pp. 4-8.

The continuous lower-level LP is replaced by KKT conditions. Complementarity is linearized with big-M, and strong duality removes price-times-quantity terms, yielding a single MILP solved with Gurobi under GAMS. See Section 4, PDF pp. 8-9.

### Experiments and reported results

Modified IEEE 39-bus case:

- 24-hour market and one-hour intervals.
- 17-hour passenger-fleet operating window.
- Six symmetric one-hour intercity routes.
- 36 vehicles, 12 initially at each of three stations.
- 500 kWh modified bus capacity and 200 kW charge/discharge limit.
- Network congestion causes the company to move more vehicles toward high-price cities and discharge there.

See Section 5.1, PDF pp. 9-13.

Practical Chinese system:

- 714 buses in the power system, 874 branches, and 213 generators.
- Three passenger stations connected to power-system buses.
- 180 passenger vehicles, 60 initially at each station.
- Energy-only flexible operation loses CNY 16,607.
- Joint energy/reserve participation earns CNY 77,256 because CNY 116,725 reserve revenue offsets a CNY 39,469 energy-market loss.

See Section 5.2 and Table 2, PDF pp. 13-14.

### Assumptions and limitations

- Service is a minimum route-frequency constraint, not exact trip-by-trip timetable coverage.
- One-hour time resolution.
- Stylized city arcs rather than realistic trip compatibility, deadheads, and depot pull-in/pull-out.
- No explicit large-scale charger-occupancy scheduling comparable to an atomic EVSP.
- One strategic fleet leader, not several competing fleet operators.
- Lower-level convexity permits KKT reformulation; a market containing indivisible fleet packages would not.
- Small/moderate vehicle counts and no column-generation scalability study.
- No incentive-compatible settlement, uplift, or coalition analysis.

### Novelty killed

- A generic price-making electric transportation company.
- Joint vehicle routing, charging/discharging, and strategic energy bidding.
- Route changes in response to endogenous network congestion prices.
- Joint energy and reserve participation by mobile storage.
- A bilevel ISO/fleet formulation converted to MILP.

### Exact atomic EVSP opportunity

The defensible distinction is exact timetable service and duty-level market representation:

- Cover every trip exactly once.
- Link trips into feasible vehicle duties with deadheads and depots.
- Represent charging and discharging within each duty.
- Enforce shared charger occupancy.
- Offer complete or partial duties as XOR packages.
- Scale with branch-and-price rather than enumerate individual-vehicle TSN binaries.
- Provide optimality, no-deviation, or equilibrium certificates.

The economic gap is not "vehicles move toward high LMPs"; Lu et al. already show that. The gap is a market and settlement that remains valid when the mobile resource is an exact, nonconvex timetable-covering fleet.

---

## 7. Wang et al. (2024)

### Verified metadata and source

Qi Wang, Chunyi Huang, Chengmin Wang, Kangping Li, and Ning Xie, "Joint optimization of bidding and pricing strategy for electric vehicle aggregator considering multi-agent interactions," *Applied Energy* 360 (2024), 122810. DOI: `10.1016/j.apenergy.2024.122810`.

Local source: `../papers/3.pdf`.

### Actual method and application

A charging-station aggregator interacts with a DSO through day-ahead demand bidding and endogenous AC-based DLMPs, and with EV users through differentiated retail charging prices. EV users select routes and charging stations through a semi-dynamic transportation assignment model.

The power side is a stochastic bilevel model with baseline-load scenarios and an SOCP relaxation of ACOPF. The traffic side is a robust semi-dynamic traffic-assignment model with uncertain OD demand. V2G is not included. See Sections 2-3, PDF pp. 3-7.

The paper defines the loop

\[
\text{charging loads}
\rightarrow \text{DLMPs}
\rightarrow \text{retail charging prices}
\rightarrow \text{user-equilibrium charging loads}.
\]

It invokes Brouwer under assumed continuity and alternates the power-market/pricing model with robust traffic assignment. The paper explicitly states that theoretical convergence cannot be proven. A damping factor limits successive price changes; if iteration fails, the highest-profit iterate is kept as a suboptimal solution. See Section 4.4, PDF pp. 8-9.

### Experiments and reported results

Test system 1 couples a 7-bus radial distribution system with a 4-link transportation system and two charging stations. Test system 2 couples an 18-bus distribution system with a 19-link transportation system and three charging stations.

Using semi-dynamic traffic assignment rather than a simple demand-elasticity approximation changes realized profit from $2.02 thousand to $2.17 thousand in the reported small case. See Section 5.2 and Table 2, PDF p. 10.

Computational results:

- 214 minutes total for test system 1.
- 336 minutes for test system 2.
- 26 and 28 outer iterations.
- Roughly 10% and 12% reported McCormick-envelope error for the two systems.
- Other convex-hull and piecewise-linear approximation errors below 5%.

See Section 5.6 and Table 5, PDF pp. 13-14.

### Assumptions and limitations

- Nonatomic user-equilibrium traffic, not an operated fleet.
- No identified vehicles, mandatory trips, duties, SOC-linked trip chains, depots, or charger scheduling.
- Continuity of optimization-induced mappings is assumed locally.
- No theoretical convergence guarantee.
- Relaxation and approximation errors are nontrivial.
- "Multi-agent" denotes hierarchical DSO/aggregator/users, not competition among multiple strategic fleet aggregators.
- No V2G, payment design, uplift, or coalition stability.

### Novelty killed

- A generic price-to-route/station-to-load-to-price loop.
- Joint wholesale bidding and differentiated retail charging-price optimization.
- Endogenous route and charging-station response to DLMPs.
- A fixed-point framing of coupled power and transportation decisions.
- Robust/stochastic treatment of aggregate traffic and grid uncertainty.

### Exact atomic EVSP opportunity

Exact fleet response is discontinuous and often set-valued because a small price change can replace an entire duty. This is structurally different from the smooth aggregate response assumed in Wang et al.

Promising questions are:

- Can an exact duty oracle compute a certified best response at each price vector?
- Can equilibrium regret be bounded when the response is set-valued?
- Can a learned surrogate predict active duty columns while an exact pricing fallback preserves certificates?
- Can active learning target price regions where fleet schedules switch?
- How do several fleet operators interact strategically rather than one aggregator mediating user equilibrium?

The contribution must be certified combinatorial response or learning of its switching structure, not another damped fixed-point iteration.

---

## 8. Afentoulis and Vagropoulos (2025)

### Verified metadata and source

Konstantinos D. Afentoulis and Stylianos I. Vagropoulos, "Are current demand response baseline designs suitable for electric vehicles? Policy insights from the independent aggregation business model," *Applied Energy* 396 (2025), 126281. DOI: `10.1016/j.apenergy.2025.126281`.

Local source: `../papers/11.pdf`.

### Actual method and application

An independent EV aggregator schedules individual charging sessions and offers upward or downward manual frequency restoration reserve in a rolling 15-minute MILP. Each EV has exogenous connection/departure times, charger rate, battery size, initial SOC, and required departure SOC. See Section 3, PDF pp. 5-6.

The aggregator is a price taker. The experiment assumes perfect fleet and market-price forecasts plus full balancing-offer clearance.

Four real baseline designs are evaluated:

1. Meter-Before-Meter-After (MBMA).
2. HighXofY.
3. Day-Ahead Declarative.
4. Real-Time Declarative.

See Section 2.3, PDF p. 4.

### Experiments and reported results

The rolling experiment covers all 35,040 15-minute intervals of 2021 across 16 combinations of:

- Two real EV fleets.
- Two electricity markets.
- Four baseline methods.

Data details:

- Boulder: 9,937 sessions, 102 charging points, and 714 kW total charging capacity.
- Barnet: 4,470 sessions, 81 charging points, and 567 kW.
- Actual French and Greek day-ahead, imbalance, and mFRR prices.

See Section 4, PDF pp. 6-7.

MBMA and Real-Time Declarative are manipulable:

- MBMA lets the aggregator inflate consumption immediately before an activation sequence, then claim upward flexibility without lowering charging during the credited interval.
- Real-Time Declarative permits an inflated declared counterfactual.
- Reported flexibility reaches 200-300% of charged energy under MBMA and 150-300% under Real-Time Declarative.
- HighXofY and Day-Ahead Declarative are less manipulable, with roughly 75-130% and 70-80% of charged energy reported as flexibility.
- Revenue ranges approximately from EUR 0.13 to EUR 0.43 per kWh charged.
- A 50% user charging-cost discount can be funded by sharing 14-25% of profit under MBMA, 35-55% under HighXofY, 45-66% under Day-Ahead Declarative, and 15-33% under Real-Time Declarative, depending on the market and fleet.

See Sections 5.2-6, PDF pp. 7-13.

### Assumptions and limitations

- Charging sessions and vehicle availability are exogenous.
- No routing, trips, duties, or service constraints.
- Price-taking balancing-market participation.
- No network or endogenous price impact.
- No V2G.
- Perfect forecasts and full bid clearance.
- The paper diagnoses manipulation but does not design a truthful or baseline-free mechanism.

### Novelty killed

- The broad claim that EV aggregators can game demand-response baselines.
- Comparing EV baseline methods on fairness rather than forecast accuracy alone.
- A real-data business case for EV baseline leverage.
- The observation that flexible loads can manufacture credited curtailment without genuine counterfactual flexibility.

### Exact atomic EVSP opportunity

An exact EVSP can define an operationally valid counterfactual: the same trips, vehicles, charger limits, and service quality under a precommitted policy. It can test whether claimed load reduction is additional or merely a rearrangement enabled by baseline construction.

However, an optimizer-generated baseline is still manipulable if the fleet controls the inputs or policy. The mechanism must determine:

- Who defines the counterfactual policy.
- Which information is committed before prices or activation are known.
- Whether payment depends on reported costs, schedules, or measured deviations.
- How to prevent pre-event charging inflation.
- Whether a baseline-free VCG, difference-reward, core-selecting, randomized-control, or synthetic-control design is preferable.

The atomic research gap is incentive design for mandatory fleet service, not simply a more accurate charging forecast.

---

## Cross-paper novelty boundary

| Broad idea | Prior paper that substantially covers it | What remains defensible |
|---|---|---|
| Continuous price-responsive EV charging fixed point | Deori et al. (2018) | Discrete, set-valued exact fleet response and finite-fleet inefficiency |
| Minimum uplift for shifting demand | Zoltowska (2016) | No-deviation uplift against every exact trip-covering fleet schedule |
| Strategic multi-period storage equilibrium | Zou et al. (2016) | Combinatorial fleet equilibrium without KKT reduction |
| VCG and bargaining for flexible storage | Fang et al. (2022) | Exact outside options, per-fleet truthfulness, budget and core stability under indivisibilities |
| Electric-bus service planning with endogenous DLMP | Wu et al. (2019) | Fixed timetable and atomic vehicle duties without sacrificing service |
| Price-making passenger fleet with routes and energy/reserve bids | Lu et al. (2021) | Exact trip cover, charger conflicts, scalable duty-column market clearing, and settlement |
| Price-route-load-price fixed-point iteration | Wang et al. (2024) | Certified discontinuous response, equilibrium regret, and learning with exact fallback |
| EV demand-response baseline gaming | Afentoulis and Vagropoulos (2025) | Baseline-free or manipulation-resistant payments for mandatory fleet operations |

## Integrated atomic-EVSP research architecture

### Layer 1: exact welfare benchmark

Jointly clear generation/network operation and EVSP duty columns. For each duty \(c\), record:

- Trips covered.
- Vehicle/depot compatibility.
- Operating cost.
- Node-time charging and discharging profile.
- Charger occupancy.
- Terminal vehicle state.

The master problem selects duties to cover every trip and clear the power system. Column pricing creates new duties from trip-cover, energy-price, and charger/resource duals.

### Layer 2: price support and no-deviation certificates

Given a dispatched fleet schedule, choose prices and minimum uplifts so every fleet weakly prefers its dispatch to every feasible alternative. Solve the resulting semi-infinite incentive system through exact EVSP separation.

Key outputs:

- Fleet opportunity cost.
- Minimum make-whole payment.
- Which alternative duty schedule causes the uplift.
- Whether LMP alone supports the dispatch.
- Sensitivity to convex-hull or extended prices.

### Layer 3: strategic price-making behavior

Compare several behavioral models rather than presuming one:

- Central social planner.
- Price-taking fleet.
- Single price-making fleet anticipating the market response.
- Multiple strategic fleet operators.
- Sequential exact best-response equilibrium.
- Learned response with exact fallback.

Report welfare, fleet profit, consumer payment, congestion, emissions, and equilibrium regret separately.

### Layer 4: mechanism design

Candidate settlements include:

- LMP only.
- LMP plus minimum uplift.
- Convex-hull or extended-LMP prices.
- VCG with a carefully defined service-preserving outside option.
- Core-selecting or coalition-stable payments.
- Baseline-free flexibility payment.

The mechanism must distinguish optional energy flexibility from mandatory passenger service. Counterfactual removal of the fleet is normally invalid unless a replacement service is explicitly modeled.

### Layer 5: scalable computation and learning

Machine learning should accelerate an exact economic computation rather than replace it without guarantees. Possible uses are:

- Predict promising duty arcs or columns.
- Warm-start price-response and counterfactual solves.
- Identify price regions where the optimal schedule changes.
- Select damping or trust regions adaptively.
- Predict which incentive constraints will bind.

Every learned heuristic should retain a full-network/full-duty pricing fallback so that final welfare, best-response, and no-deviation claims can be certified.

## Recommended central thesis question

> How should a power market clear and compensate mandatory, indivisible electric-fleet schedules so that the allocation is operationally exact, selected fleets have no profitable feasible rescheduling deviation, and payments remain economically defensible under endogenous prices and market power?

This question remains open across the eight audited papers. It also makes the exact EVSP duty structure central to the economics rather than treating the fleet as an interchangeable aggregate battery or traffic flow.
