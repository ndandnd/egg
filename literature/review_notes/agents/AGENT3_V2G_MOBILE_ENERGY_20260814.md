# Research Front 3: V2G + Solar + Storage inside Exact Vehicle Scheduling; Vehicles as Mobile Energy Assets

**Prepared for:** PhD-thesis planning, EVSP with endogenous (price-maker) electricity prices
**Date:** 2026-08-14
**Method note:** All entries below come from live web searches (publisher pages, arXiv, institutional repositories). DOIs are reported **only when literally observed** in a source; where I could not confirm a DOI I give volume/article number instead and mark it. Claims about methods are taken from abstracts/full texts actually retrieved, not inferred.

---

## 1. The closest V2G-EVSP frontier (2022–2026): who does what, and how

**Headline finding.** The V2G + e-bus scheduling literature splits cleanly into two camps: (i) *charging/discharging-only* schedulers that take vehicle-to-trip assignments as fixed (MILP, often with heuristics or robust counterparts), and (ii) *integrated trip + charging* schedulers, which are almost always metaheuristic (ALNS, NSGA-II) or LP-relaxation-based. **No paper found besides the team's own manuscript (Cho–Lodi–Scaglione, arXiv 2508.06752) solves the integrated timetabled-trip + V2G-discharge + microgrid dispatch problem by column generation with duty-level SOC labeling.** No paper in this space uses endogenous (fleet-load-dependent) prices; the closest are bi-level aggregator models where prices are set strategically by another agent (see §6a).

### Key papers

1. **Zhou, X., An, K., Schmöcker, J.-D. (2025).** "Optimization of charging and discharging schedules for battery electric buses under the V2G environment." *Transportmetrica B: Transport Dynamics.* DOI: 10.1080/21680566.2025.2506689.
   Formulates a mixed-integer model for multi-depot BEB charging/discharging with V2G, exploiting "spare" buses (deployed at 2:1 replacement ratios for diesel) to discharge during grid peaks. Solved with adaptive large neighborhood search fused with simulated annealing (ALNS-SA). A cross-line operation strategy on a real Shanghai (Jiading) network cuts total costs 8.5% vs. single-line operation.
   *Relevance:* Metaheuristic, no optimality certificate; prices exogenous. Does allow re-assignment across lines (partial duty flexibility) — the closest heuristic competitor on the transit side.

2. **Son, J., Im, J., Kim, D. (2025).** "Urban transit optimization: Efficient electric bus operations and vehicle-to-grid integration." *Computers & Industrial Engineering* 205. DOI: 10.1016/j.cie.2025.111169.
   Two-stage stochastic optimization over uncertain discharging prices and energy consumption; an LP model for multi-route, multi-depot fleet dispatch plus depot-level charging/discharging with V2G. Demonstrates profitability of strategic V2G under uncertainty.
   *Relevance:* LP → tractable but coarse (no integer duty structure); stochastic prices are exogenous scenarios, not load-responsive.

3. **Kang, M., Min, D., Lee, B., Lee, Y. (2025).** "Optimization of Electric Bus Charging and Discharging Schedules with Vehicle-to-Grid Technology." *Transactions of the Korean Institute of Electrical Engineers* 74(5). DOI: 10.5370/kiee.2025.74.5.761.
   Depot-level MILP maximizing net discharge during peak hours and minimizing operating cost via hierarchical bi-objective treatment; a model-based heuristic for large instances. Trips fixed; depot only.
   *Relevance:* Confirms the pattern — V2G scheduling at depot with MILP+heuristic, no duty optimization, no certificate at scale.

4. **Wu, W., Lin, Y., Liu, R., Jin, W. (2022).** "The multi-depot electric vehicle scheduling problem with power grid characteristics." *Transportation Research Part B* 155:322–347. DOI: 10.1016/j.trb.2021.11.007.
   Bi-objective MDEVSP under TOU tariffs minimizing operating cost and *peak concurrent charging load* (lexicographic), on a time-expanded network, solved by a tailored branch-and-price with embedded heuristics and a trip-chain pool. Guangzhou case study.
   *Relevance:* The reference point for exact-ish EVSP-with-grid-awareness. **No V2G**, and grid impact enters only as a peak-load objective, not as a price feedback. Peak-load minimization is a primitive form of "the fleet affects the grid" — useful positioning: the manuscript replaces this proxy with an actual price/dispatch response.

5. **Fei, F., Sun, W., Iacobucci, R., Schmöcker, J.-D. (2023).** "Exploring the profitability of using electric bus fleets for transport and power grid services." *Transportation Research Part C* 149, art. 104060. (DOI not directly observed.)
   Jointly optimizes bus fleet size, timetable, and charge/discharge exchange plans under two VPP contract types (spot-market-based B2G and FCR reserve contracts), modeling interactions among energy provider, bus operator, and passengers. B2G profitable above ~10 buses; FCR contracts widen the profit gap.
   *Relevance:* The most "market-design-aware" transit V2G paper; still price-taking (contract prices given) and not an exact duty-level method.

6. **Bie, Y., Qin, W., Wu, J. (2024).** "Optimal electric bus scheduling method under hybrid energy supply mode of photovoltaic–energy storage system–power grid." *Applied Energy* 372, art. 123774. DOI: 10.1016/j.apenergy.2024.123774.
   Cooperative model for EB dispatching + charging under PV-ESS-grid supply, decomposed into two subproblems solved by NSGA-II. Reduces charging cost 25.5% and emissions 68.7% vs. grid-only.
   *Relevance:* Integrates dispatch + PV + ESS but is fully metaheuristic; no V2G discharge to grid; no optimality measure.

7. **Liu, X., Yeh, S., Plötz, P., Ma, W., Li, F., Ma, X. (2024).** "Electric bus charging scheduling problem considering charging infrastructure integrated with solar photovoltaic and energy storage systems." *Transportation Research Part E* 187, art. 103572. DOI: 10.1016/j.tre.2024.103572.
   MILP scheduling BEB charging and controlling PV energy simultaneously; variable charging power to align with PV production; heterogeneous batteries, peak-net-charging-power costs, multi-route multi-depot. Beijing case with real trajectories/irradiance.
   *Relevance:* Fixed trips (charging-only); the "peak net charging power cost" term is again a load-dependent cost proxy — an implicit, primitive endogenous-price element. Companion big-data work: Liu et al., "Transforming public transport depots into profitable energy hubs," *Nature Energy* 9:1206–1219 (2024), DOI: 10.1038/s41560-024-01580-0.

8. **Luke, J., de Castro Ribeiro, M.G., Martin, S., Balogun, E., Cezar, G., Pavone, M., Rajagopal, R. (2025).** "Optimal coordination of electric buses and battery storage for achieving a 24/7 carbon-free electrified fleet." *Applied Energy* 377, art. 124506. (SSRN preprint DOI: 10.2139/ssrn.4815427; journal DOI not directly observed.)
   Digital-twin framework coordinating an e-bus fleet, co-located PV and BESS: forecasting modules (marginal grid emissions factors, solar, bus consumption via surrogate model) feed an optimization module for joint bus + battery operations. Stanford Marguerite case: ≥$1.79M 10-yr savings, 98% depot emission cuts; emissions-aware model adds 17% CO2 reduction at $66/tCO2.
   *Relevance:* State of the art for 24/7 CFE fleet coordination; optimization is dispatch-level (not set-partitioning duties), deterministic-forecast driven, no optimality-certified duty generation, no V2G export market.

9. **Terada, L.Z., Magalhães, M.M., Córtez, J.C., Soares, J., Vale, Z., Rider, M.J. (2025).** "Multi-objective optimization for microgrid sizing, electric vehicle scheduling and vehicle-to-grid integration." *Sustainable Energy, Grids and Networks* 43, art. 101773. DOI: 10.1016/j.segan.2025.101773 (also SSRN 10.2139/ssrn.5202657).
   Multi-objective MILP sizing a microgrid (PV, BESS, thermal gen, EVCS) with EV scheduling and V2G; scenario-based stochastic with off-grid contingencies; **V2G service price determined endogenously via a Nash bargaining mechanism** balancing operator and EV-owner interests; linearization avoids charge/discharge binaries.
   *Relevance:* The only paper found in the microgrid-V2G-sizing space with an endogenous price element — but it is a *bargained contract price*, not a fleet-load-dependent market/dispatch price, and "EV scheduling" here means charge-slot scheduling, not timetabled trip-covering duties.

10. **Kızıl, Ünsal, et al. (attribution per IEEE page) (2025).** "Optimal V2G Scheduling of Electric Buses to Mitigate Grid Constraints and Absorb PV Surplus Power." *APPEEC 2025.* DOI: 10.1109/appeec66370.2025.11382080.
    Mixed-integer second-order cone program relaxing ACOPF over 24 h at 5-min resolution: BEBs absorb daytime PV surplus and discharge minimally in the evening to fix voltage/congestion violations, while keeping bus services feasible.
    *Relevance:* First-class **physical network** modeling (voltage, line limits) coupled to bus V2G — but trips fixed, single-day OPF scale, no duty optimization. Complements the manuscript's economic (dispatch-cost) coupling with a physical-feasibility coupling.

11. **Mahmoud, M. et al. (attribution uncertain) (2025).** "A Robust Optimization Approach for E-Bus Charging and Discharging Scheduling with Vehicle-to-Grid Integration." *Mathematics* 13(9):1380. DOI: 10.3390/math13091380.
    Robust MILP for depot charge/discharge with dual-port chargers, emergency charging, demand response; budgeted uncertainty on trip energy consumption and grid discharging requests, dualized to a tractable MILP; out-of-sample tests beat deterministic and box-uncertainty models.
    *Relevance:* The robust-optimization face of the same depot-level frontier; trips fixed, no duties, no endogenous prices.

12. **(Authors not itemized on page) (2025).** "Short-term scheduling optimization of battery electric buses in the context of sustainable energy resources under uncertainty." *International Journal of Electrical Power & Energy Systems*, art. 110715. DOI: 10.1016/j.ijepes.2025.110715.
    Robust MILP + metaheuristics assigning BEBs to charging stations with V2G/G2V trading, renewables, SOC, capacity, and route dynamics; box and polyhedral uncertainty sets on demand/prices.
    *Relevance:* Again MILP+metaheuristic; confirms nobody in this stream certifies optimality.

13. **Wang, Y., Chen, J., Tang, T., Liu, Z. (2024).** "A holistic approach to multi-depot electric bus scheduling for energy saving considering limitations in charging facilities." *Energy* 303, art. 131880. DOI: 10.1016/j.energy.2024.131880. (Seen via citation trail; not independently fetched.)
    *Relevance:* Representative of the non-V2G MDEVSP mainstream the manuscript generalizes.

### Method map (frontier characterization)

| Paper | Trips optimized? | V2G? | PV/ESS? | Method | Certificate? | Price model |
|---|---|---|---|---|---|---|
| Zhou/An/Schmöcker 2025 | partial (cross-line) | yes | no | MILP + ALNS-SA | no | exogenous TOU |
| Son et al. 2025 | dispatch-level | yes | implicit | two-stage stochastic LP | LP only | exogenous scenarios |
| Kang et al. 2025 | no | yes | no | hierarchical MILP + heuristic | small instances only | exogenous peak/off-peak |
| Wu et al. 2022 | yes (duties) | no | no | branch-and-price (+heuristics) | yes-ish | TOU + peak-load objective |
| Fei et al. 2023 | timetable+fleet | yes | no | optimization model (contract-based) | no | contract (SbMP/FCR) |
| Bie et al. 2024 | yes | no | PV+ESS | NSGA-II decomposition | no | TOU |
| Liu et al. 2024 | no | no | PV+ESS | MILP | solver-level | TOU + peak-power cost |
| Luke et al. 2025 | route assignment | no (BESS only) | PV+BESS | forecast+optimize (digital twin) | no | tariff + marginal emissions |
| Terada et al. 2025 | charge slots | yes | PV+BESS | multi-objective MILP, stochastic | solver-level | **Nash-bargained V2G price** |
| APPEEC 2025 | no | yes | PV | MISOCP (ACOPF relaxation) | relaxation | physical grid constraints |
| **Cho–Lodi–Scaglione (ours)** | **yes (duties)** | **yes** | **PV+ESS+fossil** | **column generation, DP pricing** | **≤1% gaps reported** | **microgrid dispatch cost (endogenous supply stack)** |

---

## 2. Battery degradation in V2G scheduling

**Headline finding.** Three degradation-modeling tiers coexist: (i) throughput-linear (constant €/kWh cycled, "wAh" models), (ii) DOD-nonlinear per-cycle wear (wear-density functions, piecewise-linearized), (iii) rainflow cycle counting (RCC) — accurate but non-convex, so it appears in heuristic/DRL/rolling schemes, rarely in exact optimization. Degradation *inside a duty-level pricing subproblem* exists (Zhang et al. 2021; Klein & Schiffer 2023) but **only for charging (G2V) wear — no one prices V2G discharge-cycle degradation inside an exact set-partitioning/labeling framework.** Consensus on economics: degradation is *the* make-or-break term for V2G; V2G flips from unprofitable to profitable at battery replacement costs around 100 €/kWh (Manzolli et al.), and reserve provision beats energy arbitrage largely because it moves fewer Ah.

### Key papers

1. **Zhang, L., Wang, S., Qu, X. (2021).** "Optimal electric bus fleet scheduling considering battery degradation and non-linear charging profile." *Transportation Research Part E* 154, art. 102445. DOI: 10.1016/j.tre.2021.102445.
   Set-partitioning EVSP with degradation cost and nonlinear charging inside the column; tailored branch-and-price with a multi-label correcting pricing method and dual stabilization; global optimality on real transit instances; 10.1–27.3% cost savings mostly from battery-life extension.
   *Relevance:* Proof that degradation can live inside DP/labeling pricing — the direct template for adding V2G-cycle wear to the team's pricing subproblem.

2. **Klein, P.S., Schiffer, M. (2023).** "Electric Vehicle Charge Scheduling with Flexible Service Operations." *Transportation Science.* DOI: 10.1287/trsc.2022.0272 (arXiv: 10.48550/arxiv.2201.03972).
   Exact branch-and-price for joint charging + service-operation scheduling with battery degradation (wear-density function, piecewise-linear), nonlinear charging, TOU tariffs; novel label-setting algorithm with continuous label representation and set-based dominance; instances of 68 vehicles / 5 days in <1 h; integrated scheduling cuts charger needs up to 57%.
   *Relevance:* Methodological gold standard for degradation-aware labeling; departure-time flexibility only (trips pre-assigned) and **no V2G discharge**.

3. **Manzolli, J.A., Trovão, J.P.F., Antunes, C.H. (2022).** "Electric bus coordinated charging strategy considering V2G and battery degradation." *Energy* 254, art. 124252. DOI: 10.1016/j.energy.2022.124252.
   MILP minimizing fleet charging costs with a battery-ageing framework pricing degradation from V2G energy sales; Portuguese 11-bus case. Below ~100 €/kWh battery replacement cost, selling energy becomes attractive; 2030 projection: 38% lower operating costs; V2G TCO 39% below baseline despite earlier battery replacement.
   *Relevance:* The standard economic threshold citation for transit V2G profitability vs. degradation.

4. **Thingvad/collaborators (Energy Informatics) (2023).** "Assessing the incorporation of battery degradation in vehicle-to-grid optimization models." *Energy Informatics.* DOI: 10.1186/s42162-023-00288-x.
   Review + implementation comparing the two families usable in V2G optimization: weighted Ah-throughput models (constant cost factor; linear, optimization-friendly) vs. performance-based models (rainflow on the SOC trajectory with DOD/C-rate stress factors, called in a rolling loop after each linear solve).
   *Relevance:* The clearest taxonomy — supports designing a "linear-in-pricing, rainflow-in-validation" loop for the thesis.

5. **(IEEE Access) (2020).** "Optimization of Bi-Directional V2G Behavior With Active Battery Anti-Aging Scheduling." *IEEE Access.* DOI: 10.1109/access.2020.2964699.
   Quantifies V2G ageing via rainflow cycle counting; multi-objective (degradation + grid-fluctuation) heuristic with multi-population collaboration; minimizes charge/discharge cycles while delivering identical grid services.
   *Relevance:* Representative of the RCC-in-heuristics stream; also of the key insight that *which* SOC trajectory delivers a grid service matters as much as the service itself.

6. **(Energies 17(7):1681) (2024).** "Online Optimization of Vehicle-to-Grid Scheduling to Mitigate Battery Aging." *Energies* 17(7):1681 (mdpi.com/1996-1073/17/7/1681).
   Amplitude-based rainflow counting (MRCC) in a sliding-window online V2G scheduler; cuts equivalent full-cycle counts by 8.4% vs. standard scheduling for 50 EVs.
   *Relevance:* Shows the online/rolling degradation-aware V2G control layer that could sit under a day-ahead exact plan.

7. **Farzin, H., Fotuhi-Firuzabad, M., Moeini-Aghtaie, M. (2016).** "A Practical Scheme to Involve Degradation Cost of Lithium-Ion Batteries in Vehicle-to-Grid Applications." *IEEE Trans. Sustainable Energy* 7(4):1730–1738. DOI: 10.1109/tste.2016.2558500. (Seen via citation trail.)
   *Relevance:* The canonical practical V2G degradation-cost scheme most MILPs adopt.

8. **(IEEE OJIES) (2025).** "MILP Framework for V2G Optimization With Battery Degradation and Price Arbitrage in Scheduled Fleets." *IEEE Open Journal of the Industrial Electronics Society.* DOI: 10.1109/ojies.2025.3613601.
   Production-oriented MILP with day-ahead prices, degradation, grid constraints, per-vehicle granularity and full charging-station topology; Italian market data. V2G and controlled charging both save >35% vs. uncontrolled, but the V2G-vs-smart-charging gap is *narrow* at current battery prices.
   *Relevance:* Recent, careful economics: the marginal value of V2G over smart charging is small unless degradation is cheap — a caution for thesis claims, and an argument for co-optimizing duties (which V2G-only models cannot).

**Degradation → V2G economics, condensed:** throughput-linear models overstate V2G value when cycling is shallow and understate it when deep; DOD-nonlinear/wear-density corrects this at moderate model cost (piecewise-linear); rainflow is the referee. Reserve capacity (rarely activated) monetizes battery *availability* with little throughput and thus survives degradation accounting much better than energy arbitrage (Brinkel 2023; Manzolli 2024, §5/§6).

---

## 3. Solar/renewable uncertainty + fleet scheduling

**Headline finding.** Two-stage designs are established for *charging* (first stage: infrastructure/day-ahead plan; second stage: recourse charging), but two-stage or robust designs over *duties* (recourse = re-covering trips) barely exist — the recourse action is almost always "buy more grid power" or "deploy a diesel bus," never "re-optimize the duty set." 24/7 carbon-free matching for fleets is a Stanford-led niche (Luke et al.) plus an emerging PV-surplus-absorption line in Japan.

### Key papers

1. **(arXiv) (2025).** "Charge Schedule Optimization and Infrastructure Planning for Solar-Integrated Electric Bus Transit Systems." DOI: 10.48550/arxiv.2504.20790.
   Two-stage stochastic LP: first stage sizes charging-station power, BESS, and PV area per location; second stage schedules grid/BESS energy transfers to buses during layovers per scenario (seasonal PV, temperature-dependent consumption, TOU). Solved with Benders decomposition; Durham (Ontario) and Canberra cases; 16–32% savings; scenario-based schedules adapt better than mean-value schedules.
   *Relevance:* The cleanest published two-stage PV+transit design; bus schedules themselves come from a *concurrent-scheduler heuristic*, i.e., duties are exogenous — exactly the gap an exact EVSP layer would fill.

2. **Huang, D., Wang, S. (2022).** "A two-stage stochastic programming model of coordinated electric bus charging scheduling for a hybrid charging scheme." *Multimodal Transportation* 1(1), art. 100006. DOI: 10.1016/j.multra.2022.100006.
   First stage: battery inventory at swap/charge stations; second stage: charging mode/time/location per bus under stochastic trip energy consumption; progressive hedging decomposition.
   *Relevance:* Establishes progressive hedging as a workable decomposition for transit charging recourse.

3. **(Batteries 12(5):167) (2026).** "Day-Ahead Optimal Scheduling for Electric Bus PV-Storage Charging Station Under Uncertainty: An IGDT-Based Approach." DOI: 10.3390/batteries12050167.
   Information-gap decision theory for PV uncertainty with power-dependent (dynamic) charging efficiency linearized by big-M; two-stage bisection over risk-averse LP subproblems.
   *Relevance:* Non-probabilistic robustness (IGDT) as an alternative to scenario trees when PV forecast distributions are untrusted.

4. **Luke et al. 2025 (Applied Energy 377:124506)** — see §1 item 8; the flagship 24/7 CFE fleet paper (hourly marginal emissions matching, PV + BESS + bus ops).
   *Relevance:* Defines the 24/7 CFE benchmark; their optimization is deterministic-forecast-driven with a digital-twin wrapper, no stochastic recourse and no exact duty layer.

5. **Bie et al. 2024 (Applied Energy 372:123774)** — see §1 item 6: PV-ESS-grid supply with weather-condition sensitivity analysis (NSGA-II).
   *Relevance:* PV variability handled by scenario re-runs, not by stochastic programming — typical of the applied stream.

6. **Liu, X., Liu, X.C., Xie, C., Ma, X. (2023).** "Impacts of photovoltaic and energy storage system adoption on public transport: A simulation-based optimization approach." *Renewable and Sustainable Energy Reviews* 181, art. 113319. DOI: 10.1016/j.rser.2023.113319.
   Simulation-based surrogate optimization of PV+ESS configurations at BEB charging stations, day-to-day operations, Beijing; 17.6%/8.8% cost/emission cuts; identifies PV buy-back price as the pivotal parameter.
   *Relevance:* Evidence that *where* PV+ESS is deployed across the network drives system cost — connects to novelty check (c).

7. **D'Ignazio, K.A. (2024).** "The Electric Bus Rostering and Charging Scheduling Problem with Uncertain Energy Consumption: a Two-Stage Stochastic Programming Approach." HEC Montréal MSc thesis (biblos.hec.ca).
   Two-stage MILP: assign buses to blocks + charging plans; recourse = deploy a diesel bus when an e-bus runs short.
   *Relevance:* Rare example where the *transportation-side* recourse is explicit; still block-level, not full duty re-optimization; thesis-level, so the journal niche is open.

8. **Osaki, F., Fujimoto, Y., Iino, Y., Ihara, Y., Mitsuoka, M., Hayashi, Y. (2025).** "Dynamic bus charge scheduling by model predictive control to maximize local PV surplus power utilization." *eTransportation* 25, art. 100441. DOI: 10.1016/j.etran.2025.100441. (Seen via citation trail.)
   *Relevance:* MPC recourse layer for PV-surplus absorption — the operational complement to day-ahead exact planning.

---

## 4. Vehicles as mobile energy assets (MESS, resilience, spatial energy transport)

**Headline finding.** Three distinct literatures, none of which couples timetabled *passenger service* with spatial energy transport: (i) MESS/portable storage in distribution/transmission grids (power-systems venues; time-space networks inside MILP/stochastic programs; economics now well quantified); (ii) e-buses/school buses as emergency assets (newest work uses **branch-and-price** — see Dolatabadi et al. 2025, the single most method-adjacent paper found); (iii) spatial LMP arbitrage by moving vehicles (Crozier et al.; He et al. Joule). **Novelty check on "timetabled passenger service + spatial energy transport": no paper found. Confirmed open.**

### 4a. MESS in distribution grids

1. **Yao, S. (et al.) (2020).** "Rolling Optimization of Mobile Energy Storage Fleets for Resilient Service Restoration." *IEEE Transactions on Smart Grid.* DOI: 10.1109/tsg.2019.2930012.
   Rolling-horizon two-stage stochastic MILP coordinating MESS fleet scheduling, microgrid dispatch, and network reconfiguration after blackouts; MESS mobility modeled by a stochastic multi-layer time-space network; road/branch damage scenarios via Monte Carlo.
   *Relevance:* Canonical MESS reference; the time-space-network + stochastic-MILP pattern is exactly what a "duty = column" reformulation could beat on scalability.

2. **He, G., Michalek, J., Kar, S., Chen, Q., Zhang, D., Whitacre, J.F. (2021).** "Utility-Scale Portable Energy Storage Systems." *Joule* 5(2). DOI: 10.1016/j.joule.2020.12.005 (arXiv precursor 1811.09924: Tesla-Semi-mounted Powerpacks arbitraging two congested California nodes).
   Spatiotemporal decision model for trucked storage in California: mobilizing storage raises life-cycle revenue up to 70% in some areas and relieves local transmission congestion; spatiotemporal arbitrage alone can fully recover system cost in San Diego / Bay Area.
   *Relevance:* Establishes the economic case that *moving* batteries beats parking them where congestion is transient — buses do this movement for free as a by-product of service.

3. **(arXiv) (2023).** "Mobile Energy Storage in Power Network: Marginal Value and Optimal Operation." DOI: 10.48550/arxiv.2303.09704.
   Theory paper: joint grid + mobile-storage-fleet operation; the marginal value of mobile storage is computed analytically from LMPs and transportation costs; conditions under which mobile storage is worth strictly more/less than stationary storage + wires; algorithms using only LMP trajectories.
   *Relevance:* Gives the *duality/pricing lens* on mobile storage — directly compatible with a column-generation view where duals of grid-node energy-balance constraints price a duty's spatial energy movements.

4. **Harvard Business School working paper (Rana et al. data) (2025).** "Moving Money Around: Mobile Energy Storage and the Value of Geospatial Flexibility." (hbs.edu, no DOI observed; companion Kleinman Center brief.)
   Six years of PJM nodal prices at 339 nodes: each storage entrant cannibalizes incumbent profit ($7,820/MW-yr on average); MESS beats best-sited stationary storage by 11–47% profit and captures 22.5% more congestion value; 9.9–15 GWh of mobile capacity profitable in PJM alone.
   *Relevance:* Empirical scale of the spatial-arbitrage prize; also a warning that arbitrage value is *self-eroding* — a price-maker (endogenous-price) model is the right tool to capture that erosion, which price-taking MESS models ignore.

### 4b. E-buses / school buses as resilience assets

5. **Hosseini Dolatabadi, S.H., Dong, Y., Bhuiyan, T.H., Zeng, B., O'Neill, B., Severson, A. (2025).** "Leveraging Electric School Buses for Disaster Recovery: Optimizing Routing and Energy Scheduling via Branch-and-Price." arXiv: 2510.14131 (UT San Antonio + U. Pittsburgh + San Antonio Fire Dept.).
   MIP for routing/scheduling heterogeneous electric school buses shuttling energy between charging stations and critical isolated loads (hospitals, shelters) during outages, with multiple back-and-forth trips, continuous SOC tracking, shelter–bus-type compatibility; **exact B&P and heuristic B&P with DP/labeling pricing**, 121–335× faster than Gurobi; San Antonio case; one bus effectively delivers 4.5× its usable capacity over a horizon.
   *Relevance:* **The most method-similar external paper found anywhere in this scan**: column-based exact optimization of vehicles *moving energy spatially*. It has no passenger timetable, no market prices, no PV/microgrid co-dispatch — but it proves the B&P machinery works for spatial energy logistics and will likely be extended. Watch this group.

6. **(Building and Environment) (2024).** "Resilience and environmental benefits of electric school buses as backup power for educational functions continuation during outages." *Building and Environment*, art. 112329. DOI: 10.1016/j.buildenv.2024.112329.
   V2B assessment across nine U.S. climate regions: current ESB fleets cannot power whole schools; quantifies required fleet sizes; V2B beats diesel backup on emissions; recommends pairing with stationary batteries.
   *Relevance:* Feasibility envelope for the resilience use case (what battery-to-load ratios actually work).

7. **Li, et al. / Wu, et al. (survey via Dolatabadi's related-work) —** islanded-microgrid support by rented e-buses (MILP, CPLEX), bi-level e-bus network topology + traffic path models (GA), distributed EB-company frameworks (ADMM).
   *Relevance:* Confirms all prior EB-resilience work is fixed-schedule or heuristic; the B&P paper above is the frontier.

8. **Masrur (2017), Miramar/LBNL (2025)** — already in the team's bibliography (military microgrid V2G); the ESB/civilian work above is the natural comparison set.

### 4c. Spatial price arbitrage by moving vehicles

9. **Crozier, C., et al. (2023, extended version of a 2022 IEEE conference paper).** "Spatial Arbitrage Through Bidirectional Electric Vehicle Charging with Delivery Fleets." arXiv: 2311.11464.
   Deterministic and single-stage stochastic frameworks optimizing charging, discharging, and *travel* of electric delivery trucks under spatial + temporal LMP uncertainty (ERCOT nodal data); delivery obligations as constraints; fleet-wide coordination raises profit substantially vs. stationary arbitrage (headline up to ~47.7%), but only when inter-nodal price spreads are large and forecastable.
   *Relevance:* **Direct precedent for "vehicles deadhead to arbitrage locational prices"** — with freight, not timetabled passenger service; single-stage stochastic LP, no set-partitioning, no optimality certificates, price-taking.

10. **(University of Cambridge repository) (2025).** "A multi-objective evolutionary algorithm with constraint-compliant initialization for energy transport and urban logistics in Electric Vehicle Routing" (VRPTW-ET).
    Defines the Vehicle Routing Problem with Time Windows integrated with Energy Transport: EVs serve customers while transporting energy to (dis)charging facilities; NSGA-II variant; up to 30% energy-cost and 20% fleet reductions vs. decoupled baselines.
    *Relevance:* Names the "energy transport inside routing" problem class; entirely heuristic — an exact CG treatment would leapfrog it.

11. **(IEEE TITS) (2026).** "A Graph-Benders Decomposition for Integrated Electric Trucks Routing, Cargo Loading, and V2G Scheduling." DOI: 10.1109/tits.2026.3707595.
    MILP integrating e-truck routing, cargo loading (multiple knapsack), and V2G; Graph-Benders: routing master + V2G scheduling subproblem with feasibility/optimality/no-good cuts; "high-quality near-optimal" (not certified optimal) solutions in seconds where Gurobi times out at 10,000 s on 127k-variable instances.
    *Relevance:* The nearest *exact-framework* competitor for integrated routing+V2G — but freight routing (not trip-covering duties), Benders (not CG), and explicitly near-optimal.

---

## 5. Ancillary services by scheduled fleets

**Headline finding.** Reserve provision by bus fleets is studied at the depot/aggregator level with the timetable as a *fixed availability filter* (buses parked = capacity). Nobody re-optimizes duties to *create* reserve deliverability, and nobody certifies deliverability jointly with the schedule. The Nordic "P90" rule gives a concrete regulatory hook for chance-constrained deliverability tied to a timetable.

1. **Brinkel, N., Zijlstra, M., van Bezu, R., van Twuijver, T., Lampropoulos, I., van Sark, W. (2023).** "A comparative analysis of charging strategies for battery electric buses in wholesale electricity and ancillary services markets." *Transportation Research Part E* 172, art. 103085. DOI: 10.1016/j.tre.2023.103085.
   Simulates charging-on-arrival, peak shaving, day-ahead optimization ±V2G, and FCR/aFRR provision for three Qbuzz depots (NL). Peak shaving cuts charging costs 23–32%; day-ahead adds 6–11%; aFRR participation cuts costs 90–100%+; but FCR/aFRR delivery can create severe local grid peaks.
   *Relevance:* The benchmark economics: reserves ≫ arbitrage for bus fleets; also flags the grid-impact externality of reserve delivery — an endogenous-price/-constraint argument.

2. **El-Taweel, N.A., Ayad, A., Farag, H.E.Z., Mohamed, M. (2022/2023).** "Optimal Energy Management for Battery Swapping Based Electric Bus Fleets With Consideration of Grid Ancillary Services Provision." *IEEE Trans. Sustainable Energy* 14(2):1024–1036. DOI: 10.1109/tste.2022.3232696.
   Battery-swap station as MW-scale storage co-providing bus energy and ancillary services, **with distribution-network voltage/line constraints and explicit timetable satisfaction**; saving-cost index quantifies degradation impact of AS provision.
   *Relevance:* Closest to "reserve deliverability against the timetable" — but via swappable batteries (decoupling buses from packs), which sidesteps the hard duty-coupling problem.

3. **(DTU MSc thesis) (2025).** "Maximizing revenue from ancillary services provided by electric buses" (backend.orbit.dtu.dk).
   MILP bidding aggregated depot charging capacity into DK2 FCR-D and aFRR at 15-min resolution over a week; unidirectional only (no V2G); simulates activation against historical signals, tracks SOC mismatch and re-planning.
   *Relevance:* Shows the state of practice: reserve bids are shaped by the timetable but never reshape it; SOC-mismatch re-planning is done ex post, not endogenously.

4. **(IEEE TTE) (2024).** "Optimal Electric Bus Charging and Battery Swapping With Renewable Energy and Frequency Control Ancillary Service Through Aggregator." *IEEE Trans. Transportation Electrification.* DOI: 10.1109/tte.2024.3445830.
   Aggregator methodology for multi-area bus charging stations: operational planning + interior-point charging optimization with PPA-sourced renewables and frequency-control AS, respecting network constraints; Berlin route data on CIGRE MV benchmark.
   *Relevance:* Multi-station, network-constrained AS by bus fleets — again with fixed bus operations.

5. **(arXiv) (2024).** "Leveraging P90 Requirement: Flexible Resources Bidding in Nordic Ancillary Service Markets." DOI: 10.48550/arxiv.2404.12807.
   Distributionally robust joint chance-constrained bidding for aggregators under Energinet's P90 rule (bids may fail with ≤10% probability); EV-aggregator case.
   *Relevance:* The natural formal container for "reserve deliverability against a stochastic timetable": a P90-style joint chance constraint whose feasibility set is the *duty schedule*.

6. **Fei et al. 2023** (§1 item 5) — FCR-contract profitability from the *bus operator's* perspective with timetable co-optimization at the planning level.
   *Relevance:* The only paper found that lets AS revenue feed back into timetable/fleet design; coarse model, no deliverability certification.

---

## 6. Novelty checks (explicit verdicts)

### (a) V2G e-bus scheduling with endogenous / market-mediated prices?

**Verdict: not found in the EVSP/transit literature; exists only in adjacent forms.** The three adjacent forms are:
- **Bi-level EV-aggregator ↔ market clearing** (price endogenous via lower-level clearing, KKT/MPEC reformulations): established in power systems for generic EV fleets since at least González Vayá & Andersson (2015), "Optimal bidding of plug-in electric vehicle aggregator in day-ahead and regulation markets," *IJEHV* 7(3):209–232 (endogenous DA price impact + V2G + regulation, Switzerland case); price-maker VPPs with EV fleets (e.g., IEEE ECAI 2023, DOI: 10.1109/ecai58194.2023.10193892); bilevel EVA two-stage market participation (semanticscholar PDF, nodal clearing in lower level).
- **Bi-level aggregator ↔ bus-fleet operator**: Manzolli, J.A., et al. (2024), "Aggregator-supported strategy for electric bus fleet charging: A hierarchical optimisation approach," *Energy*, art. 132497, DOI: 10.1016/j.energy.2024.132497 — upper level sets buy/sell/capacity prices, lower level is the PTO's charge/discharge MILP (Lozano–Smith style decomposition; robust variants). Prices are *strategically set*, and the bus fleet remains a price-taker at the lower level with **fixed trips**.
- **Nash-bargained V2G price** in microgrid sizing: Terada et al. 2025 (§1 item 9).
**Nobody makes the timetabled duty optimization itself price-making** (i.e., fleet charging/discharging load moves the marginal supply price which re-prices every duty). The manuscript's microgrid supply-stack coupling, and any wholesale-market extension of it, remain unclaimed territory. Note also the weaker cousins already in transit literature that should be cited as such: peak-load objectives (Wu 2022), peak-net-charging-power costs (Liu 2024), demand charges (arXiv 2509.05940) — all are load-dependent *cost* terms, not price formation.

### (b) Exact / certified column generation for V2G-EVSP other than the team's manuscript?

**Verdict: none found.** Searches for branch-and-price / column generation + V2G + vehicle scheduling return: (i) the team's own arXiv 2508.06752; (ii) Klein & Schiffer (B&P, charging-only, no V2G); (iii) Wu et al. 2022 (B&P, no V2G); (iv) Dolatabadi et al. 2025 (B&P, energy logistics, no timetable/no market); (v) Graph-Benders e-truck routing + V2G (near-optimal Benders, freight). The closest *certified* claims are Klein & Schiffer and Zhang et al. 2021 — both G2V-only. **The manuscript's claim of first CG-based EVSP+V2G(+microgrid) appears safe as of this scan (2026-08), but the ESB-B&P group (UTSA/Pitt, Bo Zeng) and the TITS Graph-Benders group are converging on the same toolbox.**

### (c) Joint optimization of WHERE to charge/discharge across network nodes + timetabled duties + locational price differences?

**Verdict: not found as a combination.** Pieces exist separately: (i) charging-location choice inside EVSP (CLP-EVSP-CSP, arXiv 2403.09763, MILP + iterated local search; GERAD G-2024-28, B&P for EVSP + fast-charger location); (ii) locational price/congestion awareness (APPEEC 2025 MISOCP; Chalmers integrated BEB + distribution-network study; Wu 2022 peak load); (iii) locational arbitrage by moving vehicles (Crozier; He/Joule; HBS MESS). **No paper prices charging/discharging *differently by node* inside a timetabled duty-generation subproblem.** A duty-level labeling algorithm whose reduced costs include node- and time-indexed duals from a networked dispatch/OPF layer would be new.

### (d — bonus) Timetabled passenger service + spatial energy transport?

**Verdict: open.** Dolatabadi et al. (school buses) is the nearest miss — school buses explicitly *not* doing passenger service during the emergency. Crozier et al. couple freight deliveries (time windows, not timetables). Nobody treats "carry passengers on trip A, then deadhead 2 km to the constrained substation-adjacent charger and discharge" as a joint decision.

---

## Novelty threats (ranked)

1. **Dolatabadi, Dong, Bhuiyan, Zeng, O'Neill, Severson (arXiv 2510.14131, Oct 2025).** Exact B&P with DP/labeling for school buses moving energy spatially. If they add passenger timetables, market prices, or PV/microgrid dispatch, they collide with the thesis's themes 4/6. *Mitigation: cite, differentiate on timetabled service + endogenous prices + microgrid co-dispatch; move fast on the "energy logistics + timetable" extension.*
2. **Manzolli et al. 2024 (Energy, 10.1016/j.energy.2024.132497) + the 2025 OJIES MILP + the agentic-aggregator arXiv (2606.26400).** The Coimbra/aggregator line already has bi-level *price formation* around e-bus fleets and is actively productizing. If they swap their fixed-trip lower level for a duty-scheduling lower level, they get "endogenous prices + duty optimization" via MPEC instead of CG. *Mitigation: emphasize certificates and integrated duty generation, which MPEC lower levels cannot deliver at scale.*
3. **Graph-Benders e-truck routing + V2G (IEEE TITS 2026, 10.1109/tits.2026.3707595).** An exact decomposition framework for integrated vehicle-operations + V2G already exists for freight; porting to trip-covering transit is incremental for that group. *Mitigation: their method is explicitly near-optimal (no-good cuts, LP-relaxed subproblem); a certified CG/B&P with SOC labeling is a stronger claim — state it.*
4. **Klein & Schiffer (TS 2023) lineage.** The TUM group has the best labeling machinery (continuous labels, set-based dominance, degradation, nonlinear charging). Adding discharge arcs to their networks is technically straightforward; only problem framing (they focus on depot charge scheduling) has kept them away. *Mitigation: the microgrid/price-maker coupling is the moat, not the labeling.*
5. **Zhou/An/Schmöcker and the Schmöcker–Kyoto cluster (Zhou 2025; Fei 2023).** They own the "transit V2G economics" narrative in transportation journals and iterate quickly; a follow-up with duty-level optimization or market feedback is plausible. *Mitigation: they are metaheuristic-first; publish the exactness + endogenous-price angle before they do.*
6. **APPEEC 2025 MISOCP line (PV surplus + grid constraints).** Physical-network V2G bus scheduling could be upgraded to include duties; power-systems venues move fast. *Threat level lower: OPF scale forces fixed trips for now.*

## Open gaps

1. **Endogenous price formation inside duty pricing.** No work anywhere makes the *pricing subproblem's* arc costs respond to the fleet's own aggregate load (supply stack, demand charge curvature, or market clearing). The manuscript's microgrid version is the first instance; the wholesale/price-maker generalization (bi-level or supply-function) is untouched.
2. **V2G-cycle degradation inside exact pricing.** Degradation-aware labeling exists for charging only (Zhang; Klein–Schiffer). Discharge arcs make wear costs depend on the *joint* SOC trajectory — nonadditive along the path — an open labeling/dominance question (bounded-DOD labels, wear-density with V2G, or Lagrangian-relaxed rainflow).
3. **Duty-level recourse under PV/price uncertainty.** Two-stage models fix duties and let charging (or diesel substitution) absorb shocks. Two-stage stochastic column generation where second-stage columns re-cover trips is unexplored for EVSP-V2G.
4. **Reserve deliverability certified against the timetable.** P90-style joint chance constraints on reserve availability, where the feasible set is the duty schedule itself (buses can be re-blocked to guarantee deliverability), does not exist. All current AS work treats parked-bus capacity as a residual.
5. **Spatial energy transport by timetabled fleets.** Confirmed open (§6d). Includes the "energy deadheading" question: when is it optimal to insert a non-service leg purely to move stored energy to a higher-value node?
6. **Self-erosion of arbitrage value.** MESS economics (HBS) shows storage entry cannibalizes spreads; every price-taking V2G-fleet paper overstates revenue at scale. Only a price-maker fleet model quantifies this correctly — a strong motivation paragraph for the thesis.
7. **Network-node-differentiated charging/discharging duals in duty generation** (novelty check c) — no incumbent.
8. **Optimality-gap reporting culture.** Outside Wu/Zhang/Klein–Schiffer, essentially no paper in this space reports gaps; a systematic benchmark (public instances, gaps, LP bounds) would itself be a citable contribution.

## Creative ideas (research-idea sketches)

1. **Price-maker EVSP-V2G via convex supply stack in the master.** Keep set-partitioning columns; replace linear energy cost with a convex piecewise-linear supply curve (microgrid generators or residual-demand curve of a market). The master stays LP; duals of the time-indexed energy-balance rows become time-varying *endogenous prices* fed to DP pricing. Column generation converges to a fleet-level market equilibrium with a certificate — formalize this as "CG = Walrasian tâtonnement over duty space" and compare to bi-level MPEC baselines (Manzolli-style) on cost and scalability.
2. **Locational duals in pricing (answers novelty c).** Add a multi-node microgrid/distribution layer (linearized DistFlow) in the master; each charger sits at a node. The labeling algorithm sees node-and-time-indexed reduced costs, so a duty organically decides *where* to charge/discharge given congestion. Deliverable: first exact "locational V2G-EVSP"; case study with the Swedish bus data + a synthetic feeder, quantifying the value of locational awareness vs. uniform prices.
3. **Energy-deadheading duties / timetabled MESS (answers novelty d).** Extend the duty network with "energy ferry" arcs: deadhead legs to remote nodes whose only purpose is discharge. Theoretical component: conditions (spread ≥ wear + deadhead cost + driver cost) under which ferry arcs enter the optimal basis, echoing the marginal-value theory of arXiv 2303.09704 but with service-coverage constraints. Marketing frame: "the bus network as a virtual transmission line."
4. **Degradation-consistent V2G labeling.** Develop dominance rules for labels carrying (SOC, accumulated wear proxy) with a DOD-nonlinear wear-density function valid under both charge and discharge; prove correctness for monotone wear densities; validate ex post with rainflow (Energy Informatics 2023 loop). This directly generalizes Zhang 2021 / Klein–Schiffer to bidirectional power.
5. **Two-stage stochastic CG with trip-recovery recourse.** First stage: duties + committed V2G/reserve profile; second stage (per PV/price scenario): recourse columns that re-cover trips and re-schedule charging. Solve by nested CG or CG + progressive hedging (Huang–Wang precedent); measure the "value of duty recourse" vs. charging-only recourse — expected to be large exactly when V2G commitments are aggressive.
6. **P90-certified reserve-by-timetable.** Joint chance constraint: "in ≥90% of scenarios, committed reserve is deliverable given the realized timetable/SOC." Distributionally robust version per arXiv 2404.12807; the schedule (not just the bid) is the decision. Sell to both OR (new constraint class in B&P) and power (first deliverability-certified transit reserve product).
7. **Self-cannibalization study: V2G fleet at scale.** Using the price-maker model of idea 1, sweep fleet size and quantify how per-bus V2G revenue decays as the fleet's own discharge depresses peak prices (the HBS/PJM effect endogenized). Deliverable: a "V2G revenue adequacy curve" for transit agencies — a policy-relevant, easily-cited artifact no price-taking model can produce.
8. **Resilience option value of timetabled fleets.** Combine the manuscript's microgrid setting with Dolatabadi-style islanding events: duties must remain feasible while reserving enough mobile energy to serve critical loads in a rare-event scenario tree. Prices the option value of the fleet-as-backup *without* dedicated MESS capex; military and school-district cases both apply.
9. **Swap-station arbitrage vs. duty coupling.** El-Taweel shows swappable packs decouple grid services from vehicle motion. A clean comparison — plug-in V2G duties (coupled) vs. battery-swap depot (decoupled) under identical timetables and endogenous prices — would identify when the *coupling* the thesis handles is actually worth its algorithmic cost. Honest, referee-friendly framing.
10. **Benchmark + open instances.** Publish EVSP-V2G-microgrid instances (Swedish bus data derivative + solar traces + supply stacks) with LP bounds and gaps, positioned as the "Solomon instances" of V2G-EVSP. Cheap to do from existing assets; buys citations and sets the evaluation standard competitors must meet (where most are metaheuristics with no bounds).

---

## Appendix: adjacent items worth having on file

- Perumal, S.S.G., et al. (2022) e-bus planning review — already in team bibliography; frames EVSP taxonomy.
- Zhou, Y., Meng, Q., Ong, G.P., Wang, H. (2024). "Electric bus charging scheduling on a bus network." *TRC* 161, art. 104553. DOI: 10.1016/j.trc.2024.104553 (network-level charging scheduling, no V2G).
- Zhou, Y., Wang, H., Wang, Y., Yu, B., Tang, T. (2024). "Charging facility planning and scheduling problems for battery electric bus systems: A comprehensive review." *TRE* 183, art. 103463. DOI: 10.1016/j.tre.2024.103463.
- (TRC 2023) "Integrated optimization of electric bus scheduling and charging planning incorporating flexible charging and timetable shifting." DOI: 10.1016/j.trc.2023.104175 — CG first stage + timetable-shifting second stage to cut peak power; another "peak proxy" instance.
- Parmentier, A., Martinelli, R., Vidal, T. (2023). "Electric Vehicle Fleets: Scalable Route and Recharge Scheduling Through Column Generation." *Transportation Science* 57(3):631–646. DOI: 10.1287/trsc.2023.1199 — the scalability toolbox (multigraph reformulation, bidirectional pricing, sparsification, diving) most transferable to the thesis codebase.
- Lam, M. (via INFORMS IJOC 2024/2025). "The Electric Vehicle Routing and Overnight Charging Scheduling Problem on a Multigraph." DOI: 10.1287/ijoc.2023.0404 — branch-price-and-cut with charging-schedule feasibility; relevant labeling tricks.
- (MICE 2024) "On the role of time-of-use electricity price in charge scheduling for electric bus fleets." DOI: 10.1111/mice.13134 — TOU-only baseline, up to 22% savings.
- (arXiv 2509.05940 / Research Square 10.21203/rs.3.rs-8884872/v1, 2025) Brussels 28-bus integrated MILP with PV+ESS+V2G+demand charges+degradation via discrete-event optimization: PV+ESS −56% cost; all extensions −58%; V2G marginal unless degradation cheap. Fixed trips. *Best single "everything-in-one-depot" MILP to benchmark against.*
- Milan V2G feasibility (IEEE Access 2023). DOI: 10.1109/access.2023.3279713 — depot-level deliverable-energy accounting given service obligations (7–10 MW from two Milan depots).
- IFP Energies HAL working paper (hal-03898558): millions-of-EV smart charging flattens residual demand and *prices* — system-level evidence that fleet load moves prices (motivation for price-maker modeling).
