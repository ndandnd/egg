# Agent 4 — Economic theory for the dictator-to-market spectrum with one large atomic player

**Scope.** Literature audit for the EVSP-inside-price-formation thesis: welfare comparisons between price-taking, strategic (price-maker), and centrally planned operation of a single large flexible agent; potential-game/convergence theory for one big player against an endogenous price; major–minor player models; principal–agent and mechanism-design results for flexibility procurement under private (combinatorial) information; emissions-vs-cost objective divergence; and performative-prediction / forecast-feedback loops. Each theme lists key papers (DOIs only where actually observed during this search session — where a DOI was not visible I say so), then novelty threats, open gaps, and research-idea sketches.

**Notation used below** (matching the project): the fleet's value function is V(p) = min_{S∈𝒮} [c(S) + p·e(S)] over finitely many schedules S; V is concave piecewise-linear in the price vector p, the load response e(S*(p)) is a supergradient of V and jumps at kinks. Regimes: **T** = price-taker (best-responds to a fixed/forecast price), **M** = strategic price-maker (minimizes own bill Σ_t L_t·g_t(U_t+L_t)), **D** = benevolent dictator/planner (minimizes true generation-cost integral + fleet operating cost).

---

## Theme 1 — Welfare gap between price-taking, strategic, and centralized operation of a single large flexible agent

### 1a. Self-scheduling vs centralized dispatch, and three-regime comparisons for storage

1. **Anunrojwong, J., Balseiro, S. R., Besbes, O., & Xu, B. (2024/2025). "Battery Operations in Electricity Markets: Strategic Behavior and Distortions."** SSRN working paper 4877753 (no journal DOI observed; SSRN abstract id 4877753).
   - Analytically tractable two-settlement (day-ahead + real-time) market model; closed-form battery behavior and generation cost in three regimes: (i) no battery, (ii) centralized battery, (iii) decentralized profit-maximizing battery. The strategic battery distorts in three ways: quantity withholding, shifting participation from day-ahead to real-time, and reduced real-time responsiveness. Proves the Price of Anarchy (cost-reduction ratio of centralized vs profit-maximizing battery) is always in [9/8, 4/3]; shows competition mitigates distortions but several market-power-mitigation mechanisms backfire.
   - *Relevance:* This is the closest existing analogue of the project's T/M/D spectrum — but for a **convex** battery, not a combinatorial scheduling agent, and it omits the naive price-taker regime. The main quantitative benchmark to beat/extend.

2. **Jiang, Z., Nie, X., & Skoulakis, S. (2026). "The Welfare Gap of Strategic Storage: Universal Bounds and Price Non-Linearity."** arXiv:2602.19660 (no DOI observed beyond the arXiv listing).
   - Continuous-time stochastic generalization of the above: with **linear** price functions, the 4/3 PoA bound is tight and is a "structural invariant" — unaffected by arbitrary stochastic demand and general convex operational constraints. With general **convex** price functions the PoA is **unbounded** even for deterministic demand; for monomial price functions of degree d they map a "price of non-linearity" (bound 2 in specific discrete-demand cases; tight characterization for quadratic).
   - *Relevance:* Shows linearity of the inverse supply curve is the knife-edge for bounded strategic-storage inefficiency; a merit-order stack (piecewise-constant marginal cost) is exactly the non-linear case where bounds can blow up — directly relevant to the microgrid setting with a fossil-generator step stack.

3. **Sioshansi, R. (2010). "Welfare Impacts of Electricity Storage and the Implications of Ownership Structure."** The Energy Journal 31(2). DOI: 10.5547/issn0195-6574-ej-vol31-no2-7.
   - Large storage doing arbitrage smooths on/off-peak price differences, destroying its own arbitrage value but creating external welfare gains for consumers; incentives of merchant owners, consumers, and generators are misaligned; a mix of merchant and consumer ownership maximizes potential welfare gain.
   - *Relevance:* Canonical statement that the *ownership/objective* of a single large flexible asset determines how much of the social value it realizes — the "who holds the pen" question the thesis generalizes to fleets.

4. **Sioshansi, R. (2014). "When energy storage reduces social welfare."** Energy Economics 41:106–116 (DOI not observed; RePEc listing).
   - Equilibrium model with combinations of competitive/strategic generation and standalone/generator-owned storage. If generation is competitive and does not own storage, storage cannot reduce welfare; otherwise storage can be welfare-diminishing relative to no storage. Counterintuitively, welfare losses under strategic generators can be *larger* when storage itself is competitive.
   - *Relevance:* Warns that adding a "well-behaved" flexible agent to an imperfect market can lower welfare — a caution for claims that the EV fleet is automatically benign under regime T.

5. **"Merchant Storage Investment in a Restructured Electricity Industry."** The Energy Journal. DOI: 10.5547/01956574.40.4.asid (author list not captured in the search snippet).
   - Investment-stage comparison of profit-maximizing merchant vs welfare-maximizing storage sizing; with sufficiently competitive generation, the profit-maximizing merchant's behavior can be welfare-diminishing vs no storage at all, contradicting the fixed-capacity result of Sioshansi (2014).
   - *Relevance:* The welfare ranking of regimes can flip between operations and investment timescales; the thesis's fleet-sizing extension should note this.

6. **"Energy Storage Participation in Wholesale Markets: The Impact of State-of-Energy Management."** IEEE Open Access Journal of Power and Energy. DOI: 10.1109/oajpe.2022.3174523 (authors not captured in snippet).
   - Compares storage restricted to self-scheduling vs submitting price-responsive offers with the market operator managing state of energy. Self-scheduling-only is suboptimal under uncertainty (storage profit −64% in the case study); strategic storage can exploit infeasible schedules if the MO does not manage its SOE.
   - *Relevance:* Directly the "self-scheduling vs centralized dispatch" design question, with quantified welfare/profit deltas; the analogue for a fleet would compare bill-optimal duty self-scheduling vs surrendering the duty model to the operator.

7. **González Vayá, M., & Andersson, G. (2015). "Optimal Bidding Strategy of a Plug-In Electric Vehicle Aggregator in Day-Ahead Electricity Markets Under Uncertainty."** IEEE Transactions on Power Systems. DOI: 10.1109/tpwrs.2014.2363159.
   - Bilevel (MPEC/MILP) bidding of a PEV aggregator that *endogenously* moves day-ahead prices; fleet modeled as a probabilistic virtual battery. Compares against exogenous-price bidding, uncontrolled charging, and central dispatch of the fleet; strategic bidding beats exogenous-price bidding, and the aggregator has only limited market-power potential at moderate penetrations.
   - *Relevance:* The nearest EV-specific antecedent of regime M — but with a *continuous aggregate battery abstraction*, explicitly discarding duty-level combinatorics. The thesis's exact-EVSP inside the bilevel is the step it does not take.

### 1b. Monopsony: a large BUYER withholding consumption to depress price

8. **Kazempour, S. J., Conejo, A. J., & Ruiz, C. (2015). "Strategic Bidding for a Large Consumer."** IEEE Transactions on Power Systems 30(2):848–856. DOI: 10.1109/tpwrs.2014.2332540.
   - Stochastic MPEC where a large consumer submits bid curves to alter pool prices to its own benefit; demonstrates cost advantages of strategic (price-maker) bidding relative to non-strategic bidding.
   - *Relevance:* The canonical monopsony-load MPEC. Decision variables are continuous demand bids — no integer duty structure; welfare accounting is secondary.

9. **"Strategic Biddings of a Consumer demand in both DA and Balancing Markets in Response to Renewable Energy Integration."** Electric Power Systems Research (2022). DOI: 10.1016/j.epsr.2022.108132 (authors not captured in snippet).
   - Bilevel/MPEC-MILP of a strategic consumer co-participating in day-ahead and balancing/reserve markets; documents a reduction in the consumer's payment *and a decline in social welfare* from strategic demand-side behavior.
   - *Relevance:* Explicit demand-side welfare-loss quantification (monopsony distortion) in a modern co-optimized market — but again convex/continuous demand.

10. **Baldick, R. Course notes, "Restructured Electricity Markets: Market Power" (UT Austin EE394V; grey literature, no DOI).**
    - Textbook-level treatment: a flexible buyer purchasing less than willingness-to-pay depresses price for all inframarginal purchases ("monopsony power"); the ISO exercising interruptible demand can be a monopsonist on behalf of load; this saves consumers money but reduces short-run welfare and deters investment (long-run welfare loss).
    - *Relevance:* Clean articulation of exactly the L_t·g_t(U_t+L_t) bill-minimization distortion the thesis's regime M formalizes; also flags the long-run investment channel.

11. **OECD (2009). "Monopsony and Buyer Power"** (Policy Roundtable report; no DOI).
    - Distinguishes monopsony (withholding purchases to depress price below competitive level — welfare-reducing) from countervailing bargaining power (may push prices toward competitive levels). All-units price effects are the mechanism.
    - *Relevance:* Supplies the IO vocabulary for the thesis: the fleet's bill-minimization is textbook monopsony; the deadweight-loss geometry transfers directly.

12. **"Measuring Oligopsony Market Power in the Italian Electricity Market: Preliminary Results."** International Advances in Economic Research (2014). DOI: 10.1007/s11294-014-9478-8 (authors not captured in snippet).
    - Empirically measures demand-side markdowns of 3.8–5.3% on average (7.5–10% in peak hours, 2011) using individual consumer bid data; oligopsony power rises with abundant renewable supply.
    - *Relevance:* Rare empirical magnitude for demand-side market power — a calibration anchor for how large the M-vs-T price gap plausibly is at national scale.

13. **Hogan, W. (2010). "Demand Response Pricing in Organized Wholesale Markets"** (IRC comments, grey literature) and **CAISO Market Surveillance Committee (2011), Opinion on FERC Order 745** (grey literature); **FERC Order 745** itself (2011).
    - The Order-745 debate: paying load full LMP for consumption reductions over-rewards curtailment (double payment), inducing curtailment whose value exceeds cost; FERC's "net benefits test" and "billing unit effect" institutionalize a *pecuniary* (transfer) test rather than an efficiency test — effectively sanctioned monopsony on behalf of load.
    - *Relevance:* A regulatory-economics precedent that "consumer-side price suppression" is deliberately distinguished from efficiency; useful when arguing regime M's bill savings are largely transfers, not welfare.

### 1c. Self-defeating price-taking: herding/avalanche/rebound peaks

14. **Bailey, M. R., Brown, D. P., Myers, E., Shaffer, B., & Wolak, F. A. (2025). "Electric Vehicles and the Energy Transition: Unintended Consequences of Time-of-Use Pricing."** American Economic Review: Insights 7(4):550–566. DOI: 10.1257/aeri.20240476.
    - Field experiment: TOU pricing successfully shifts EV charging off-peak but induces larger synchronized "shadow peaks" at the price boundary, increasing exceedance of local capacity constraints and advancing network upgrades; centrally managed charging solves the coordination problem and is well tolerated.
    - *Relevance:* Flagship empirical evidence that naive price-following by many EVs is self-defeating and that the D regime (central management) dominates — the thesis provides the missing theory for one *atomic* fleet.

15. **Kühnbach, M., Stute, J., & Klingler, A.-L. (2021). "Impacts of avalanche effects of price-optimized electric vehicle charging — Does demand response make it worse?"** Energy Strategy Reviews. DOI: 10.1016/j.esr.2020.100608.
    - Simulation of German system to 2050: when EV demand is large enough to have leverage on residual load, one-shot price-based DR creates new peaks in formerly cheap hours ("avalanche effect", framed via Gottwalt et al. as a sequential game between price setter and price takers); dynamically updated DR signals or splitting the fleet into groups avoids it.
    - *Relevance:* Names and quantifies the self-defeating price-taker loop for EV fleets; the thesis's V(p) supergradient jumping at kinks is the exact mathematical mechanism (the entire fleet load jumps to the cheap hour).

16. **"Herding from Uncoordinated Smart Charging of EVs: A Real-Life Demonstration."** IEEE ISGT Europe 2025. DOI: 10.1109/isgteurope64741.2025.11305626 (authors not captured in snippet).
    - Real-network demonstration: beyond ~20–30% EV penetration, the tariff-induced synchronized charging peak equals then exceeds the traditional evening peak, nonlinearly in penetration.
    - *Relevance:* Empirical threshold behavior for when "small" price-taking flips to system-shaping — useful for the thesis's national-market-vs-microgrid dial.

17. **Karaduman, Ö. (2021). "Economics of Grid-Scale Energy Storage in Wholesale Electricity Markets."** MIT CEEPR Working Paper 2021-005 (grey literature; no DOI; author name from CEEPR series listing, not visible in the retrieved text itself).
    - Structural empirical model: large storage buying raises prices and selling lowers them; price-taker models overestimate profitability and bias estimated social returns; storage's private and social incentives diverge exactly as its price effect grows ("the operator has incentives to under-produce").
    - *Relevance:* Empirical confirmation that the T-regime valuation error and the M-regime withholding distortion grow together with size — the thesis's "fleet large enough to move prices" premise.

18. **"Investigating the impacts of price-taking and price-making energy storage in electricity markets through an equilibrium programming model."** IET Generation, Transmission & Distribution (2019). DOI: 10.1049/iet-gtd.2018.6223 (authors not captured in snippet).
    - EPEC comparing price-taking vs strategic storage against strategic generators: price-taking storage mitigates generator market power at peak and slightly enhances it off-peak (net positive); strategic storage withholds capacity to preserve peak/off-peak spreads, limiting its demand-flattening effect — still better than no storage.
    - *Relevance:* A full ordering (no storage ≺ strategic ≺ price-taking storage in welfare) for the convex case; the thesis should test whether the ordering survives combinatorial flexibility.

19. **Electrolyzer analogues:** "How flexible electricity demand stabilizes wind and solar market values: The case of hydrogen electrolyzers," Applied Energy 307 (2022) (DOI not observed; RePEc listing) — flexible hydrogen demand endogenously sets a floor under renewable market values (a *large buyer raising* prices in cheap hours); and "Effect of large-scale variable electric loads and operation strategy in decentralized electricity markets: Case of large electrolyzers" (Chalmers, using Nord Pool bid curves; no DOI observed) — a 400 MW electrolyzer can raise day-ahead price by ~35 €/MWh (+52% over 2023 median) depending on its price-limit operating strategy.
    - *Relevance:* The green-hydrogen literature is the most active current site of "single large flexible buyer moves prices" analysis; none of it has combinatorial duty structure, but it supplies price-impact magnitudes and the "operating strategy = price-limit policy" framing.

---

## Theme 2 — Potential games, best-response convergence, and cycling against an increasing price curve

### Core theory

1. **Monderer, D., & Shapley, L. S. (1996). "Potential Games."** Games and Economic Behavior 14(1):124–143. DOI: 10.1006/game.1996.0044.
   - Defines exact/weighted/ordinal potentials; finite games with a (generalized) ordinal potential have the Finite Improvement Property (FIP): every improvement path terminates at a pure Nash equilibrium; congestion games admit exact potentials.
   - *Relevance:* The baseline machinery. Key observation for the thesis: **one large player best-responding to a price curve that depends on its own aggregate load is formally a 1-player "game" whose iterated best response is a fixed-point iteration, not a potential-game dynamic** — its natural potential is the *social* cost only in regime D; in regime M the player optimizes L·g(U+L), which is *not* the integral of g, so "best response to last round's prices" (the T-iteration) need not descend anything.

2. **"Coordination Games on Weighted Directed Graphs."** Mathematics of Operations Research (2022). DOI: 10.1287/moor.2021.1159 (authors not captured in snippet).
   - Surveys and extends FIP theory; recalls that computing a pure NE of congestion games is PLS-complete (Fabrikant et al.) and that even symmetric network congestion games have exponentially long best-response paths (Ackermann et al.).
   - *Relevance:* Even where an improvement potential exists, convergence can be exponentially slow — a warning for iterative fleet-vs-price-clearing loops with 2^(schedules) strategy sets.

3. **"On the Convergence Time of the Best Response Dynamics in Player-specific Congestion Games."** arXiv:0805.1130. DOI: 10.48550/arxiv.0805.1130 (authors not captured in snippet).
   - Player-specific singleton congestion games: best-response dynamics **can cycle**, though from every state a short best-response path to equilibrium exists; random best response terminates with probability one; expected time can be super-polynomial (conjectured, with supporting simulations).
   - *Relevance:* Prototype of the cycling phenomenon the thesis should expect when the fleet's discrete schedule choice and a price recomputation alternate: player-specific (schedule-specific) costs break the exact potential.

4. **Mavronicolas, M., et al. (2007). "Congestion Games with Player-Specific Constants."** MFCS 2007 (no DOI observed; conference PDF).
   - A weighted congestion game with 3 players on 3 parallel links lacking even the Finite Best-Reply Property; but weighted congestion games with linear delays plus player-specific *additive constants* admit an ordinal potential (FIP, pure NE exist).
   - *Relevance:* Delineates precisely how little heterogeneity destroys FIP — mapping to the fleet: schedule-specific operating-cost offsets (the c(S) term) play the role of player-specific constants; affine g_t keeps an ordinal potential, general g_t does not.

### Energy-specific convergence results

5. **Ma, Z., Callaway, D. S., & Hiskens, I. A. (2013). "Decentralized Charging Control of Large Populations of Plug-in Electric Vehicles."** IEEE Transactions on Control Systems Technology 21(1):67–78. DOI: 10.1109/tcst.2011.2174059 (conference version: CDC 2010, DOI: 10.1109/cdc.2010.5717547).
   - Infinite-population charging game weakly coupled through a common price; a quadratic "tracking penalty" against the population-average trajectory makes the best-response map a contraction; unique Nash equilibrium ≈ valley-filling; iterated best response converges *in the infinite-population limit*.
   - *Relevance:* The classic fix for oscillation: **add a proximal/tracking term to damp the fixed-point iteration.** The thesis's atomic fleet is the opposite limit (one player = the whole mean field), where the contraction argument fails without modification; also the strategy set here is a convex set of charging rates, not discrete duties.

6. **Gan, L., Topcu, U., & Low, S. H. (2013). "Optimal Decentralized Protocol for Electric Vehicle Charging."** IEEE Transactions on Power Systems 28(2). DOI: 10.1109/TPWRS.2012.2210288.
   - Iterative price-signal protocol converging to the exact convex optimum (flattest feasible aggregate profile) for arbitrary heterogeneous EV constraints, including asynchronous updates with outdated prices; each EV solves only a local convex problem with an added quadratic damping term.
   - *Relevance:* Shows convergence of price-iteration is achievable *with convex individual feasible sets plus damping*. Both ingredients break for a set-partitioning EVSP: the fleet's feasible set is a non-convex lattice of schedules, and V(p)'s supergradient is discontinuous.

7. **Roozbehani, M., Dahleh, M. A., & Mitter, S. K. (2012). "Volatility of Power Grids Under Real-Time Pricing."** IEEE Transactions on Power Systems 27(4):1926–1940. DOI: 10.1109/tpwrs.2012.2195037 (also CDC 2010, DOI: 10.1109/cdc.2010.5718173; IEEE SmartGridComm 2010, DOI: 10.1109/smartgrid.2010.5621994).
   - Passing wholesale prices directly to price-responsive consumers creates a closed-loop feedback system; instability/volatility characterized by the maximal ratio of consumer to producer generalized price-elasticity; stabilization requires deliberately *biased/static* pricing functions, with a characterized efficiency loss from stabilization.
   - *Relevance:* The control-theoretic twin of the avalanche effect and the closest existing "cycling theorem": when the flexible load's elasticity (for an atomic fleet with piecewise-linear V, locally *infinite* elasticity at kinks) exceeds the supply side's, price-feedback iterations oscillate. The thesis can sharpen this: an atomic combinatorial fleet is *always* in the unstable regime at kinks of V.

8. **Cycling in agent-based practice:** Nitsch, F. (2025). *Flexibility options in electricity markets with high shares of renewable energies* (DLR dissertation, grey literature) documents that in the AMIRIS agent-based model, naive price forecasts fed to multiple flexibility options produce avalanche/cannibalization effects — revenue expectations self-invalidate.
   - *Relevance:* Practitioner-level confirmation that the T-iteration does not converge without coordination; motivates the thesis's fixed-point/potential analysis.

**Synthesis for the thesis (theme 2).** For a *single* atomic player against an increasing inverse-supply curve g_t: (i) regime D is a pure optimization — "convergence" is trivial; (ii) regime M is a pure optimization of a different objective — also no game dynamics; (iii) the interesting dynamic is **regime T iterated with price recomputation**: L^{k+1} ∈ argmin_S c(S) + p(L^k)·e(S), p = g(U + L). This is a fixed-point iteration of a *monotone-decreasing* set-valued map (higher prices ⇒ ≤ load in each hour under substitutability). Monotone-decreasing maps generically produce 2-cycles (the classic cobweb), and with a finite schedule set, exact 2-cycles between two schedules straddling a kink of V are easy to construct; Tarski-type convergence would instead require an order-*preserving* map (strategic complements), which price adjustment is not. Known repairs: damping/proximal terms (Ma et al., Gan et al.), agent grouping (Kühnbach et al.), price-function flattening (Roozbehani et al.), or randomized/asynchronous updates (player-specific congestion literature). No paper was found that states the cobweb/2-cycle result specifically for a combinatorial scheduling agent — see Open Gaps.

---

## Theme 3 — Major–minor / large-player models: one big fleet plus a fringe

1. **Huang, M. (2010). "Large-Population LQG Games Involving a Major Player: The Nash Certainty Equivalence Principle."** SIAM J. Control and Optimization 48(5):3318–3353. DOI: 10.1137/080735370.
   - Founding major–minor mean-field paper: one non-vanishing major player plus a continuum of minor players; state augmentation with aggregate quantities; consistency conditions yield decentralized ε-Nash strategies.
   - *Relevance:* The canonical mathematical home for "one atomic fleet + fringe of small flexible loads"; the fleet is the major player whose randomness makes the mean field stochastic.

2. **Nourian, M., & Caines, P. E. (2013). "ε-Nash Mean Field Game Theory for Nonlinear Stochastic Dynamical Systems with Major and Minor Agents."** SIAM J. Control and Optimization 51(4):3302–3331. DOI: 10.1137/120889496.
   - Nonlinear extension: the major agent's noise makes the minors' mean field a stochastic process; solution via stochastic HJB + McKean–Vlasov consistency, ε_N = O(1/√N). (Partially observed variants: Caines & Kizilkale, IEEE TAC 2017, DOI: 10.1109/tac.2016.2637347; Şen & Caines, SIAM J. Control Optim. 2016, DOI: 10.1137/16m1063010.)
   - *Relevance:* Machinery for the fleet-with-fringe game when the fleet has private stochastic duty demand.

3. **"Price formation and optimal trading in intraday electricity markets with a major player."** arXiv:2011.07655 (authors not captured in snippet; companion to an intraday-market MFG paper).
   - Linear-quadratic MFG where a big producer trades against a continuum of small renewable producers, all interacting through the endogenous intraday price; closed-form Nash equilibrium; leader has first-mover advantage but an information disadvantage; ε-Nash construction for finite N.
   - *Relevance:* Existing template for *price formation with one major player* in electricity — continuous LQ trading rates; no scheduling combinatorics.

4. **"Master equation of discrete-time Stackelberg mean field games with multiple leaders."** arXiv:2209.03186 (authors not captured in snippet).
   - Discrete-time Stackelberg MFG with leaders committing to dynamic policies, major and minor followers with private Markovian types; master-equation computation of all equilibria; leaders may be welfare-maximizing.
   - *Relevance:* Formalism covering "system operator (leader) vs fleet (major follower) vs small loads (minor followers)" — including a *benevolent* leader — in one nested structure; types are continuous, not feasibility sets.

5. **Tajeddini, M. A., Kebriaei, H., & Glielmo, L. (2020). "Decentralized Hierarchical Planning of PEVs Based on Mean-Field Reverse Stackelberg Game."** IEEE Trans. Automation Science and Engineering 17(4):2014–2024. DOI: 10.1109/tase.2020.2986374. (Related: Tajeddini & Kebriaei, IEEE Systems Journal 2019, DOI: 10.1109/jsyst.2018.2855971.)
   - Aggregator announces a price *function* (reverse Stackelberg) to a cooperative mean-field population of PEVs; convergence to leader–follower MF ε-Nash; leader can achieve its global optimum by shaping the followers' reaction function.
   - *Relevance:* Reverse Stackelberg = "menu/tariff design as leadership" — a bridge between theme 3 and theme 4's mechanism design; again convex charging strategies only.

6. **"A tri-level cooperative optimization framework for electric vehicle charging via a mean-field reverse Stackelberg game."** Int. J. Electrical Power & Energy Systems (2026). DOI: 10.1016/j.ijepes.2026.111855; and **"Optimal Charging Control for Electric Vehicle Fleet Incorporating Energy Storage System Using Major-Minor Mean Field Game Theory."** IEEE ETFG 2025. DOI: 10.1109/etfg61999.2025.11401252 (author lists not captured).
   - Recent stacked architectures: DSO dispatch / RSG pricing / MFG charging population; and major–minor MFG where storage units are majors and EVs are minors, solved with actor–critic RL.
   - *Relevance:* Confirms the "aggregator-of-aggregators" architecture is being modeled with MFG+Stackelberg stacks; none makes the major player's strategy space a discrete schedule set.

7. **"Aggregator of aggregators" (regulatory grey literature):** Silicon Valley Clean Energy ResponDER market design (2022); Uplight response to NJ BPU Order 2222 RFI (2024) — defines the AoA role explicitly; IESO Transmission–Distribution Coordination WG materials (2022); US DOE "Sourcing Distributed Energy Resources for Distribution Grid Services."
   - *Relevance:* The institutional form exists in market-design practice (a platform coordinating competing aggregators under one interface) but has essentially no formal economic theory attached — an opening for the thesis's hierarchy analysis.

---

## Theme 4 — Information asymmetry inside a benevolent organization; mechanism design for flexibility with private combinatorial costs

### Screening / menus for flexible demand (classic)

1. **Chao, H.-p., & Wilson, R. (1987). "Priority Service: Pricing, Investment, and Market Organization."** American Economic Review 77(5):899–916 (no DOI observed; cited in later works). Related: **Chao, Oren, Smith & Wilson (1986), "Multilevel demand subscription pricing for electric power,"** Energy Economics 8(4):199–217, DOI: 10.1016/0140-9883(86)90001-0; **Oren, Smith & Wilson (1985), "Capacity Pricing,"** Econometrica 53(3), DOI: 10.2307/1911654.
   - The founding menu-of-contracts literature for electricity: a menu of (price, reliability) options induces self-selection by customers ordered by outage cost, implementing the efficient rationing plan without knowing individual types; supports investment via revenue adequacy.
   - *Relevance:* The natural template for "SO offers the fleet a menu of curtailment/flexibility contracts"; but types are scalar outage costs — not feasibility sets of a scheduling polytope.

2. **"A Bi-Level Optimization Formulation of Priority Service Pricing."** IEEE Transactions on Power Systems (2020). DOI: 10.1109/tpwrs.2019.2961173 (authors not captured; Papavasiliou group per references).
   - Re-derives priority-service menus as a Stackelberg equilibrium via bi-level MIP, explicitly *because* the classical theory's convexity assumptions fail with unit commitment; integrates menu design with day-ahead UC on the Belgian system.
   - *Relevance:* Precedent for menu design *with nonconvex generation*, i.e., screening layered on integer programming — the mirror image of the thesis's problem (their nonconvexity is on the supply side, the fleet's is on the demand side).

### Modern mechanism design for DR/EVs with private information

3. **"The aggregator's contract design problem in the electricity demand response market."** Operational Research 23 (2023). DOI: 10.1007/s12351-023-00753-1 (authors not captured).
   - Principal–agent model where customers privately know DR potential and disutility; a menu of contracts (separating contracts) lets the aggregator elicit types with minimal informational rent.
   - *Relevance:* Standard adverse-selection template for flexibility procurement; two-dimensional scalar types.

4. **"Contract Design for Energy Demand Response" (DR-VCG).** IJCAI 2017. DOI: 10.24963/ijcai.2017/167 (arXiv:1705.07300; authors not captured in snippet).
   - Mechanism offering a set of contracts (reduction target + penalty scheme) with VCG pricing over the *combinatorial selection of contract bundles*; truthful bidding and honest preparation effort are dominant strategies; outperforms the deployed SCE mechanism.
   - *Relevance:* Shows VCG over a combinatorial allocation works for DR procurement — but the agents' private information is cost per contract, not a hidden feasibility structure.

5. **Gerding, E. H., Robu, V., Stein, S., Parkes, D. C., Rogers, A., & Jennings, N. R. (2011). "Online mechanism design for electric vehicle charging."** AAMAS 2011 (ACM DL identifier DOI: 10.5555/2031678.2031733). Journal version: **Robu et al., "An Online Mechanism for Multi-Unit Demand and its Application to Plug-in Hybrid Electric Vehicle Charging,"** JAIR (2013). DOI: 10.1613/jair.4064.
   - Online DSIC mechanisms where each EV's private type includes *arrival time, departure deadline, and marginal-value vector* — i.e., elements of its scheduling feasibility; truthfulness requires occasionally "burning" electricity (leaving units unallocated); limited-misreport assumption (can't claim earlier arrival/later departure).
   - *Relevance:* **Closest existing work to "private type = scheduling feasibility":** temporal availability windows are private. But it is many small agents each with an interval type, not one agent with a private set-partitioning feasible region; and efficiency is sacrificed (burning) rather than characterized as an information rent on combinatorial structure.

### Markets vs hierarchies, indivisibilities, and transfer prices

6. **Scarf, H. E. (1994). "The Allocation of Resources in the Presence of Indivisibilities."** Journal of Economic Perspectives 8(4):111–128. DOI: 10.1257/jep.8.4.111. (Foundations: Scarf, Econometrica 1981, "Production Sets with Indivisibilities" Parts I & II, DOIs: 10.2307/1911124, 10.2307/1913318.)
   - With indivisibilities, profitability at competitive linear prices can neither detect nor support optimal allocations; proposes a *quantity test* instead; suggests viewing the large firm as "an algorithm for solving integer programming problems."
   - *Relevance:* The deep classical reason the thesis's D regime cannot be decentralized to the fleet via linear transfer prices: V(p)'s kinks are exactly Scarf's failure of the pricing test. The "firm as an IP-solving algorithm" line is nearly a mission statement for the benevolent-dictator microgrid.

7. **O'Neill, R. P., Sotkiewicz, P., Hobbs, B. F., Rothkopf, M. H., & Stewart, W. R. (2005). "Efficient market-clearing prices in markets with nonconvexities."** European Journal of Operational Research 164(1):269–285. DOI: 10.1016/j.ejor.2003.12.011.
   - Restores clearing via commodity prices *plus* discriminatory contracts/uplift payments for integer activities (IP pricing); answers Scarf's search for prices yielding zero profits at the optimum.
   - *Relevance:* The internal-transfer-pricing fix: the SO can support the dictator solution with a linear price + schedule-specific side payment — i.e., a *two-part transfer price*. Whether this remains incentive-compatible when the fleet privately knows 𝒮 is exactly the thesis's theme-4 question.
   - Note: nonconvex-pricing follow-ons (convex hull/extended LMP pricing — Gribik–Hogan–Pope tradition) were repeatedly referenced in retrieved texts but not directly retrieved; treat as known adjacent literature.

8. **Williamson, O. (1975). *Markets and Hierarchies*; Coase (1937), "The Nature of the Firm"** (books/classics, no DOIs; background).
   - Transaction-cost economics: hierarchies replace markets when contracting is costly — e.g., under specificity, complexity, and information asymmetry.
   - *Relevance:* Provides the framing question the thesis can answer *quantitatively* in one setting: when the interface between SO and fleet is a set of hourly prices, indivisibilities create a market failure of size = duality gap; the hierarchy (dictator) closes it at the cost of information centralization. No retrieved work formalizes "markets vs hierarchies under indivisibilities" for energy — see Open Gaps.

9. **Strategic behavior over nonconvex private information:** "Incorporating Non-Convex Operating Characteristics into Bi-Level Optimization Electricity Market Models," IEEE TPWRS (2019/2020) (DTU PDF; authors not captured) — strategic producers can profitably *misreport their nonconvex operating characteristics* (start-up costs, minimum output) to a UC-clearing market; and "Mixed integer parametric bilevel programming for optimal strategic bidding ... with indivisibilities," Optimization (2013), DOI: 10.1080/02331934.2013.801473 — exact algorithms for bilevel problems with integer lower levels.
   - *Relevance:* Establishes both (a) that misreporting *combinatorial structure* is a real strategic lever, and (b) the computational toolkit (parametric integer programming, duality-gap penalization) for the thesis's M regime with integer market clearing.

---

## Theme 5 — Emissions vs cost objectives for the dictator

1. **Holland, S. P., & Mansur, E. T. (2008). "Is Real-Time Pricing Green? The Environmental Impacts of Electricity Demand Variance."** Review of Economics and Statistics 90(3):550–561 (no DOI observed; NBER WP 13508).
   - RTP reduces within/across-day demand variance; the emissions effect of variance reduction is *region-dependent in sign* — decreases emissions where oil-fired peakers are marginal, increases them where hydro is marginal; effects small.
   - *Relevance:* First rigorous demonstration that the cost-optimal flexible-load schedule is not emissions-optimal — sign can flip by region; foundational for the thesis's dictator-objective variants.

2. **"Cascading marginal emissions signals for green charging with growing electric vehicle adoption."** Nature Communications (2025), article s41467-025-64979-7 (DOI string not directly displayed in retrieved text; URL observed).
   - Neither average (AEF) nor short-run marginal (MEF) emission factors correctly measure managed charging's impact once the EV load is large enough that *multiple* generators respond; proposes cascading marginal signals that stay valid as adoption scales.
   - *Relevance:* The emissions-side twin of the price-maker problem: a large fleet invalidates the marginal *emissions* signal exactly as it invalidates the marginal *price* signal — the thesis's performativity story applies to both signals.

3. **Xu, Q., Ricks, W., Manocha, A., Patankar, N., & Jenkins, J. D. (2024). "System-level impacts of voluntary carbon-free electricity procurement strategies."** Joule 8(2):374–400. DOI: 10.1016/j.joule.2023.12.007. (Working papers: SSRN, DOI: 10.2139/ssrn.4248431; Zenodo, DOIs: 10.5281/zenodo.6229426, 10.5281/zenodo.8325964.)
   - Capacity-expansion analysis of voluntary procurement: annual volumetric matching and short-run-MEF "emissions matching" have ≈zero long-run system CO₂ impact; hourly (24/7) matching drives real reductions and pulls clean-firm/LDES technologies into the market, at a cost premium (order $13–30/MWh in the companion analysis).
   - *Relevance:* Defines the emissions-objective menu for the dictator (volumetric, MEF-offset, hourly-CFE) and shows they induce sharply different schedules and costs; contested by WattTime analyses arguing hourly matching without additionality has little benefit (grey literature) — a live controversy the thesis can formalize for a scheduling fleet.

4. **"Reducing Marginal Emissions of an Electric Vehicle Fleet through Smart Charging and Vehicle-to-grid."** IEEE ISGT Europe 2023. DOI: 10.1109/isgteurope56780.2023.10407696 (authors not captured).
   - MEF-based optimization of a real fleet: V1G cuts marginal emissions ~15–40%, V2G 20–60%+ by discharging stored low-carbon energy against high-MEF hours.
   - *Relevance:* Quantifies the emissions-dictator's lever for a fleet including V2G — direct comparator for the team's microgrid manuscript.

5. **"Should we reinforce the grid? Cost and emission optimization of electric vehicle charging under different transformer limits."** (Wageningen repository PDF; venue/DOI not observed.)
   - Pareto frontiers between cost-optimal and emissions-optimal EV charging: CO₂-abatement cost of moving from cost- to emissions-optimal charging ranges ~2.8–22.6 €/t (marginal profiles, V1G) up to hundreds of €/t (average profiles, V2G); emissions-optimal V2G *raises* charging cost because high-emission hours are low-price hours.
   - *Relevance:* Concrete divergence measurements (schedule overlap and abatement cost) between the two dictator objectives — the quantity the thesis can characterize theoretically via the two supergradient maps of V under p = price vs p = MEF.

6. **Electricity Maps (grey literature). "Optimizing electricity consumption with a marginal signal may not reduce its carbon footprint."**
   - Across 65 regions, average and marginal signals are nearly uncorrelated (55% of regions negatively correlated); optimizing on one signal can increase emissions measured by the other.
   - *Relevance:* Practical warning that the dictator's objective choice (MEF vs AEF vs cost) is not a detail; scheduling against the wrong signal can be counterproductive.

---

## Theme 6 — Performative prediction and forecast feedback in electricity markets

1. **Perdomo, J., Zrnic, T., Mendler-Dünner, C., & Hardt, M. (2020). "Performative Prediction."** ICML 2020, PMLR 119:7599–7609 (no DOI; PMLR).
   - Founds the field: predictions that influence their own targets; equilibrium notion of *performative stability* (predictions calibrated against the outcomes they induce); necessary and sufficient conditions for repeated retraining to converge to a stable point near minimal performative risk.
   - *Relevance:* "Retraining" = the fleet re-optimizing against last round's realized prices; performative stability = a self-confirming price forecast. The thesis's T-iteration is literally repeated risk minimization in a performative environment; known convergence conditions (strong convexity + small sensitivity) fail at kinks of V — predicting exactly where cycling appears.

2. **Hardt, M., Jagadeesan, M., & Mendler-Dünner, C. (2022). "Performative Power."** NeurIPS 2022 (no DOI observed; proceedings PDF).
   - Defines performative power = a firm's causal ability to shift the population's data distribution; low power ⇒ the firm can do no better than static optimization ("price-taker"); high power ⇒ profitable steering; monopoly maximizes performative power.
   - *Relevance:* Gives the thesis a *measurement-theoretic* definition of "large enough to move prices": the fleet's performative power = sup over schedule changes of induced price movement — computable from g_t and e(S); connects the T/M distinction to an identifiable causal quantity.

3. **Hardt, M., & Mendler-Dünner, C. (2023). "Performative Prediction: Past and Future."** arXiv:2310.16608 (survey; no DOI observed).
   - Historical arc from Morgenstern's impossibility worry through Grunberg–Modigliani (1954) and Simon (1954) — existence of self-confirming predictions by continuity/fixed point — to the modern optimization treatment.
   - *Relevance:* Grunberg–Modigliani's continuity condition **fails** for an atomic combinatorial fleet (the load response is discontinuous at kinks), so a self-confirming point forecast may not exist — a crisp, citable historical hook for a thesis theorem on nonexistence of consistent price forecasts.

4. **"Decision-focused learning under decision dependent uncertainty for power systems with price-responsive demand."** Electric Power Systems Research (2024; ScienceDirect id S0378779624005510; DTU Orbit PDF; authors/DOI not captured in retrieved text).
   - Names the loop exactly: a day-ahead demand forecast sets prices, price-responsive demand shifts against those prices, counteracting the forecast in both directions; proposes prescribing a *biased* forecast (decision-focused, Bayesian-optimization-tuned) so ex-post dispatch is efficient — "bypassing market integration of flexible demand."
   - *Relevance:* State of the art on operator-side forecast-feedback correction; the thesis's fleet-side analogue (fleet anticipates its own price impact = regime M; SO anticipates fleet = biased forecast) is a two-sided version nobody has posed with combinatorial load.

5. **"Predicting and Publishing Accurate Imbalance Prices Using Monte Carlo Tree Search."** arXiv:2411.04011.
   - Belgian imbalance-price publication: published price predictions trigger battery responses that change the price; MCTS over a learned system model + RL battery cluster improves published-price accuracy 12.8–20.4%; self-described as pioneering "price publishing under response."
   - *Relevance:* Concrete TSO-side instance of performative price forecasting with strategic storage in the loop.

6. **"Performative Time-Series Forecasting."** arXiv:2310.06077. DOI: 10.48550/arxiv.2310.06077.
   - Formalizes performativity for time-series ML (self-negating/self-fulfilling forecasts), proposes anticipating the induced distribution shift via delayed-response features.
   - *Relevance:* ML-methods anchor if the thesis includes a forecasting chapter.

7. **Cross-references:** Roozbehani–Dahleh–Mitter (theme 2) is the control-theoretic formulation of the same loop; Kühnbach et al. and Nitsch (theme 1c/2) are the energy-domain empirical naming ("avalanche effect", forecast cannibalization); the stochastic feedback-pricing DR paper arXiv:2603.15983 explicitly imports performative-optimization tools into real-time DR pricing.

---

## Novelty threats

Ranked by severity for the thesis's theory front:

1. **Anunrojwong–Balseiro–Besbes–Xu (SSRN 4877753) + Jiang–Nie–Skoulakis (arXiv:2602.19660).** The three-regime welfare comparison (none/centralized/strategic) with tight PoA bounds [9/8, 4/3] for linear prices and unboundedness for convex prices **already exists for a convex battery**, including stochastic demand and two-settlement structure. Any thesis claim must be explicitly positioned as: (a) adding the *naive price-taker* regime as a fourth point (their comparison omits T — they compare only planner vs profit-maximizer); (b) replacing the convex battery with a **finite schedule set / set-partitioning feasible region**, where V is piecewise-linear and the PoA analysis machinery (first-order conditions, closed forms) breaks; (c) studying the microgrid case where the fleet is *the* load, outside their marginal-perturbation regime.
2. **González Vayá & Andersson (10.1109/tpwrs.2014.2363159).** Already compares uncontrolled / exogenous-price (T) / price-maker bidding (M) / central fleet dispatch (D) *for an EV aggregator* with endogenous day-ahead prices. Defense: their fleet is a continuous virtual battery (they deliberately aggregate away duty combinatorics), their D is fleet-cost-minimal dispatch rather than a true system planner with generation control, and no welfare theory (bounds, orderings, structure) is derived — it is a numerical bidding paper.
3. **Kazempour–Conejo–Ruiz (10.1109/tpwrs.2014.2332540) and successors.** Monopsony load MPECs are mature; "strategic large consumer lowers its payment and lowers social welfare" is published. Defense: no integer/combinatorial demand-side structure, no analytic welfare-gap characterization, no comparison to a benevolent planner.
4. **Bailey et al. (10.1257/aeri.20240476) + avalanche literature (10.1016/j.esr.2020.100608).** "Naive price-following EVs are self-defeating; central management fixes it" is empirically established. Defense: the phenomenon is documented for *populations* of small takers; the atomic-fleet version (one optimizer whose supergradient jumps) and its fixed-point/cycling theory are not.
5. **Priority service + DR contract design (Chao–Wilson; 10.1109/tpwrs.2019.2961173; 10.1007/s12351-023-00753-1; DR-VCG 10.24963/ijcai.2017/167; Gerding/Robu et al. 10.1613/jair.4064).** Screening flexible demand with private types is a large literature, and the online-EV-mechanism strand even makes *availability windows* private. Defense: no work found where the agent's private type is a **combinatorial feasibility set (duty network / set-partitioning structure)** and the principal designs transfers over V(p)-type value functions; the "burning" inefficiency results suggest interesting analogues.
6. **Performative prediction (ICML 2020) and the DTU decision-focused forecasting paper.** The feedback loop is named, both in ML generally and for price-responsive demand in power systems. Defense: no work applies performative stability/power to a *combinatorial* responder, where the decision-dependent distribution map is discontinuous — existence of performatively stable forecasts genuinely fails there, which is new territory.
7. **Storage MPEC/EPEC and integer-bilevel algorithmics (10.1080/02331934.2013.801473, 10.1007/s10957-023-02166-8).** The computational tools for M-with-integers exist; a thesis contribution must be structural/economic, not merely "we solved a bilevel MILP."

---

## Open gaps

1. **No four-point welfare ordering (uncontrolled / naive-taker / strategic / planner) for an agent with combinatorial flexibility.** All published orderings and PoA bounds assume convex action sets. With a finite schedule set, the taker's response is a supergradient selection that can *overshoot* (herd into the cheap hour), so — unlike the convex case, where T sits between M and D — **naive T can plausibly be strictly worse than M** (strategic anticipation self-damps). No theorem or counterexample of this "non-monotone regime ordering" was found anywhere.
2. **No monopsony theory for integer/indivisible demand.** Classical monopsony markdown formulas (and the Order-745 debate) assume smooth demand reduction. Withholding by an EVSP fleet means *dropping/reshaping whole duties* — a discrete withholding lattice. Nothing found characterizes optimal discrete withholding, its deadweight loss, or how the markdown formula generalizes when the buyer's marginal value correspondence is a step function.
3. **No convergence/cycling theory for one atomic combinatorial player against an increasing price curve.** The pieces exist (cobweb intuition, Roozbehani elasticity-ratio instability, player-specific congestion cycling, Ma/Gan damped convergence for convex populations), but no paper states: conditions on g_t and the schedule set under which the T-iteration converges vs 2-cycles; whether a proximal/damped iteration converges to a *mixed* or *split* schedule; the relation between cycle amplitude and the duality gap of the set-partitioning LP relaxation.
4. **No principal–agent model where the private type is a feasibility set of a combinatorial optimization problem.** Closest: online EV mechanisms with private time windows (interval types). A hidden *duty network* (exponentially many implicit constraints, verifiable only through delivered service) is a different screening object; even the right notion of "type space" (sublattices? matroid-like families? cost-function equivalence classes of V(·)) is unformalized.
5. **Markets-vs-hierarchies has never been made quantitative for energy indivisibilities.** Scarf (1994) + O'Neill et al. (2005) supply the machinery: the linear-price decentralization loss for the SO–fleet interface *equals an integer-programming duality gap*, and two-part transfer prices (uplift) close it — but no one has connected this to Williamson-style organization choice, nor asked when uplift-style internal transfers remain incentive-compatible under private fleet information.
6. **Emissions-vs-cost divergence for scheduling (not just charging-rate) flexibility is unquantified theoretically.** Empirical Pareto frontiers exist (Wageningen; ISGT V2G), and the signal-validity problem at scale is known (Nature Comms cascading MEF), but there is no structural result of the form "the cost-optimal and MEF-optimal schedules of a combinatorial fleet coincide iff the merit order is emissions-monotone," nor an analysis of a *price-and-emissions-making* fleet (its charging changes both signals simultaneously).
7. **Performative stability with discontinuous response maps.** The entire performative-prediction literature assumes Lipschitz/continuous distribution maps. An atomic fleet's response is piecewise-constant with jumps: existence, uniqueness, and learnability of performatively stable price forecasts in this regime are open — as is the two-sided version (SO biases forecast, fleet strategizes).
8. **The microgrid limit (fleet = dominant load) has no market-theoretic treatment.** Major–minor MFG assumes a continuum fringe; PoA storage papers assume a large market; monopsony empirics measure a few percent markdown. When the fleet is 50–90% of load, prices are almost entirely self-generated — the "market" degenerates and the right comparison is dictator vs internal-transfer-price mechanisms, which nobody has analyzed.

---

## Creative ideas (research-idea sketches)

1. **Four-regime welfare theorem for combinatorial flexibility.** Setting: hours t=1..T, inverse supply g_t increasing convex piecewise-linear, fleet with finite schedule set 𝒮, V(p)=min_S c(S)+p·e(S). Define system costs W_U (uncontrolled), W_T (fixed point or limit-cycle average of naive taker iteration), W_M (bill minimizer), W_D (planner). *Conjecture/theorem targets:* (i) W_D ≤ W_M always; (ii) for affine g, W_M/W_D ≤ 4/3 with the bound tight **even over combinatorial 𝒮** (the Jiang et al. "structural invariant" argument may survive because it only uses objective misalignment, not convexity of the feasible set — verify); (iii) **∃ instances with W_T > W_M and even W_T > W_U** (self-defeating taker strictly worse than doing nothing), constructed from a two-hour valley with a kink of V between the hours; (iv) W_T − W_D is bounded by (max_t Δg_t)·(fleet energy), i.e., the taker's loss is controlled by the price-curve step sizes at the herding hour. Item (iii) would be a headline result: *price signals can be worse than no signals for a single large discrete agent* — the atomic-agent formalization of the avalanche effect.

2. **Discrete monopsony markdown lemma.** For the bill minimizer with schedule set 𝒮: show the optimal strategic distortion is characterized by a "virtual price" p̃_t = g_t(U_t+L_t) + L_t·g_t'(U_t+L_t) (marginal outlay), and that the strategic schedule is S_M ∈ argmin c(S) + p̃·e(S) — i.e., **regime M = regime T evaluated at the marginal-outlay price vector**. Consequences: (a) M is implementable by the same EVSP column-generation oracle with modified prices (algorithmic payoff); (b) the monopsony distortion is exactly the difference of two supergradient selections of V at p vs p̃, so it *jumps discretely* — small fleets exhibit zero distortion until a threshold size, then a lumpy withholding jump (no smooth markdown), a qualitatively new monopsony phenomenon worth its own paper.

3. **Cobweb/cycling theorem for the taker iteration.** Model L^{k+1} ∈ e(argmin_S c(S)+g(U+L^k)·e(S)). Prove: (i) if g is a step function (merit order) and V has a kink straddled by two schedules with loads L_a≠L_b, the iteration admits a 2-cycle {L_a, L_b} and no fixed point exists whenever no schedule's load self-confirms; (ii) a damped iteration on *prices* (p^{k+1} = (1−α)p^k + α·g(U+L^k)) converges for α small iff the market admits a "mixed schedule equilibrium" — a lottery/split over schedules whose expected load self-confirms; (iii) relate the existence of pure fixed points to integrality of the set-partitioning LP: **the taker iteration has a fixed point iff the convexified (column-generation master) problem has an integral optimum at the equilibrium price** — tying convergence of the market loop to the duality gap of the thesis's own solution algorithm. This would unify themes 2, 6, and the team's computational machinery in one theorem.

4. **Performative stability with jumps: existence via mixing, nonexistence in pure forecasts.** Import Perdomo et al.'s framework: forecaster publishes p̂, fleet best-responds, realized price is Γ(p̂). Γ is piecewise-constant ⇒ Brouwer/Grunberg–Modigliani fails; prove (i) a performatively stable *distributional* forecast (over the finitely many kink cells) always exists (Kakutani on the simplex over schedules); (ii) repeated retraining converges to it iff the damping of idea 3 holds; (iii) define the fleet's **performative power** (Hardt et al.) in closed form: P = max_{S,S'} ‖g(U+e(S))−g(U+e(S'))‖, and show the T/M welfare gap is O(P·fleet energy) — making "big enough to matter" a measurable causal quantity. Positioning: first performative-prediction analysis with a combinatorial responder; publishable at an ML venue *and* usable in the thesis.

5. **Screening a fleet whose type is a feasibility set.** Principal (SO, knows g) contracts with fleet (knows 𝒮 and c privately). Key structural object: the fleet's *reported* value function V̂(p) must be concave piecewise-linear with supergradients in a feasible-load lattice — so the type space is effectively the space of support functions of discrete sets. Ideas: (i) show the revelation principle reduces the mechanism to a **menu of load-profile/payment pairs** = a priority-service-style menu over profiles rather than reliabilities (Chao–Wilson generalization); (ii) prove an "information rent = duality gap" theorem: if the true 𝒮 were convex, efficient two-part transfers exist (O'Neill-style) with zero rent under some conditions; with indivisibilities, any IC mechanism leaves rent bounded below by a quantity proportional to the integrality gap of the fleet's scheduling LP — **a mechanism-design meaning for the integrality gap**; (iii) study "burning"-type inefficiency (Gerding et al.) in this setting: does efficiency require the SO to sometimes command strictly wasteful duties?
 
6. **Markets vs hierarchies, quantified on the microgrid.** Using the team's microgrid manuscript as the testbed: compare (a) full hierarchy (dictator MILP), (b) internal linear transfer prices (iterated or equilibrium), (c) internal two-part transfer prices (linear + uplift per O'Neill et al.), (d) menu mechanism from idea 5. Theorem targets: cost(b) − cost(a) = duality gap of the joint UC+EVSP relaxation (can be large; construct worst cases); cost(c) = cost(a) under complete information but not IC under private 𝒮; empirical section quantifies all gaps on real data. This is a self-contained "economics of the microgrid org chart" paper — directly the Williamson/Scarf synthesis nobody has done.

7. **Emissions-dictator vs cost-dictator divergence bound.** Both dictators solve min over the same 𝒮 with different hourly signals (price stack vs emissions stack). Characterize the schedule-overlap: if the merit order is *emissions-monotone* (cost order = emissions order), schedules coincide; define a rank-correlation-type statistic ρ between the two stacks and bound the emissions excess of the cost-dictator by a function of (1−ρ) and the fleet's shiftable energy. Add the performative twist from theme 5: for a large fleet, MEF signals are invalidated by the fleet's own response (Nature Comms cascading argument), so prove the "cascading MEF" fixed point is exactly the emissions-dictator's optimum — unifying the 24/7-CFE debate with the thesis's price-formation machinery.

8. **Major–minor game: atomic EVSP fleet + convex fringe.** One major player with discrete strategy set, continuum fringe of convex chargers (mean field à la Ma et al.). Questions: existence of equilibrium (mixed for the major player); does the fringe damp or amplify the major's cycling (fringe absorbs price jumps ⇒ restores continuity of the effective residual price curve ⇒ convergence — a "fringe as stabilizer" theorem); comparative statics of the welfare gap in the fleet/fringe size ratio, interpolating the national-market and microgrid poles of the thesis. This would be the first major–minor model whose major player is an integer program.

9. **Regulatory design for a benevolent-ish fleet.** Given the M regime's bill minimization is mostly a transfer (Hogan/Order-745 logic), design a *simple* correction: charge the fleet the marginal-outlay wedge L_t·g_t' as a "market-impact fee" and prove it implements D in dominant strategies when g is known — then show the fee mis-implements D when the fleet has private duty costs, quantifying the residual distortion. Connects theme 1b, 4, and gives a policy-facing chapter.

10. **Empirical/computational companion: measuring the fleet's performative power in the team's microgrid data.** Estimate P (idea 4) and the four welfare points (idea 1) from the existing co-optimization model by toggling objectives; report whether W_T > W_M occurs in real data (candidate headline empirical fact: "naive price-taking by our truck fleet costs more than strategic bidding *and* raises system cost — coordination, not sophistication, is the binding constraint").

---

## Search-provenance note

All bibliographic claims above derive from web searches conducted 2026-08-14. DOIs are reported only where the DOI string was visible in retrieved content; where author lists were not visible in snippets this is flagged inline rather than guessed. Grey literature (course notes, regulatory filings, working papers, white papers) is labeled as such.
