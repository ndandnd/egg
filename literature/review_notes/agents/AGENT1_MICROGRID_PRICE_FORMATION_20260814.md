# Research Front 1: Price Formation and Market/Coordination Mechanisms in Microgrids (with Large EV/Fleet Loads)

**Prepared for:** PhD-thesis planning — "price-maker EVSP" project (timetabled, duty-based, exact EVSP inside market-mediated price formation; microgrids where the fleet is a dominant load; spectrum from benevolent-dictator co-optimization to decentralized price-mediated operation).

**Method note:** All evidence below is **abstract-level** (titles, abstracts, and search-result snippets seen via web search on 2026-08-14). Full texts were not audited on this pass. DOIs are reported **only where they appeared verbatim in search results**; where no DOI was visible, a URL or bibliographic string is given instead. Venue names are as seen in the search results and should be re-verified before citation in the thesis.

---

## Theme 1 — Transactive energy and local energy markets (LEMs) in microgrids: how prices are formed

**State of the field (abstract-level synthesis).** Price formation in microgrid-scale markets falls into five recurring families: (i) **single/double auctions** (uniform-price, average, VCG, McAfee, trade-reduction rules); (ii) **system-determined pricing** (supply-demand-ratio rules, internal tariffs at the point of common coupling bounded by retail buy/sell prices); (iii) **negotiation/bilateral P2P**; (iv) **equilibrium/optimization-based pricing** (marginal-cost/dual-variable prices from a welfare-maximizing dispatch, incl. DLMP variants); and (v) **hierarchical/Stackelberg operator-set pricing**. The transactive-energy (TE) tradition (GridWise/PNNL) adds "value as key operational parameter" plus a control layer.

### Key papers

1. **Hammerstrom, D.J., et al. (2008). "Pacific Northwest GridWise Testbed Demonstration Projects; Part I. Olympic Peninsula Project." PNNL-17167, Pacific Northwest National Laboratory.** (Companion conference paper: Chassin, Hammerstrom, DeSteese, IEEE PES GM 2008, DOI: 10.1109/PES.2008.4596723.)
   - Seminal field demonstration of a retail **double-auction market cleared every 5 minutes** coordinating residential water heaters/thermostats, a commercial building, municipal water pumps, and distributed diesel generators to manage a constrained feeder. Generators bid start-up cost/minimum-runtime-aware offers; uncurtailable load bid at a price cap; the clearing price was broadcast back to all bidders. Demonstrated that price is an effective control signal for congestion at the feeder scale.
   - *Relevance:* the canonical existence proof of feeder-scale, market-cleared price formation — the mechanism a "price-maker EVSP" depot would bid into; note that diesel gensets bidding startup/min-runtime logic anticipates the unit-commitment-like pricing the project needs.

2. **"Market Mechanisms and Trading in Microgrid Local Electricity Markets: A Comprehensive Review." Energies 16(5):2145, 2023. DOI: 10.3390/en16052145.**
   - Abstract-level: systematic review of the "market layer" of microgrids: market design, mechanism, players, and pricing mechanisms; also covers distributed-ledger implementations and the mathematical structure of objective functions.
   - *Relevance:* best single starting survey to position an internal microgrid market for a fleet-dominated microgrid.

3. **Energy Systems TCP GO-P2P Annex, "Peer-to-Peer, Community Self-Consumption and Transactive Energy: A Systematic Literature Review of Local Energy Market Models" (2022, userstcp.org PDF).**
   - Systematic review of 139 papers; of these, only 53 even specified their price-formation mechanism; classifies mechanisms into single auction, double auction, system-determined, negotiation-based, equilibrium-based. Notes almost all P2P work targets **small residential prosumers**, with EVs appearing only occasionally as small participants.
   - *Relevance:* documents both the taxonomy of local price formation and the absence of large timetabled fleet actors in LEM studies — direct support for the project's gap claim.

4. **Cornélusse, B., Savelli, I., Paoletti, S., Giannitrapani, A., Vicino, A. (2019). "A community microgrid architecture with an internal local market." Applied Energy. DOI: 10.1016/j.apenergy.2019.03.109.**
   - Community microgrid with an **internal local market cleared by marginal pricing** (welfare maximization); a "community microgrid operator acting as a benevolent planner" redistributes revenues/costs so no member is worse off than standalone operation. Formulated as a **bilevel model** (lower level clears the market; upper level does the redistribution). Belgian test case, ~54% annual community savings.
   - *Relevance:* the closest structural template to the project's "benevolent-dictator ↔ market spectrum": it shows how the same physical co-optimization can be re-expressed as a cleared market plus transfers. No vehicles, no scheduling — the fleet-side is entirely missing.

5. **"Transactive Energy: State-of-the-Art in Control Strategies, Architectures, and Simulators." IEEE Access, 2021. DOI: 10.1109/access.2021.3115154.**
   - Reviews TE control strategies in a four-level hierarchy; centralized/decentralized/distributed/hierarchical architectures; and TE simulators. Anchored in the GridWise Architecture Council definition of TE.
   - *Relevance:* provides the architecture vocabulary (which layer sets prices, which layer responds) for describing where an EVSP oracle sits in a TE stack.

6. **"A Review of Peer-to-Peer Energy Trading Markets: Enabling Models and Technologies." Energies 17(7):1702, 2024. DOI: 10.3390/en17071702.**
   - Abstract-level: taxonomy of P2P clearing rules — average, VCG, trade-reduction, McAfee; continuous vs periodic vs k-double auctions.
   - *Relevance:* the menu of implementable auction rules if the depot is made a bidder in a local double auction.

7. **"Trustful double auction design for Peer-to-Peer energy trading between interconnected micro-grids with supply–demand imbalance." International Journal of Electrical Power & Energy Systems, 2024. DOI: 10.1016/j.ijepes.2024.110117.**
   - Two-stage double auction (intra-MG then inter-MG) with incentive compatibility, individual rationality, budget balance; fair allocation of power-loss costs.
   - *Relevance:* representative of mechanism-design-grade auction work at microgrid scale; all participants are small prosumers — no scheduling-constrained large bidder.

8. **"Pricing and Energy Trading in Peer-to-Peer Zero Marginal-Cost Microgrids." IEEE Transactions on Smart Grid, 2021. DOI: 10.1109/tsg.2021.3122879.**
   - Shows that in 100%-renewable community microgrids, **optimal (marginal-cost) pricing is insufficient to induce battery owners to act optimally** — a fundamental degeneracy of marginal prices under zero-marginal-cost supply — and proposes a P2P negotiation algorithm converging to the centralized welfare optimum.
   - *Relevance:* a warning directly applicable to the project: in a solar+storage depot microgrid, marginal prices may be degenerate/non-supporting, so the naive "post duals from the co-optimization as prices" decentralization may fail — a research question in itself.

9. **"Stochastic Energy Management of Microgrid with Nodal Pricing." Journal of Modern Power Systems and Clean Energy. DOI: 10.35833/mpce.2018.000519.**
   - Computes internal **nodal prices (DLMP-style, from dual variables of an OPF)** within a microgrid, then schedules local resources and flexible loads against those prices.
   - *Relevance:* precedent for "internally formed" microgrid prices via duals — but loads are generic, not vehicle duties.

**Also noted (Theme 1):** "Simulation Analysis of a Double Auction-Based Local Energy Market in Socio-Economic Context" (Sustainability 14(13):7642, 2022, DOI: 10.3390/su14137642 — agent-based uniform-price double auction, socio-economic outcomes); "Exposing a locational energy market to uncertainty" (IJEPES, 2025, DOI: 10.1016/j.ijepes.2025.111285 — agent-based locational LEM for DC systems with EV-user bidding under range anxiety); PNNL TE practices surveys PNNL-33252 and PNNL-34505; Dynge et al., "Local electricity market pricing mechanisms' impact on welfare distribution, privacy and transparency," Applied Energy 341:121112, 2023, DOI: 10.1016/j.apenergy.2023.121112 (seen in citation lists).

---

## Theme 2 — Microgrids where EV charging is a dominant load: bus depots, charging hubs, depot energy management

**State of the field.** A rapidly growing 2023–2026 literature treats the **bus depot or charging hub as a microgrid** (PV + stationary storage + chargers + grid connection, occasionally diesel/islanded operation). Optimization is almost universally **single-owner MILP/MPC cost minimization against an exogenous tariff** (ToU + demand charges, sometimes day-ahead prices). None of the works found forms prices internally or models the depot's load moving any price. Several very recent papers co-optimize **bus scheduling + depot energy infrastructure**, which converges toward the team's OPTE manuscript from the transit side.

### Key papers

1. **"Co-Design Optimization and Total Cost of Ownership Analysis of an Electric Bus Depot Microgrid with Photovoltaics and Energy Storage Systems." Energies 17(24):6233, 2024 (mdpi.com/1996-1073/17/24/6233).**
   - Co-design (sizing) of a **depot microgrid** with PV+ESS for three European cities; compares energy-management strategies incl. a hardware-in-the-loop validation; ~30% reduction in charging-related TCO vs grid-only. Charging schedules come from a high-level charging-management system; prices are **exogenous tariffs** (ESS does ToU arbitrage).
   - *Relevance:* representative "depot = microgrid" paper; explicit that prices are taken, not formed.

2. **"Optimizing bus charging infrastructure by incorporating private car charging demands and uncertain solar photovoltaic generation." npj Sustainable Mobility (Nature Portfolio), 2024. DOI: 10.1038/s44333-024-00021-5.**
   - Bus depot with PV+BES sized/scheduled under PV uncertainty; opens the depot to private EVs as a revenue stream; minutely charging events, charger availability constraints.
   - *Relevance:* depot as an "energy hub" with third-party demand — a proto-market (the depot sells charging) but at fixed prices; suggests an entry point for endogenous pricing of third-party access.

3. **"An Integrated Optimization Framework for Smart Charging of Electric Bus Fleets under Dynamic Electricity Prices with On-Site Solar Generation, Energy Storage, and V2G operations." arXiv, 2025. DOI: 10.48550/arxiv.2509.05940.**
   - MILP for a real Brussels network (28 articulated buses, 232 trips): dynamic tariffs, demand charges, battery degradation, PV, ESS, V2G. Finds up to 58% cost reduction with all components; ESS used mainly for arbitrage. Prices fully **exogenous**.
   - *Relevance:* the most complete recent "everything-in-the-depot" optimization; a natural baseline/benchmark structure for the project's price-taking limit case.

4. **"Coordinated Optimization of Cross-Line Electric Bus Scheduling and Photovoltaic–Storage–Charging Depot Configuration." Energies 19(7):1791, 2026. DOI: 10.3390/en19071791.**
   - **Joint MILP over bus scheduling (cross-line) and depot PV/storage/charger configuration**, solved by Benders decomposition; explicitly criticizes the literature for optimizing depot energy systems and bus schedules separately; fleet shrinks from 17 to 14 buses under co-optimization; storage value tied to ToU peak arbitrage.
   - *Relevance:* the transit community is actively converging on "co-optimize schedule + depot energy assets" — the deterministic, price-taking version of the team's problem. Novelty must therefore rest on **price formation**, not on co-optimization per se.

5. **"Development of a Cost-Driven, Real-Time Management Strategy for e-Mobility Hubs Including Islanded Operation." Energies 17(17):4229, 2024. DOI: 10.3390/en17174229.**
   - E-mobility hub as a microgrid (dispatchable + PV generation, BESS, EVSE, local loads) with a centralized controller supporting **dynamic pricing and demand-response mechanisms as business models**; HIL-validated; islanded and connected modes.
   - *Relevance:* rare explicit mention of hub-internal dynamic pricing as a business model, but implemented as controller rules, not equilibrium price formation.

6. **"Scenario-Based Stochastic MPC for Energy Hubs with EV Fleets Under Persistent Grid Outages." arXiv, 2026. DOI: 10.48550/arxiv.2604.18268.**
   - Campus energy hub (Ashesi University, Ghana) with solar, battery, diesel backup, EV fleet, weak grid with Markov-chain outages; stochastic MPC within 1% of perfect-forecast benchmark; naive MPC no better than rule-based control.
   - *Relevance:* fleet-in-microgrid operation under unreliability — the "weak grid/islanded" regime where internal price formation (diesel marginal cost vs free solar) is most economically meaningful.

7. **"A comparative analysis of charging strategies for battery electric buses in wholesale electricity and ancillary services markets." Transportation Research Part E 172, 2023 (ideas.repec.org: S136655452300073X).**
   - Compares charging-on-arrival, peak-shaving, day-ahead optimization ± V2G, FCR/aFRR provision for three real Dutch depots (Qbuzz); aFRR participation can offset nearly all charging cost but can worsen local grid peaks.
   - *Relevance:* depots already participate in *wholesale/ancillary* markets as price takers; the local-market/price-maker angle remains open.

8. **"Analyzing the flexibility potential of bus fleet operators in Germany." Smart Energy, 2024. DOI: 10.1016/j.segy.2024.100153.**
   - 80-bus depot as a "storage aggregator" (mobile + stationary) participating optimally in short-term electricity and balancing markets; includes battery-degradation economics; historical 2020–2022 data.
   - *Relevance:* quantifies depot flexibility as a market resource — but again price-taking and without timetable-level scheduling detail.

**Price-assumption verdict (Theme 2):** every depot/hub study found assumes **exogenous prices** (flat, ToU, day-ahead spot, demand charges). The only internal "prices" are controller heuristics. No study lets the depot's schedule move a price that then feeds back into the schedule.

---

## Theme 3 — DLMP at small scale: charger siting/timing, feeder/campus congestion, locational value of charging flexibility

**State of the field.** DLMP work is mature: the DSO computes nodal prices from an OPF (often SOCP/linearized DistFlow duals) and EV aggregators respond, either as price takers in an iterative loop (ADMM-style DSO↔aggregator negotiation) or inside bilevel formulations. The EV load model is essentially always an **aggregate energy/power envelope**, never a duty-covering combinatorial schedule.

### Key papers

1. **Li, R., Wu, Q., Oren, S.S. (2014). "Distribution Locational Marginal Pricing for Optimal Electric Vehicle Charging Management." IEEE Transactions on Power Systems 29(1):203–211. DOI: 10.1109/tpwrs.2013.2278952.**
   - Seminal DLMP-for-EVs paper: DSO solves social-welfare optimization; EV aggregators are **price takers**; shows the socially optimal charging schedule is implementable decentrally by posting DLMPs.
   - *Relevance:* the canonical "prices decentralize the optimum" result the project would generalize to integral, duty-constrained fleet loads (where it may fail — duality gap).

2. **Liu, Z., Wu, Q., Oren, S.S., Huang, S., Li, R., Cheng, L. (2018). "Distribution Locational Marginal Pricing for Optimal Electric Vehicle Charging Through Chance Constrained Mixed-Integer Programming." IEEE Transactions on Smart Grid 9(2):644–654. DOI: 10.1109/tsg.2016.2559579.** (seen in citation lists)
   - DLMP with chance constraints and integer decisions for EV charging management.
   - *Relevance:* early evidence that integrality inside DLMP loops is recognized as hard; still aggregate EV models.

3. **Bai, L., Wang, J., Wang, C., Chen, C., Li, F. (2017). "Distribution Locational Marginal Pricing (DLMP) for Congestion Management and Voltage Support." IEEE Transactions on Power Systems 33(4):4061–4073. DOI: 10.1109/tpwrs.2017.2767632.** (seen in citation lists)
   - Standard DLMP decomposition (energy, loss, congestion, voltage components).
   - *Relevance:* price-component anatomy useful for attributing which part of the depot's price impact comes from congestion vs energy.

4. **"Transactive-Based Day-Ahead Electric Vehicles Charging Scheduling." IEEE Transactions on Transportation Electrification, 2024. DOI: 10.1109/tte.2023.3348490.**
   - EV aggregators optimize parking-lot charging/discharging, bid into a DSO **transactive market-clearing that iteratively computes DLMPs**; Monte Carlo + robust treatment of uncertainties; IEEE-33 node feeder.
   - *Relevance:* state-of-the-art DSO↔EV-aggregator iterative price formation — the fleet is a parking lot, not a timetabled fleet.

5. **"DLMP-Based Congestion Management Model for Power Distribution Network Considering Network Loss and EV Charging Demand Uncertainty." IEEE Transactions on Smart Grid, 2025. DOI: 10.1109/tsg.2025.3631315.**
   - Two-layer iterative DSO↔EVA coordination; inner ADMM iterates DLMPs preserving aggregator privacy; robust ambiguity sets for EVA behavior.
   - *Relevance:* the algorithmic template (iterate prices ↔ loads to a fixed point) that the project would instantiate with an exact EVSP oracle as the load-response map.

6. **"DLMP Calculation and Congestion Minimization With EV Aggregator Loading in a Distribution Network Using Bilevel Program." IEEE Systems Journal, 2020. DOI: 10.1109/jsyst.2020.2997189.**
   - **Bilevel with the EV aggregator as leader** and DSO welfare maximization as follower (KKT/duality single-level reformulation) — i.e., a *strategic* (price-anticipating) EV aggregator against DLMPs.
   - *Relevance:* closest DLMP work to "EV load as price-maker"; aggregator is still an energy envelope, no vehicle duties, no integrality in the leader.

7. **Wu, Z., Guo, F., Polak, J., Strbac, G. (2019). "Evaluating grid-interactive electric bus operation and demand response with load management tariff." Applied Energy 255:113798. DOI: 10.1016/j.apenergy.2019.113798.**
   - **The single most important prior for this project.** Bi-level model: upper level = electric **bus service planning** (opportunity charging flexibility tied to bus mobility over a network, tempo-spatial energy needs), lower level = **electricity market clearing with DLMP** for congestion management; real bus-network data; finds e-bus DR reduces losses 7.2% but that restricted bus operations limit load-shifting (8.17% charging-demand loss; +10.57% battery reliance).
   - *Relevance / threat:* this paper already couples electric bus operation with market-clearing-formed (DLMP) prices in one bilevel model. At abstract level it is *not* an exact duty-based set-partitioning EVSP (appears to be a service-planning/scheduling LP-MILP hybrid) and not a microgrid (distribution network), but any novelty claim must be phrased to survive this paper. **Full-text audit strongly recommended.**

8. **"Integrating Variable Distribution Use-of-System Tariffs and Local Flexibility Markets through a Bilevel Modelling Approach." (DTU / EV4EU project paper, 2024, ev4eu.eu PDF).**
   - Bilevel: DSO designs time/space-differentiated network tariffs *and* runs a capacity-limitation local flexibility market; **EV-aggregator followers** with smart charging respond; real 47-node network.
   - *Relevance:* shows tariff-design and local-market instruments being co-designed against EV aggregators — the regulatory-instrument side of the project's design space.

**Also noted (Theme 3):** "DLMP-Based Quantification and Analysis Method of Operational Flexibility in Flexible Distribution Networks" (IEEE Trans. Sustainable Energy, 2022, DOI: 10.1109/tste.2022.3197175 — DLMP as a *flexibility price*); "Electric Vehicle Charging Implications on Distribution Locational Marginal Prices" (EEM 2024, DOI: 10.1109/eem60825.2024.10608919 — quantifies EV-induced DLMP rises on IEEE-34).

---

## Theme 4 — Islanded/isolated microgrids (islands, military bases, remote communities) with EV fleets

**State of the field.** Coordination is essentially always **central dispatch / EMS optimization** (deterministic or stochastic MILP/MINLP/metaheuristic): diesel unit commitment + renewables + storage + EV charging (sometimes V2G). No internal market-like price formation was found in any islanded-microgrid-with-EV paper; at most, an "EV aggregator" negotiates with the system operator. This is exactly the regime where fleet load is *structurally* dominant (small systems), so the absence of price-formation studies is a clear gap.

### Key papers

1. **Cho, Lodi, Scaglione (2025). "Electric Vehicle Scheduling and Vehicle-to-Grid Integration in Microgrids." arXiv:2508.06752. DOI: 10.48550/arxiv.2508.06752.** *(the team's own manuscript — publicly visible and indexed)*
   - Military-microgrid EVSP+V2G via column generation (LP master + pricing + restricted master MIP); minimizes fuel-generated electricity while covering mission-critical transport.
   - *Relevance:* baseline. Note the arXiv version is discoverable and already surfaces in searches for "islanded microgrid EV fleet" — the thesis must differentiate the *new* direction (price formation / decentralization spectrum) from this benevolent-planner formulation.

2. **Clairand, J.-M., et al. (2020). "Power Generation Planning of Galapagos Microgrid Considering Electric Vehicles and Induction Stoves." / two-level EV charging + generation-planning study for Santa Cruz Island, Galapagos. Energies 13(13):3455 (mdpi PDF: energies-13-03455).**
   - Two-level problem: (1) EV charging strategy minimizing cost and maximizing renewable use, managed by an **EV aggregator interacting with the system operator**; (2) impact on island generation planning (diesel + renewables).
   - *Relevance:* an early "fleet load shapes islanded dispatch" study; sequential (not equilibrium/market) coordination; aggregate private EVs, not a scheduled fleet.

3. **"Multi-Objective Dispatching Optimization of an Island Microgrid Integrated with Desalination Units and Electric Vehicles." Processes 9(5):798, 2021 (mdpi.com/2227-9717/9/5/798).**
   - PV/wind/diesel/battery island microgrid with EV and desalination flexibility; multi-objective (cost + net-load fluctuation) via grey-wolf metaheuristic.
   - *Relevance:* representative central-dispatch treatment; no prices at all internally.

4. **"Synergic integration of desalination and electric vehicle loads with hybrid micro-grid sizing and control: An Island Case Study" (Bruny Island, Australia). Energy Storage (Wiley), 2020. DOI: 10.1002/est2.104.**
   - MILP sizing/scheduling of island microgrid with V2G EVs, desalination, load deferral; storage-form comparison.
   - *Relevance:* shows EVs treated as one of several storages under a single planner.

5. **"Energy Management of Multi-Area Islanded Hybrid Microgrids: A Stochastic Approach." IEEE Access, 2023. DOI: 10.1109/access.2023.3313259.**
   - Stochastic (Monte Carlo + scenario reduction) MINLP dispatch of islanded AC/DC microgrid with diesel active/reactive cost, RES, BESS, EV charging uncertainty; metaheuristic solution.
   - *Relevance:* the standard coordination answer in islanded settings — stochastic central dispatch, exogenous everything.

6. **Military demonstrations: (a) "Optimized V1G and V2G Electric Vehicle Fleet Management and Grid Transaction at Marine Corps Air Station Miramar" (OSTI technical report 2580493); (b) "Los Angeles Air Force Base Vehicle-to-Grid Demonstration" (LBNL final report, DOI: 10.2172/2274679); (c) "Optimal Allocation of Solar PV Generation and Energy Storage Systems in a Military Microgrid including V2G Operation" (IEEE SEFET 2025, DOI: 10.1109/sefet65155.2025.11255576); (d) Lai, K., Zhang, L. "Sizing and Siting of Energy Storage Systems in a Military-Based Vehicle-to-Grid Microgrid," IEEE Trans. Industry Applications 57(3):1909–1919, 2021, DOI: 10.1109/tia.2021.3057339.**
   - LA AFB: DER-CAM-based fleet scheduling co-optimizing base tariff costs and CAISO frequency-regulation revenue while maintaining travel capability. Miramar: six bidirectional V2G vans in a building-scale microgrid providing demand management and simulated DR. SEFET/TIA papers: staged optimization to displace diesel with ESS/PV/V2G on bases.
   - *Relevance:* real military fleet-microgrid deployments; all price-taking against retail tariffs or wholesale markets; coordination by optimization software, no internal price formation.

7. **Arctic/remote-community line: "Are Electric Vehicles a Solution for Arctic Isolated Microgrid Communities?" World Electric Vehicle Journal 16(3):128, 2025 (mdpi.com/2032-6653/16/3/128); "Off the grid and on the fence: Unpacking electric vehicle adoption barriers in isolated microgrids." Energy Research & Social Science, 2025. DOI: 10.1016/j.erss.2025.104281; NSF "EVITA" project (Kotzebue/Galena, Alaska).**
   - Diesel-powered isolated Alaskan microgrids; EV cost/emission outcomes hinge on diesel price pass-through, renewable share, and **rate structures** (subsidized charging rates flip the economics); EVITA is actively modeling EV charging impacts on Arctic diesel microgrids.
   - *Relevance:* empirically grounds "the fleet's electricity price is endogenous to the microgrid's dispatch" (diesel marginal cost vs free wind/solar), and shows tariff design (not markets) is the current coordination instrument in practice.

**Also noted (Theme 4):** seaport microgrids as fleet-dominated logistics-energy systems: "Optimal power scheduling of seaport microgrids with flexible logistic loads" (IET Renewable Power Generation, 2022, DOI: 10.1049/rpg2.12401); Mao et al., "Optimal scheduling for seaport integrated energy system considering flexible berth allocation," Applied Energy 308:118386, 2021, DOI: 10.1016/j.apenergy.2021.118386; and notably **Sun, Y., Guo, Y., Zhang, Q., Jia, Y. "Berth allocation and energy scheduling for all-electric ships in seaport microgrid: A Stackelberg game approach." Energy 322:135640, 2025. DOI: 10.1016/j.energy.2025.135640** — a *logistics-scheduling* problem (berth allocation) coordinated with a seaport microgrid via a **Stackelberg game**, i.e., the nearest analogue in another domain to "timetabled operations + game-mediated microgrid prices". Full-text audit recommended.

---

## Theme 5 — Strategic behavior INSIDE microgrids / local markets: large flexible loads exercising market power

**State of the field.** Three strands: (i) **Stackelberg operator-vs-prosumer pricing** inside microgrids (operator sets internal buy/sell prices; prosumers respond) — ubiquitous since ~2017; (ii) **strategic storage/DER market power** (withholding, bid shading) mostly at wholesale, recently at LEM/oligopoly level; (iii) **price-maker EV aggregators** — a well-developed *wholesale* literature (bilevel/MPEC), essentially absent at local/microgrid level, and never with timetabled duties.

### Key papers

1. **Liu, N. (et al.). "Distributed game-based pricing strategy for energy sharing in microgrid with PV prosumers." IET Renewable Power Generation, 2017/2018. DOI: 10.1049/iet-rpg.2017.0570.**
   - Stackelberg game: microgrid operator (leader) sets internal buy/sell prices; PV prosumers (followers) choose consumption/sharing; existence/uniqueness of equilibrium proven; distributed algorithm.
   - *Relevance:* the archetypal internal-price-setting microgrid game the project could adopt as the "market layer," replacing toy followers with an EVSP-constrained fleet.

2. **"A reverse Stackelberg model for demand response in local energy markets." European Journal of Operational Research, 2025. DOI: 10.1016/j.ejor.2025.06.017.**
   - DSO computes affine tariff functions (upper level) to steer a generalized Nash equilibrium among prosumers (lower level) to operationally efficient outcomes; Nikaido–Isoda reformulation; IEEE feeders.
   - *Relevance:* OR-methodological state of the art for tariff design steering strategic agents in LEMs — a template for "design the internal tariff so the fleet's optimal EVSP is system-optimal."

3. **"Powering sustainability: Analyzing local energy market equilibrium with energy storage and renewable resources in oligopolistic grids." Journal of Energy Storage, 2025. DOI: 10.1016/j.est.2025.119406.**
   - Day-ahead LEM equilibrium with oligopolistic players (incl. DSO); shows **even small-capacity resources exert market power in thin local markets**, causing price swings and welfare loss; regulatory recommendations.
   - *Relevance:* directly supports the project's premise that a dominant depot load in a small market will be a price-maker, and that this matters for welfare — but the strategic players here are generators/storage/DR, not fleets.

4. **"Battery Operations in Electricity Markets: Strategic Behavior and Distortions." arXiv, 2024. DOI: 10.48550/arxiv.2406.18685.** (companion PDF shows Price-of-Anarchy bounds 9/8–4/3)
   - Closed-form model of a strategic (monopoly) battery: quantity withholding, day-ahead→real-time shifting, reduced responsiveness; bounded welfare loss; competition mitigates.
   - *Relevance:* the cleanest theory of *storage-like* market power; a scheduled V2G fleet is a "battery with duty constraints," so these distortion taxonomies are the natural hypotheses to test with an EVSP oracle.

5. **"Market Power and Withholding Behavior of Energy Storage Units." arXiv, 2024. DOI: 10.48550/arxiv.2405.01442.**
   - Framework to distinguish competitive vs market-power withholding by storage; price-sensitivity (linear supply function) model; ex-post monitoring test for operators.
   - *Relevance:* provides a market-power *monitoring* lens — an interesting experiment: would a cost-minimizing (non-strategic) depot look like it is "withholding" to such tests?

6. **"Integration of DERs in the Aggregator Platform for the Optimal Participation in Wholesale and Local Electricity Markets." (IET conference, 2021). DOI: 10.1049/icp.2021.1657.**
   - Bilevel model of a DER aggregator acting as **price-maker in the local electricity market** (LEM cleared by welfare maximization at lower level) while price-taking in wholesale.
   - *Relevance:* the only found instance of an explicit price-maker *in a local market* via bilevel programming — the strategic asset is generation/storage, not a vehicle fleet. Closest mechanism-side prior for novelty check (b).

7. **Price-maker EV-aggregator (wholesale-level) line:**
   - **Vayá, M.G., Andersson, G. (2015). "Optimal bidding of plug-in electric vehicle aggregator in day-ahead and regulation markets." Int. J. Electric and Hybrid Vehicles 7(3):209–232** — bilevel; aggregator demand endogenously moves day-ahead prices.
   - **"Risk-constrained offering strategies for a large-scale price-maker electric vehicle demand aggregator." IET Smart Grid, 2020. DOI: 10.1049/iet-stg.2019.0210** — price-quota-curve MILP + GA, three-settlement market.
   - **"An Optimized Decision Model for Electric Vehicle Aggregator Participation in the Electricity Market Based on the Stackelberg Game." Sustainability 15(20):15127, 2023. DOI: 10.3390/su152015127** — two-stage bilevel EVA-vs-ISO with KKT/duality single-leveling; price-taker vs price-maker scenarios compared.
   - *Relevance:* establishes "EV load as price-maker" is well-trodden at wholesale with **aggregate flexibility envelopes**. The project's distinguishing features must be: (a) timetabled duty-covering EVSP (integral, combinatorial) as the load model, (b) microgrid/local price formation, (c) exact CG machinery.

8. **Fleet bidding with trip-level detail (price-taking):**
   - **"Bidding and Charging Scheduling Optimization for the Urban Electric Bus Operator." IEEE Transactions on Smart Grid, 2022. DOI: 10.1109/tsg.2022.3197429** — EB operator bids energy+reserve using a **trip-chain-based flexibility-region model** aggregated across buses; stochastic hierarchical optimization + accelerated Benders.
   - **Duan, X., Hu, Z., Song, Y. "Bidding Strategies in Energy and Reserve Markets for an Aggregator of Multiple EV Fast Charging Stations With Battery Storage." IEEE Trans. ITS 22(1):471–482, 2020. DOI: 10.1109/tits.2020.3019608** (seen in citations).
   - **"Optimal Charging Schedule Planning for Electric Buses Using Aggregated Day-Ahead Auction Bids." Energies 14(16):4727, 2021 (mdpi.com/1996-1073/14/16/4727)** — MILP aggregation of bus fleet into min/max hourly energy bids for a day-ahead auction (Ohio State campus case); trips/timetables respected in aggregation and disaggregation stages.
   - **"When Agents Meet Electric Bus Fleet Operations: Pricing Behavior, Trade-offs, and Policy Implications in an Aggregator Framework." arXiv:2606.26400 (2026)** — LLM-agent aggregator setting charging-price/V2G-compensation multipliers over a PTO scheduling model; DA/RT workflows.
   - *Relevance:* the transit-fleet literature has reached "timetable-aware market *bidding*" but always **price-taking into an exogenous auction**; the aggregation → bid → disaggregation pipeline (Energies 2021) is exactly the interface a price-maker version would need to break open.

**Verdict (Theme 5):** strategic behavior inside microgrids is studied for operators, prosumers, storage, and generic DER aggregators. **No paper was found where a timetabled vehicle fleet exercises market power in a local/transactive market.**

---

## Theme 6 — Explicit novelty checks

### (a) "Transactive/local market microgrid + timetabled vehicle scheduling" — does any paper couple the two?
- **No exact match found.** Closest priors, in decreasing order of threat:
  1. **Wu, Guo, Polak, Strbac 2019 (Applied Energy, 10.1016/j.apenergy.2019.113798):** bi-level electric-bus *service planning* ↔ DLMP market clearing on a distribution network. Not a microgrid, and (at abstract level) not an exact set-partitioning EVSP, but it *is* "bus operations coupled to market-formed prices." Must be cited and differentiated in any thesis/paper.
  2. **Yao, Liu, Scaglione, Bekhor, Zhang 2025 (arXiv:2505.04532), "Integrated equilibrium model for electrified logistics and power systems":** ELO schedules/routes e-trucks in response to LMPs; PSO sets LMPs by DC-OPF; **fixed-point equilibrium** (existence proof; Anderson acceleration; Hawaii case). This is the price→schedule→load→price loop *formalized*. It differs from the project in: PU-MDP behavioral fleet model (not exact duty-based CG EVSP), transmission-level LMP (not microgrid/local market), no timetabled trip-covering constraints, no V2G/microgrid assets. **Important: shares an author (Scaglione) with the team's own manuscript — internal coordination needed so the thesis positions itself relative to this line rather than colliding with it.**
  3. **Sun et al. 2025 (Energy, 10.1016/j.energy.2025.135640):** berth allocation + energy scheduling in a seaport microgrid via Stackelberg game — timetable-like logistics decisions coordinated game-theoretically with a microgrid, in the maritime domain.
- Conclusion: the specific combination "**exact, duty-based, trip-covering EVSP (CG/RCSPP pricing) embedded in microgrid-internal price formation**" appears unclaimed, but the *broad* combination "fleet operations + endogenous prices" is now occupied by at least two groups (Imperial College 2019; Scaglione et al. 2025). Novelty claims must be scoped precisely.

### (b) "EV fleet strategic bidding in a local energy market"?
- **Not found for fleets.** Found: DER-aggregator price-maker in an LEM (10.1049/icp.2021.1657); oligopolistic LEM equilibria with storage/DR (10.1016/j.est.2025.119406); EV *aggregator* price-maker at wholesale (bilevel/MPEC line, e.g., 10.1049/iet-stg.2019.0210, 10.3390/su152015127); EB operator *price-taking* bidding with trip-chain flexibility (10.1109/tsg.2022.3197429). The intersection "trip-chain/duty-constrained fleet" × "local market" × "price-anticipating" is open.

### (c) "Microgrid marginal price feedback to fleet schedule iteration"?
- **Not found in microgrids.** The generic pattern exists: DSO↔EVA ADMM/DLMP iterations (10.1109/tsg.2025.3631315, 10.1109/tte.2023.3348490); transmission-level fleet↔LMP fixed point (arXiv:2505.04532); dual-consensus economic dispatch exchanging only prices (10.1109/tsg.2020.3018622). Nobody iterates "microgrid dispatch duals → EVSP re-solve → new load → new duals," and nobody has studied convergence/cycling of such a loop when the load-response map is the argmin of an *integer* set-partitioning problem (discontinuous best-response — a real theoretical question).

---

## Novelty threats (things the project must NOT claim as new)

1. **"Coupling fleet/bus operations with market-formed electricity prices" in general** — occupied by Wu et al. 2019 (bi-level bus operation + DLMP clearing) and Yao/Scaglione et al. 2025 (logistics↔LMP fixed-point equilibrium). Claim must be narrowed to: *exact, timetabled, duty-based EVSP (set-partitioning + CG/RCSPP)* inside *microgrid-internal* price formation.
2. **"EV load as price-maker"** — a decade of wholesale bilevel/MPEC EV-aggregator literature (Vayá & Andersson 2015 onward) endogenizes price impact of EV demand. Novelty lies only in the *load model* (duties, integrality) and the *market scale* (microgrid/local).
3. **"Internal microgrid market cleared at marginal cost with a benevolent operator redistribution"** — Cornélusse et al. 2019 already built exactly this architecture (bilevel, welfare-maximizing internal market, planner-mediated transfers). The project's "benevolent dictator ↔ market" spectrum should cite this as the no-vehicles precedent.
4. **"Depot/hub as microgrid co-optimization (PV+ESS+charging+V2G, even with bus scheduling)"** — dense 2024–2026 literature (Energies 17(24):6233; arXiv:2509.05940; Energies 19(7):1791 with Benders-decomposed joint scheduling+sizing). Also the team's own arXiv:2508.06752. Co-optimization per se is not novel; endogenous price formation is the differentiator.
5. **"Timetable-aware market bidding by bus fleets"** — trip-chain flexibility aggregation and day-ahead auction bidding already exist (IEEE TSG 2022 10.1109/tsg.2022.3197429; Energies 14(16):4727), including reserve markets and V2G. These are price-takers, but they own the "timetables meet markets" phrasing.
6. **"Strategic storage / withholding distorts prices"** — well-developed theory with PoA bounds (arXiv:2406.18685, 2405.01442); a V2G fleet behaving strategically will be seen as a special case unless duty constraints are shown to change the qualitative conclusions.
7. **"DLMP guides EV charging; DSO↔aggregator iterative price loops; bilevel EV-aggregator-vs-DSO"** — all standard (10.1109/tpwrs.2013.2278952; 10.1109/tsg.2025.3631315; 10.1109/jsyst.2020.2997189).
8. **"Transactive microgrid double auctions incl. EV participants"** — Olympic Peninsula (2008) onward; EV-centric microgrid double-auction comparisons exist (10.1007/s40866-023-00178-x).

## Open gaps (things nobody appears to do)

1. **Exact EVSP as the demand-side oracle in any price-formation loop.** All price-feedback work uses aggregate envelopes, MDP/behavioral models, or LP flexibility regions. Nobody uses a set-partitioning/CG EVSP (with SOC and charging arcs) as the best-response map — and hence nobody has confronted the **integer, discontinuous best-response** in equilibrium computation or proven anything about existence/convergence there.
2. **Microgrid-internal price formation with a fleet-dominant load.** Depot-microgrid papers all take prices; islanded-microgrid EV papers all centrally dispatch; LEM papers have no timetabled loads. The "diesel-vs-solar marginal-price regimes seen by a mission-constrained fleet in an islanded microgrid" question is untouched.
3. **The centralization spectrum itself.** No paper quantifies, on one physical system, the welfare gap between (i) benevolent-planner co-optimization, (ii) posted internal marginal prices with a price-taking fleet, (iii) a price-anticipating (strategic) fleet, and (iv) an auction/negotiation mechanism. (Cornélusse et al. do (i)-(ii) without vehicles; battery-PoA papers do (i)-(iii) without duties or networks.)
4. **Non-existence/degeneracy of supporting prices under integrality.** Zero-marginal-cost microgrids already break marginal pricing for storage (10.1109/tsg.2021.3122879); adding an integral duty-covering load makes Walrasian support harder still (duality gap of the set-partitioning master). Nobody has characterized when duals from the CG master are (or are not) implementable internal tariffs, or connected this to convex-hull/IP pricing ideas at microgrid scale.
5. **Market-power measurement for duty-constrained loads.** Withholding tests exist for storage; no analogue for a fleet whose "withholding" may be indistinguishable from timetable feasibility. Regulatory implications (should a municipal bus depot in a small LEM be mitigated?) unexplored.
6. **Timetable/service-design as a market-power instrument** — the possibility that a fleet reshapes *which trips/duties exist* (deadheads, depot choice, charging location) to move local prices has no literature at all.
7. **Mechanism design for a single dominant, combinatorial bidder.** LEM auction papers assume many small bidders; nothing on auction/tariff design when one bidder's valuation is the value function of an NP-hard scheduling problem (combinatorial bids = duties/columns).

## Creative ideas (research-idea sketches connecting microgrid price formation with an exact EVSP oracle)

1. **"CG-in-the-loop" fixed-point microgrid equilibrium.** Formalize the map Φ: price profile λ → (EVSP via column generation) → charging/discharging load → (microgrid economic dispatch / UC of gensets+storage) → new duals λ'. Study existence of fixed points (Kakutani on the convexified master vs failure under integrality), cycling, and damping/averaging schemes (cf. Anderson acceleration in arXiv:2505.04532). Deliverable: conditions under which the benevolent-planner solution (the OPTE manuscript) is *exactly* a fixed point — i.e., when prices decentralize the co-optimization — and counterexamples when it is not.
2. **One system, four regimes ("the decentralization ladder").** On the same military-microgrid instance family as arXiv:2508.06752, compute and compare: (R1) integrated co-optimization; (R2) iterated posted marginal prices with price-taking fleet; (R3) strategic fleet (bilevel: fleet leader anticipates microgrid dispatch — an MPEC whose lower level is the dispatch LP, solvable by KKT/duality single-leveling, with the fleet's CG kept exact via Benders or branch-and-price on the leader); (R4) double-auction/transactive clearing (Olympic-Peninsula-style 5-min or hourly market) with the depot bidding aggregated duty-flexibility bids (adapting the Energies 14(16):4727 aggregation to be *incentive-relevant*). Report the "price of decentralization" and "price of anarchy of a duty-constrained battery" against the R1 benchmark.
3. **IP pricing / convex-hull pricing for duty-covering loads.** When the restricted-master MIP is resolved, LP duals no longer support the allocation. Import convex-hull-pricing / uplift ideas from unit commitment into the microgrid: compute minimal-uplift internal tariffs that make the fleet's chosen duties individually rational, and compare uplift magnitude to (a) fleet dominance share and (b) charger/genset lumpiness. This gives the thesis a clean, publishable OR-theory core.
4. **Duties as combinatorial bids.** Reinterpret CG columns (duties with embedded charging plans) as *package bids* in a combinatorial auction run by the microgrid operator; the LP master *is* the auction's winner-determination relaxation, and CG is iterative bid generation. Design a mechanism (e.g., pay-as-clear on duals + uplift, or VCG-on-columns) and analyze incentive properties when the fleet can misreport duty costs/energy needs. Nothing like this exists in the LEM auction literature (which assumes simple bids).
5. **Strategic withholding with a timetable alibi.** Extend the storage-withholding detection framework (arXiv:2405.01442) to a duty-constrained V2G fleet: simulate a profit-maximizing depot in a thin LEM (oligopoly setting of 10.1016/j.est.2025.119406) and test whether standard market-power monitors can distinguish strategic under-discharge from timetable-forced behavior. Policy payoff: should municipally-owned fleets be exempt from mitigation?
6. **Islanded-microgrid regime map.** In a diesel+PV+storage islanded system (Galapagos/Alaska/military data), the internal marginal price is piecewise: ~0 (solar surplus), storage opportunity cost, diesel marginal cost, and scarcity. Map how the *optimal duty structure* (number of vehicles, charging windows, V2G usage) switches across these regimes, and quantify the error of the standard exogenous-tariff assumption used by the entire depot-EMS literature (Theme 2) as fleet dominance grows from 10% to 80% of load. This is the cleanest empirical "so what" experiment for the thesis.
7. **Reverse-Stackelberg tariff design against an EVSP follower.** Adapt the EJOR 2025 reverse-Stackelberg/affine-tariff approach: the microgrid operator designs a (time-varying, possibly affine-in-power) internal tariff such that the *fleet's own* cost-minimizing EVSP reproduces the welfare-optimal schedule. Since the follower is an IP, exact steering may be impossible — characterize the achievable set and the optimal affine approximation (connects to idea 3).
8. **Two-fleet (or fleet-vs-storage) local market game.** The thin-market oligopoly result says even small players move LEM prices. Model two depots (e.g., bus depot + logistics depot, or depot + merchant storage) sharing one microgrid/feeder, each with an exact EVSP/storage oracle, competing through the internal price. Compute Nash equilibria via best-response CG iterations; study whether timetable rigidity softens or intensifies competition (duty constraints reduce strategic flexibility — a testable hypothesis).
9. **Transactive depot demonstrator with unit-commitment-aware bids.** Reproduce the Olympic Peninsula generator-bidding logic (startup cost, min-runtime folded into 5-min offers) for the *demand side*: encode duty commitments as multi-interval demand bids with "min-runtime"-like linkage, and show a receding-horizon transactive clearing that respects trip departures. This bridges the 2008 seminal demo with modern fleet ops and would be attractive to the TE community (PNNL-style venues).
10. **Seaport transfer case.** Port microgrids already couple logistics scheduling (berths, cranes, e-trucks) with energy management, including Stackelberg coordination (10.1016/j.energy.2025.135640, 10.1049/rpg2.12401). Position one thesis chapter as a domain transfer: the exact-EVSP-with-price-formation machinery applied to drayage e-truck fleets in a port microgrid — a second application domain that strengthens generality claims and taps a distinct reviewer pool.

---

## One-paragraph bottom line

Price formation *inside* microgrids is a mature literature (auctions, P2P, DLMP, Stackelberg internal pricing, transactive demonstrations since 2008), and fleet/depot energy management is an exploding literature — but the two are joined only at their edges: depots price-*take* into wholesale/ancillary markets; DLMP loops use aggregate EV envelopes; the two genuinely close prior works (Wu et al. 2019 bus-ops↔DLMP bilevel; Yao/Scaglione et al. 2025 logistics↔LMP fixed point) do not use an exact duty-based EVSP, do not operate at microgrid scale with local resources (diesel UC, PV, storage, V2G), and do not study the centralization spectrum. The defensible novelty is precisely: **an exact, timetabled, set-partitioning EVSP (CG + RCSPP pricing) as the demand-side best-response oracle inside microgrid-internal price formation, with a systematic comparison from benevolent-planner co-optimization to strategic/price-mediated operation, including the integrality-induced pricing pathologies (duality gaps, uplift, degeneracy of marginal prices) that no prior work confronts.**
