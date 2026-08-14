# Agent 2 — Deep Literature Research: The "Benevolent Dictator" Problem and Decomposition-as-Price-Formation

**Scope.** This report supports a PhD-thesis planning effort on the electric vehicle scheduling problem (EVSP) coupled to electricity price formation, with three regimes: (i) price-taking fleet, (ii) strategic price-maker fleet, (iii) integrated "benevolent dictator" (joint generation dispatch + fleet scheduling). The central hypothesis investigated here: **the naive price-iteration loop (post price → solve fleet → aggregate load → recompute marginal-cost price → repeat) is exactly an unstabilized price-based (Lagrangian / Dantzig-Wolfe) decomposition of the dictator problem, and stabilized column generation / bundle / proximal methods are the principled fix.**

**Method note.** All findings below come from extensive web searches (August 2026). DOIs are reported **only when actually observed** in search results or fetched pages. Where a DOI was not observed, this is stated explicitly. A few well-known references that could not be verified in this session are flagged `[verify]`.

**Headline verdict (details in §6):** The hypothesis appears to be *assembled from known parts but not published as a unified frame* for fleet + generation coordination. Each ingredient exists separately — (1) price iteration oscillates (EV-charging control literature, tatonnement economics), (2) Dantzig-Wolfe masters compute price signals for flexible demand (Najafi & Fripp 2023; Anjos, Lodi & Tanneau 2018), (3) stabilization fixes dual oscillation with convergence guarantees (du Merle et al. 1999; Frangioni 2002; Pessoa et al. 2018), (4) the duality gap of the integrated nonconvex problem is exactly minimum uplift (Gribik-Hogan-Pope 2007; Andrianesis et al. 2021). **No paper found states: "the fleet-charging chicken-and-egg iteration IS unstabilized decomposition of the joint fleet+generation problem, and stabilization is the principled damping."** The closest threats are listed in §7.

---

## 1. Classics and theory: price-based decomposition, instability, and stabilization

### 1.1 Foundational decomposition papers

- **Dantzig, G.B. & Wolfe, P. (1960), "Decomposition Principle for Linear Programs," *Operations Research* 8(1):101–111. DOI: 10.1287/opre.8.1.101.**
  The original price-directed decomposition: a master LP over convex combinations of subsystem proposals, with dual prices sent to subproblems that return new proposals (columns). Finite convergence for LPs. Economically, the master is a coordinator that "buys" proposals at internal prices.
  *Relevance:* The dictator problem's LP master (energy balance + generation cost, fleet columns) is a textbook DW structure; the thesis frame starts here.

- **Marsten, R.E., Hogan, W.W. & Blankenship, J.W. (1975), "The Boxstep Method for Large-Scale Optimization," *Operations Research* 23(3):389–405. DOI: 10.1287/opre.23.3.389.**
  The first trust-region stabilization of cutting-plane/price-directed methods: restrict the dual iterate to a box around the incumbent, creating a continuum between steepest ascent and pure cutting planes. The companion piece "The Use of the Box Step Method in Discrete Optimization" (DOI: 10.1007/bfb0120702) documents the instability phenomena that motivated it (wild dual moves, degeneracy of the convexified dual, heavy re-optimization overhead).
  *Relevance:* Historically the earliest "damped price update with a proof"; note co-author Hogan later founded uplift/CH-pricing theory — a poetic closing of the loop for the thesis narrative.

- **Lemaréchal, C. (2001), "Lagrangian Relaxation," in Jünger & Naddef (eds.), *Computational Combinatorial Optimization*, LNCS 2241, Springer, pp. 112–156. (No DOI observed.)**
  Canonical survey: prices replace coupling constraints; the dual function's value is the concave hull; Everett's theorem; the "filling property" for primal recovery; duality gaps under nonconvexity; equivalence of Lagrangian dual and DW master (column generation solves the dual).
  *Relevance:* The formal identity "Lagrangian price iteration = DW column generation seen in the dual" that the thesis hypothesis rests on is stated here in full generality.

### 1.2 Instability of pure price iteration (cutting-plane view)

- **Briant, O., Lemaréchal, C., Meurdesoif, Ph., Michel, S., Perrot, N. & Vanderbeck, F. (2008), "Comparison of Bundle and Classical Column Generation," *Mathematical Programming*. (PDF verified at bipop.inrialpes.fr; DOI not observed in this session.)**
  Shows that standard LP-master column generation is exactly Kelley/Cheney-Goldstein cutting planes in the dual, which is unstable with poor theoretical convergence rates; compares boxstep, piecewise-linear penalties, and quadratic bundle stabilizers across cutting stock, vertex coloring, CVRP, lot sizing, TSP.
  *Relevance:* The precise technical statement of "unstabilized price iteration = Kelley = unstable" — the negative half of the thesis hypothesis.

- **"An optimal variant of Kelley's cutting-plane method," arXiv:1409.2636.**
  Documents that Kelley's method "suffers from very poor performance, both in practice and in theory," attributing it to iterate instability, and that bundle methods (Lemaréchal; Wolfe) overcame this with a quadratic regularizer. Provides a stabilized variant with optimal worst-case rate.
  *Relevance:* Citable theory statement that instability is intrinsic to unregularized price updates, not an implementation artifact.

### 1.3 Stabilized column generation and bundle methods

- **du Merle, O., Villeneuve, D., Desrosiers, J. & Hansen, P. (1999), "Stabilized Column Generation," *Discrete Mathematics*. DOI: 10.1016/s0012-365x(98)00213-1.**
  The classic LP-friendly stabilization: penalize dual deviation from a stability center via a piecewise-linear (box + penalty) term implemented with bounded surplus/slack columns; update center on improvement ("serious step"); speedups up to 10x reported.
  *Relevance:* Drop-in stabilization for the Cho-Lodi-Scaglione dictator master — the concrete "damping with a certificate" the thesis proposes.

- **Frangioni, A. (2002), "Generalized Bundle Methods," *SIAM Journal on Optimization* 13(1):117–156. DOI: 10.1137/s1052623498342186.**
  Unifies bundle variants under arbitrary closed convex stabilizing terms; proves finite termination / asymptotic convergence / finite convergence under various hypotheses on the stabilizer and the function; dual view of bundle methods as inner linearization.
  *Relevance:* The general convergence theory the thesis can invoke: *any* reasonable proximal damping of the price iteration inherits guarantees.

- **Frangioni, A. & Gendron, B. (2013), "A Stabilized Structured Dantzig-Wolfe Decomposition Method," *Mathematical Programming*. DOI: 10.1007/s10107-012-0626-8.**
  Extends DW to alternative ("structured") master models of the easy polyhedron and shows the same stabilization machinery applies, with convergence theory inherited from generalized bundle methods; computational gains on multicommodity network design.
  *Relevance:* Template for stabilizing a *nonstandard* master — the dictator master is nonstandard (contains generation variables and energy-balance rows, not just convexity rows).

- **Pessoa, A., Sadykov, R., Uchoa, E. & Vanderbeck, F. (2018), "Automation and Combination of Linear-Programming Based Stabilization Techniques in Column Generation," *INFORMS Journal on Computing* 30(2):339–360. DOI: 10.1287/ijoc.2017.0784.**
  Links dual-price smoothing (Wentges-style) to in-out separation; derives generic convergence properties; self-adjusting parameters; shows smoothing + penalty stabilization have cumulative speedups.
  *Relevance:* Modern, parameter-light stabilization recipes for the thesis implementation; also the cleanest published statement that smoothing = damped price updates.

- **Lübbecke, M. & Desrosiers, J., "Selected Topics in Column Generation" (Optimization Online preprint 2002/580; published in *Operations Research* 2005 — DOI not observed).**
  Survey covering dual oscillation ("wild oscillations of dual variables produce extreme columns"), boxstep, du Merle-style stabilization, bundle and ACCPM alternatives, Ben Amor's primal-dual stabilization.
  *Relevance:* One-stop citation for the phenomenology of unstabilized CG: tailing off, extreme columns from extreme prices — precisely the "oscillating fleet response to naive prices."

### 1.4 Economics lineage: prices coordinate subproblems, and tatonnement fails

- **Arrow, K.J. & Hurwicz, L. (1951/1958), "A Gradient Method for Approximating Saddle Points and Constrained Maxima," RAND P-223 (1951); reprinted as book chapter, DOI: 10.1007/978-3-0348-0439-4_2.**
  Primal-dual gradient dynamics on the Lagrangian: prices rise with excess demand, agents best-respond. Convergence requires (strict) concavity/convexity; the mechanism is a mathematical formalization of Walrasian tatonnement and of "decentralization through prices" (see also Arrow-Hurwicz, "Decentralization and Computation in Resource Allocation").
  *Relevance:* The naive price loop in the EV setting is an Arrow-Hurwicz/Uzawa iteration; its known failure modes under nonconvexity are exactly what the thesis will exhibit.

- **Scarf, H.E. (1960), "Some Examples of Global Instability of the Competitive Equilibrium," *International Economic Review*. DOI: 10.2307/2556215.**
  The famous counterexample: economies with cyclic preferences where tatonnement orbits forever around the unique equilibrium. Later work (Hirota; Kumar & Shubik, SFI WP 01-12-074) shows stability depends on the *adjustment mechanism*, not just the economy.
  *Relevance:* The canonical "price iteration cycles" result; a fleet flip-flopping between two charging windows is a discrete Scarf economy. Also: experimental confirmation in **Anderson, Granat, Plott & Shimomura, "Global Instability in Experimental General Equilibrium: The Scarf Example" (Caltech preprint, DOI: 10.7907/pvhqy-8kz29)** — real traders orbit as predicted.

- **Kim, C. (1970), "Decomposition of Planning Systems," *Decision Sciences*. DOI: 10.1111/j.1540-5915.1970.tb00790.x.**
  Explicitly recognizes that Dantzig-Wolfe, formulated as a computational device, doubles as a *planning protocol*: centralized optimality within a decentralized organizational structure, and explores implementation problems.
  *Relevance:* Establishes the long pedigree of "decomposition = internal price-mediated planning"; the thesis modernizes this for fleet + microgrid.

- **Kornai, J. & Lipták, T. (1965), "Two-Level Planning," *Econometrica*. DOI: 10.2307/1911892.**
  The quantity-directed dual to price-directed planning: headquarters allocates resource quotas; sectors report shadow prices; a game-theoretic iteration converges for the LP economy.
  *Relevance:* The "prices vs quantities" alternative *inside* the dictator problem (Benders-style resource direction vs DW-style price direction) — a natural axis for thesis experiments.

**Convergence guarantees, summarized.** For convex (LP) problems: unstabilized DW/Kelley converges finitely but with no useful rate and empirically wild dual oscillation; pure subgradient/Uzawa steps converge only with diminishing step sizes (slow, no certificates at iterates). Stabilized versions: boxstep and du Merle converge finitely with monotone certificate improvement; generalized bundle methods (Frangioni 2002) give finite termination or asymptotic convergence with serious-step descent guarantees; level/proximal bundle enjoy O(1/ε²)-type worst-case complexity (cited in arXiv:1409.2636 discussion). For nonconvex/integer subproblems: all price-based methods solve only the *convexified* (Lagrangian dual = convex hull) problem; convergence is to the dual optimum with a residual duality gap; primal recovery needs heuristics or a final restricted-master MIP (see §4).

---

## 2. Power systems: prices as multipliers, price-based coordination of demand, distributed methods

### 2.1 Lagrangian relaxation for unit commitment

- **Bragin, M.A. (2023), "Survey on Lagrangian Relaxation for MILP: Importance, Challenges, Historical Review, Recent Advancements, and Opportunities," arXiv. DOI: 10.48550/arxiv.2301.00573.**
  Frames LR explicitly in economic terms: multipliers are shadow prices that rise when "demand exceeds supply"; documents that dual values understate primal values (duality gap generically nonzero with integers), that relaxed solutions are infeasible and must be heuristically repaired, and that "price-based coordination... has been the subject of intensive research for decades because of the fundamental difficulties of non-smooth optimization."
  *Relevance:* A recent authoritative source that *already speaks the thesis's language* (price-based coordination of integer subproblems) — cite carefully and differentiate.

- **Kim, S. et al. (2012), "Evaluation of Two Lagrangian Dual Optimization Algorithms for Large-Scale Unit Commitment Problems," *J. Electrical Engineering & Technology* 7(1). DOI: 10.5370/jeet.2012.7.1.17.** *(Author list not fully captured; venue/DOI verified.)*
  Benchmarks subgradient vs cutting-plane multiplier updates on large UC libraries; the cutting-plane method "suffers considerable oscillations" and is slow to approach the dual optimum — an empirical UC-scale replication of Kelley instability.
  *Relevance:* Power-systems evidence that the *unstabilized* dual update oscillates on generation-side problems, mirroring the fleet-side oscillation.

- Classic LR-UC phenomenology (documented in the above and in an LR-UC thesis surveyed): identical/similar units "chatter" — committed and decommitted together as marginal units under small multiplier changes; flat dual ("flat bottom") with multiple near-optimal commitments; final iterates need not be feasible, so the best feasible schedule is tracked externally.
  *Relevance:* "Chattering of identical units" is the generation-side twin of "fleet flip-flop between charging windows"; both are symptoms of dual non-uniqueness under indivisibility.

### 2.2 Price-based coordination of flexible demand via decomposition

- **Najafi, F. & Fripp, M. (2023), "Market-based coordination of price-responsive demand using Dantzig-Wolfe decomposition method," *Energy and AI*. DOI: 10.1016/j.egyai.2023.100277 (arXiv version DOI: 10.48550/arxiv.2302.00166).**
  The paper flagged in the project brief. A grid operator solves the DW master (marginal generation-cost pricing) and broadcasts price signals; price-responsive devices (EVs as interruptible loads, water heaters) solve subproblems and return energy bids/columns. Claims: with **convex** subproblems, convergence to the optimum (= Nash equilibrium) in finitely many iterations; generation cost, payments, and peak-to-average ratio all fall.
  *Relevance:* **Closest published antecedent to novelty claim (a)** — explicitly "master computes prices, devices are subproblems, DW theory gives convergence." Crucially it (1) assumes convex subproblems, (2) has no timetabled trip-covering fleet scheduling, (3) does not discuss stabilization, oscillation of the naive loop, duality gaps, or uplift. The thesis must cite and sharply differentiate.

- **Anjos, M.F., Lodi, A. & Tanneau, M. (2018), "A Decentralized Framework for the Optimal Coordination of Distributed Energy Resources," *IEEE Transactions on Power Systems*. DOI: 10.1109/tpwrs.2018.2867476.**
  DW/column-generation coordination of heterogeneous DERs whose operation is *any MILP*; same optimality guarantees as centralized (for the convexified relaxation, with a final integer step); distributed, private, robust to data changes; tested on Ontario market data.
  *Relevance:* Proves the architecture works with **integer** subproblems and is co-authored by Lodi (bridge to the team's own work). Framed as computation, not as price formation or stabilization theory — the thesis's economic reading (naive iteration = this method without stabilization; gap = uplift) is absent.

- **Gan, L., Topcu, U. & Low, S.H. (2013), "Optimal Decentralized Protocol for Electric Vehicle Charging," *IEEE Transactions on Power Systems*. DOI: 10.1109/tpwrs.2012.2210288 (CDC 2011 version DOI: 10.1109/cdc.2011.6161220).**
  Utility broadcasts a control/price signal; EVs update charging profiles; the signal includes a penalty that makes the iteration converge to valley-filling optima even with asynchronous updates. Convergence *requires* the added quadratic penalty on deviation — i.e., damping.
  *Relevance:* Price-iteration + damping with proofs, for charging *profiles* (convex per-EV sets, no duties). A key stepping stone the thesis subsumes.

- **Ma, Z., Callaway, D.S. & Hiskens, I.A. (2013), "Decentralized Charging Control of Large Populations of Plug-in Electric Vehicles," *IEEE Transactions on Control Systems Technology* 21(1):67–78. DOI: 10.1109/tcst.2011.2174059.**
  Nash-certainty-equivalence (mean-field) charging negotiation. Documented explicitly (in the companion PDF examined): with pure best response to broadcast prices, "the iterative procedure oscillates indefinitely" — agents move in unison; adding a tracking-cost δ‖u − avg(u)‖² makes the map a contraction and yields convergence to the unique Nash equilibrium (valley-filling in the homogeneous limit); they quantify the range of δ that guarantees convergence.
  *Relevance:* **The sharpest published statement that naive price iteration for EV fleets oscillates and that a proximal-like penalty fixes it** — but framed as mean-field game theory, with convex individual sets, no integer duties, no LP duality certificates, no decomposition language.

- **Ma, Z., Zou, S., Ran, L., Shi, X. & Hiskens, I.A. (2016), "Efficient decentralized coordination of large-scale plug-in electric vehicle charging," *Automatica* 69:35–47. (DOI not observed.)**
  Price update = weighted average of previous price and marginal cost at forecast demand (i.e., explicit damping/smoothing of the price path); convergence under mild conditions "without artificial deviation costs"; converged price = marginal generation cost, so the outcome is socially optimal.
  *Relevance:* Damped tatonnement done right in the EV setting; still convex, aggregate-profile world. Notably, the price-smoothing step is literally Wentges-style dual smoothing — an unexploited connection the thesis can make precise.

### 2.3 ADMM / distributed methods and their trouble with integers

- **"Computational Performance Study on the ADMM Algorithm for a Demand Response Peak Shaving Application," *IEEE Systems Journal* (2023). DOI: 10.1109/jsyst.2023.3234709.** *(Authors not captured.)*
  Benchmarks fully parallel ADMM for residential DR; states plainly that with integer/nonconvex device models "ADMM turns into a heuristic... one can ensure neither convergence nor global optimality," and points to Dantzig-Wolfe as the more suitable alternative for mixed-integer subproblems.
  *Relevance:* Justifies the thesis's choice of DW/CG (not ADMM) as the principled decomposition when fleet decisions are integer: DW at least solves the convexified problem exactly and yields valid bounds.

- **ADMM-for-MIP workarounds** (from an NREL distribution-network paper, docs.nlr.gov/fy21osti/79129.pdf, and arXiv:2511.08750 / DOI: 10.48550/arxiv.2511.08750): relax-and-fix binaries progressively; relaxed-then-refine two-phase schemes; objective-based convergence checks; heavy sensitivity to penalty parameter ρ (divergence possible). None offers optimality certificates.
  *Relevance:* Catalogues the ad-hoc landscape the thesis's LP-certificate-bearing approach improves upon; also a useful "related distributed methods" section.

- **Distributed EV-charging surveys/variants**: dual decomposition for residential load control has documented slow convergence; Frank-Wolfe-based EV coordination exists. (Secondary citations inside the OSTI ADMM report, DOI not applicable.)
  *Relevance:* Background breadth for the related-work section.

**What this literature says about duality gaps:** with integer subproblems, all price-mediated methods (LR, DW, dual decomposition, ADMM) coordinate at best the *convex hull* of each agent's feasible set; the residual gap manifests as infeasibility of the price-response profile (fractional mixtures of schedules) that must be repaired — by heuristics (LR-UC), a final restricted-master MIP (DW), rounding phases (ADMM). The gap's economic name is *uplift* (§4).

---

## 3. Integrated transport-energy planning (co-optimizing generation + vehicle scheduling)

### 3.1 True co-optimization with fleet schedules

- **Cho, N., Lodi, A. & Scaglione, A. (2025), "Electric Vehicle Scheduling and Vehicle-to-Grid Integration in Microgrids," arXiv:2508.06752. DOI: 10.48550/arxiv.2508.06752.**
  The team's own manuscript (public since Aug 2025, code at github.com/ndandnd/evspv2g): military-microgrid dictator problem; column generation with an LP master containing energy balance and generation costs; DP pricing generates truck route-and-energy-profile columns; final restricted master MIP. Demonstrates fuel/cost reductions from V2G-enabled joint scheduling.
  *Relevance:* The dictator-problem artifact the thesis builds on; being on arXiv, its framing (computational OR, military microgrid) is public but does **not** claim the decomposition-as-price-formation frame — that space is still open, and best claimed by the same group quickly.

- **Yetkin, M., Augustino, B., Lamadrid, A.J. & Snyder, L.V. (2024), "Co-optimizing the smart grid and electric public transit bus system," *Optimization and Engineering*. DOI: 10.1007/s11081-023-09878-w.**
  Social-planner MPOPF (DC-OPF + ramping) with a transit fleet as *mobile storage*: bus assignment/relocation constraints, charge/discharge, V2G, deterministic + two-stage stochastic variants; quantifies benefit of coordinated vs uncoordinated strategies; analyzes pricing strategies' effect on the co-optimization; explicitly **excludes unit commitment** and does not use trip-level set-partitioning or column generation (MATPOWER cases, solver-based).
  *Relevance:* **Main published "dictator with a transit fleet" competitor.** Differentiators for the thesis: timetabled trip covering via set-partitioning/CG, charging SOC columns, UC-style generation, decomposition/pricing theory, three-regime comparison.

- **"Elastic flexible unit commitment: A scenario-based power-electric fleet analysis," *International Journal of Electrical Power & Energy Systems* (2023). (ADS listing; DOI not observed.)**
  A "master ISO" coordinates day-ahead UC in a coupled power–electric-fleet network with PEVs, e-buses, e-taxis, V2G/B2G, incentive-based DR, scenario-based uncertainty; MILP on IEEE 6/24-bus systems. Fleet temporal/spatial patterns matter, but vehicles follow *travel patterns*, not optimized timetabled duties.
  *Relevance:* Shows UC + fleet coupling exists in MILP form; still no trip-covering scheduling decisions, no decomposition theory.

- **Wei, W., Mei, S., Wu, L., Shahidehpour, M. & Fang, Y. (2016), "Optimal Traffic-Power Flow in Urban Electrified Transportation Networks," *IEEE Trans. Smart Grid* 8(1):84–95. DOI: 10.1109/tsg.2016.2612239.**
  ISO co-optimizes generation schedule and road congestion tolls subject to traffic user equilibrium of EV route choices; MISOCP reformulation; shows ignoring interdependence can produce insecure operation.
  *Relevance:* The "coupled infrastructures" school: co-optimization of power + *traffic assignment* (aggregate flows), not fleet duties. Companion works: **Wei, Wu, Wang & Mei (2017), "Network Equilibrium of Coupled Transportation and Power Distribution Systems," DOI: 10.1109/tsg.2017.2723016** — equilibrium as a fixed point computed by *best-response iteration between the traffic problem and OPF* (an unstabilized block-coordinate loop in the convex setting!); and the review **Wei et al. (2019), J. Modern Power Systems & Clean Energy, DOI: 10.1007/s40565-019-0516-7**. Also **Gan, Shahidehpour et al. (2020), "Coordinated Planning of Transportation and Electric Power Networks...," DOI: 10.1109/tsg.2020.2989751**.

- **E-bus + charger joint scheduling via LR:** "A Joint Scheduling Framework for Electric Bus Fleets and Charging Infrastructure in Urban Transit Systems," *Systems* 14(3):235. DOI: 10.3390/systems14030235. Continuous-time MILP coupling fleet assignment, SOC dynamics, charger capacity; solved by Lagrangian-relaxation decomposition (fleet subproblem + charger subproblem) with an LP diving heuristic and explicit lower/upper bounds. Similarly, an *Applied Energy* e-bus charging-scheduling paper (S030626192201769X; DOI not observed) decomposes the fleet charging problem by bus via LR with bi-criterion DP subproblems under TOU tariffs and site load caps; and an arXiv e-bus paper (2309.00523) combines charging scheduling with real-time operational control via LR + dual decomposition.
  *Relevance:* LR-with-prices *within* transit scheduling exists — but the "generation side" is always an exogenous tariff, never co-optimized dispatch. The dictator's two-sided master remains distinctive.

### 3.2 The value of integration vs sequential/price-mediated planning

- **Brown, T. et al. (2018), "Synergies of sector coupling and transmission reinforcement in a cost-optimised, highly renewable European energy system," *Energy*. DOI: 10.1016/j.energy.2018.06.222.**
  PyPSA-Eur-Sec-30: co-optimizing electricity + heat + transport (BEV flexibility) reduces total system cost substantially; BEV flexibility pairs with solar diurnal cycles; the more tightly sectors are coupled, the less transmission is needed.
  *Relevance:* Macro evidence that integrated planning beats siloed planning; fleet flexibility is one of the biggest levers. The thesis provides the *micro/operational, exact-optimization* counterpart.

- **ACER (2024), "Welfare Benefits of Co-Optimising Energy and Reserves" (report, no DOI).**
  Co-optimizing energy + balancing capacity vs sequential clearing: ≈2.1% operational cost savings, extrapolated to ~€1.28B/yr EU-wide.
  *Relevance:* Regulator-grade precedent for quantifying "integration value" as a percentage of system cost — the same metric the thesis's regime-(i)-vs-(iii) experiments should report.

- **PyPSA-DE (2025), arXiv:2510.09414:** integrated national planning reduces German grid expansion by one-third (€92B savings) vs the sequential national plan. *(Preprint; no DOI observed.)*
  *Relevance:* Same message at planning scale; also a reminder that "value of integration" numbers are headline-friendly.

- **A sequential-vs-integrated comparison in maritime refueling** ("A comparative analysis of sequential and integrated optimization models for ship refueling operations," *Electronic Research Archive*, DOI landing 10.3934/era.2026025 — DOI string observed on landing page): integrated model beats two-stage by 1–13%, gap growing with network size.
  *Relevance:* Cross-domain evidence that decoupled "plan then price" pipelines lose more as coupling grows — a hypothesis the thesis can test for fleet-vs-microgrid size ratios.

**Gap:** no found work quantifies integration value for a *timetabled, trip-covering* fleet against a *dispatch/UC* model in one exact optimization, let alone decomposes the sequential-planning loss into "convexification gap + strategic distortion + iteration truncation." That decomposition is a thesis-sized contribution.

---

## 4. Duality gap = internal uplift: pricing under indivisibilities and organizational remedies

### 4.1 Nonexistence of supporting prices under indivisibility (the disease)

- **Gomory, R.E. & Baumol, W.J. (1960), "Integer Programming and Pricing," *Econometrica* 28(3). DOI: 10.2307/1910130.**
  First attempt at IP shadow prices (from cutting-plane duals): prices exist but are algorithm-dependent, can misprice resources, and lose the marginal interpretation; decentralization by prices only partially survives indivisibility. Refinements: **Alcaly & Klevorick (1966), DOI: 10.2307/1909864**; **Wolsey, L.A. (1981), "Integer programming duality: price functions and sensitivity analysis," *Mathematical Programming* 20:173–195, DOI: 10.1007/bf01589344** (nonlinear price *functions* are needed); **"Integer programming and pricing revisited," *IMA J. Management Mathematics* 8(3):203–, DOI: 10.1093/imaman/8.3.203** (Chvátal-function duals close the gap but are computationally awkward).
  *Relevance:* The mathematical bedrock for "linear internal prices cannot support the integer fleet optimum"; the thesis's DP-priced route columns are exactly the indivisible activities these papers worry about.

- **Baumol, W.J. & Fabian, T. (1964), "Decomposition, Pricing for Decentralization and External Economies," *Management Science* 11(1):1–32. DOI: 10.1287/mnsc.11.1.1.**
  DW decomposition as decentralized decision-making in a multi-division firm; the famous negative result: "in many cases there exist no prices which will lead divisions to make independent decisions that are optimal from the point of view of the company as a whole" (even at the LP optimum, quantity directives are needed at the end).
  *Relevance:* **The internal-transfer-price failure the brief asks about, in the original.** The dictator's final restricted-master MIP is the modern form of Baumol-Fabian's "headquarters must ultimately issue quantity orders."

- Related organizational-economics thread: **Hirshleifer (1957), "Economics of the Divisionalized Firm," DOI: 10.1086/294136** (transfer pricing origins); **Burton, Damon & Loughridge (1974), "The Economics of Decomposition: Resource Allocation vs Transfer Pricing," *Decision Sciences*, DOI: 10.1111/j.1540-5915.1974.tb00617.x** (price-directed DW vs quantity-directed Kornai-Liptak as competing decentralization designs); a quadratic-decomposition transfer-pricing scheme (**DOI: 10.1287/mnsc.14.6.b310**); and a dissenting note (**Maiti & Sengupta 1973, DOI: 10.1287/mnsc.19.12.1459**).
  *Relevance:* A ready-made "decentralization inside the firm" literature to anchor the thesis's story that the fleet+microgrid owner *is* a divisionalized firm coordinating by internal prices.

### 4.2 Electricity-market cures (uplift and convex hull pricing) — reusable internally

- **O'Neill, R.P., Sotkiewicz, P.M., Hobbs, B.F., Rothkopf, M.H. & Stewart, W.R. Jr. (2005), "Efficient market-clearing prices in markets with nonconvexities," *European Journal of Operational Research* 164:269–285. DOI: 10.1016/j.ejor.2003.12.011.**
  IP pricing: solve the MIP, then an LP with integer activities fixed; the LP duals price commodities *and* the integral activities (contract/commitment payments), supporting a Walrasian equilibrium with multi-part prices; answers Scarf's (1994) challenge.
  *Relevance:* Blueprint for *internal* multi-part transfer prices: energy price + per-duty "commitment payment" to each truck route — an interpretable internal settlement for the dictator solution.

- **Gribik, P.R., Hogan, W.W. & Pope, S.L. (2007), "Market-Clearing Electricity Prices and Energy Uplift," working paper (lmpmarketdesign.com; no DOI).**
  Convex hull pricing: choose prices maximizing the optimized Lagrangian; the **minimum total uplift equals the duality gap** between the MIP value and the Lagrangian dual value. CH prices = optimal multipliers of the UC Lagrangian dual.
  *Relevance:* **The exact identity the thesis needs: internal uplift ≡ duality gap of the dictator problem** — DW master duals (which solve the dual) are CH prices, and the final MIP-vs-LP gap is the unavoidable internal make-whole budget.

- **Hua, B. & Baldick, R. (2017), "A Convex Primal Formulation for Convex Hull Pricing," *IEEE Trans. Power Systems*. DOI: 10.1109/tpwrs.2016.2637718.**
  Polynomially solvable primal formulation using explicit convex hulls of unit feasible sets and convex envelopes of costs (SOCP/LP); replaces expensive dual-space methods.
  *Relevance:* When fleet-column hulls are hard, generation-side hulls can still be written explicitly — a hybrid master structure worth exploiting.

- **Andrianesis, P., Bertsimas, D., Caramanis, M.C. & Hogan, W.W. (2021), "Computation of Convex Hull Prices in Electricity Markets With Non-Convexities Using Dantzig-Wolfe Decomposition," *IEEE Trans. Power Systems*. DOI: 10.1109/tpwrs.2021.3122000 (arXiv:2012.13331).**
  DW/CG computes *exact* CH prices with finite convergence and gives "intuition on the price formation rationale"; explicitly notes generalized LP (= DW) solves the Lagrangian dual, and that uplift minimization is exactly the MILP-vs-dual gap.
  *Relevance:* **The published bridge "DW column generation = price formation" on the generation side.** The thesis extends it across the meter: fleet duty columns join generator columns in one master; internal CH prices coordinate both. Also relevant: benchmarking of dual first-order methods for CH prices, **arXiv:2504.01474** (bundle proximal level method among the best — stabilization again).

**Synthesis for the thesis:** In the dictator problem, DW master duals at termination are convex-hull prices *of the integrated fleet+generation economy*; the restricted-master-MIP-vs-master-LP gap is the *minimum internal uplift* — the exact amount by which linear internal prices fail to decentralize truck duties. This connects §1's stabilization theory (how to compute the prices without oscillation) to §4's economics (what the residual gap means). No found paper draws this full circle.

---

## 5. Additional context: strategic (price-maker) fleet literature

- **Stackelberg/MPEC EV-aggregator studies** quantify price-maker vs price-taker outcomes for *aggregate* EV portfolios: e.g., "An Optimized Decision Model for Electric Vehicle Aggregator Participation in the Electricity Market Based on the Stackelberg Game," *Sustainability* 15(20):15127 (2023) (bilevel EVA-vs-ISO, KKT/strong-duality MILP reformulation, price-taker vs price-maker scenario comparison; DOI not directly observed); "Large-scale aggregation of prosumers toward strategic bidding in joint energy and regulation markets," *Applied Energy* (2020) (notes explicitly that "only a few studies pay attention to evaluating the increase of market profit induced by strategic relative to non-strategic behavior"; DOI not observed); stochastic bilevel EV-aggregator trading, *Energies* 12(20):3813 (2019) (DOI not observed).
  *Relevance:* Regime (ii) exists for aggregate batteries/prosumers; **none of these embeds a trip-covering scheduled fleet** — supporting novelty claim (c). Note these are profit comparisons, not welfare-gap decompositions.

- **EVSP baseline:** van Kooten Niekerk, van den Akker & Hoogeveen (2017), "Scheduling electric vehicles," *Public Transport*, DOI: 10.1007/s12469-017-0164-0 (CG with TOU electricity prices, SOC discretization); "Electric Vehicle Scheduling in Public Transit with Capacitated Charging Stations," *Transportation Science*, DOI: 10.1287/trsc.2022.0253 (path-based binary program, CG + diving, 816 trips); Klein & Schiffer branch-and-price for charge scheduling with nonlinear batteries and TOU prices (TRISTAN 2022 paper, no DOI).
  *Relevance:* Confirms the fleet side of the thesis rests on a mature exact-CG literature — but always with **exogenous prices** (regime (i)); the coupling to endogenous price formation is the new move.

---

## 6. Novelty checks — explicit verdicts

**(a) Has anyone framed fleet-charging price iteration as unstabilized decomposition of a joint fleet+generation problem?**
**Not found.** Search probes: "price iteration as Dantzig-Wolfe EV," "tatonnement Dantzig-Wolfe equivalence EV," "chicken-and-egg electricity price fleet schedule iteration," "iterative price update oscillation EV decomposition," and variants. Closest items: (1) **Najafi & Fripp 2023** builds the DW coordinator whose master computes prices — but assumes convex device subproblems, never discusses the naive marginal-cost loop, oscillation, stabilization, or integer duties; (2) **Ma-Callaway-Hiskens** and **Gan-Topcu-Low** *prove* the naive loop oscillates and that damping fixes it — but in mean-field-game/fixed-point language, for convex charging-profile sets, without LP duality, columns, or bounds; (3) **Bragin's 2023 LR survey** describes LR as price-based coordination with shadow prices and supply-demand intuition — generic MILP framing, no fleet/generation instantiation and no tatonnement connection; (4) **Wei et al. 2017** compute a transport-power equilibrium by best-response iteration between two convex problems — an unstabilized block iteration, but convex and market-level, with no decomposition-theoretic reading. The specific identity "naive loop = Uzawa/Kelley on the dictator dual; damping = bundle/proximal stabilization; certificates = master LP bounds; residual gap = uplift" appears unclaimed.

**(b) Has anyone applied stabilized column generation to a combined generation+vehicle-scheduling master?**
**Not found.** Stabilized CG is standard in vehicle routing/scheduling (e.g., a stabilized CG paper for military aircraft mission planning appears in MaRDI listings) and appears in power systems (a "stabilised scenario decomposition algorithm applied to stochastic unit commitment" is cited in the same listing; ML-accelerated stabilized CG for microgrid energy management exists — GNN-based CG for networked microgrids, MPCE paper). CH-price computation uses bundle/level stabilization in the dual (arXiv:2504.01474). But no paper found stabilizes a master that *simultaneously* contains energy balance/generation costs and set-partitioning fleet columns. The Cho-Lodi-Scaglione master is a virgin target.

**(c) Has anyone quantified the welfare gap between price-taking, strategic, and integrated operation for a scheduled fleet (not an aggregate battery)?**
**Not found.** Bilevel/MPEC studies quantify price-taker vs price-maker *profits* for aggregate EV/prosumer portfolios (§5); integration-value studies quantify coordinated vs uncoordinated *costs* for mobile-storage transit fleets (Yetkin et al. 2024) and for sector coupling at planning scale (Brown et al. 2018) — but no three-regime comparison with a trip-covering, set-partitioning fleet model was located. The 2020 *Applied Energy* prosumer paper itself remarks that few studies even compare strategic vs non-strategic outcomes.

---

## 7. Novelty threats (ranked, with mitigation)

1. **Najafi & Fripp (2023), *Energy and AI*, DOI: 10.1016/j.egyai.2023.100277.** Owns "DW master computes the price signal for price-responsive devices; DW theory gives convergence." *Mitigation:* they require convex subproblems and stop at the algorithm; the thesis's contributions are precisely where they stop — integer duty columns, oscillation⇢stabilization theory, duality-gap-as-uplift economics, three-regime welfare comparison. Cite prominently.
2. **Andrianesis, Bertsimas, Caramanis & Hogan (2021), DOI: 10.1109/tpwrs.2021.3122000.** Owns "DW/CG = exact CH price formation with intuition" on the generation side. *Mitigation:* no demand-side scheduling subproblem; the thesis imports their identity into an integrated planner and adds stabilization + fleet indivisibilities.
3. **Anjos, Lodi & Tanneau (2018), DOI: 10.1109/tpwrs.2018.2867476.** Owns "DW/CG coordination of MILP-modeled DERs with centralized-equivalent guarantees." *Mitigation:* computational framing, no generation-side dispatch co-optimization, no stabilization/price-formation analysis; overlapping co-author (Lodi) makes this a foundation rather than a threat, but external examiners will expect explicit differentiation.
4. **Ma, Callaway & Hiskens (2013) / Gan, Topcu & Low (2013) / Ma et al. (2016 Automatica).** Own "naive price iteration oscillates; damped iteration converges" for EV charging. *Mitigation:* convex profile sets, mean-field/fixed-point proofs, no combinatorial duties, no certificates; the thesis should include a result they cannot state: bounds/certificates in the presence of integer duties, plus the formal identification of their damping terms with proximal/bundle stabilizers.
5. **Yetkin, Augustino, Lamadrid & Snyder (2024), DOI: 10.1007/s11081-023-09878-w.** Owns "social-planner co-optimization of grid + transit fleet, value of coordination, pricing analysis." *Mitigation:* no trip-level set-partitioning/CG, no UC, no decomposition theory, no strategic regime; the thesis's operational fidelity and theory are the differentiators.
6. **Bragin (2023) LR survey, DOI: 10.48550/arxiv.2301.00573.** Owns the rhetorical territory "LR = price-based coordination with shadow prices." *Mitigation:* generic; the thesis's specificity (EVSP columns, microgrid dispatch, uplift semantics, tatonnement lineage) goes far beyond.
7. **The e-bus LR papers (Systems 14(3):235, DOI: 10.3390/systems14030235; Applied Energy S030626192201769X; arXiv:2309.00523).** Own "price-mediated decomposition inside transit charging scheduling." *Mitigation:* generation side exogenous; no price-formation claim.
8. **Timing risk on the team's own arXiv (2508.06752):** the dictator formulation and CG machinery are now public; any group combining it with Najafi-Fripp-style framing could pre-empt the unifying story. Publish the framing paper early.

---

## 8. Open gaps (specific, defensible)

1. **No published equivalence theorem** mapping the practitioner's price-iteration loop (marginal-cost re-pricing of aggregated fleet load) to a specific unstabilized dual algorithm (Uzawa step / Kelley cut) on the dictator problem's Lagrangian dual — including the characterization of when it cycles (dual degeneracy / flat dual / discrete best-response jumps).
2. **No stabilized CG study on a two-sided master** (energy balance + generation cost rows + fleet convexity rows): which stabilizer (box, 3/5-piece penalty, quadratic, smoothing) best suits masters whose duals are *electricity prices* with physical meaning and natural warm starts (yesterday's prices)?
3. **No internal-uplift accounting** for organizations: the literature prices uplift in markets (ISO make-whole payments) but not as an *internal decentralization budget* for a fleet+microgrid owner; no numbers exist for how large the fleet-indivisibility uplift is relative to total cost, nor how it scales with fleet size, charger scarcity, or V2G capability.
4. **No welfare ladder** price-taker → strategic → dictator for scheduled fleets (§6c); relatedly, no decomposition of the sequential-planning loss into convexification gap vs strategic withholding vs iteration truncation.
5. **Vanishing-gap asymptotics unproven in this setting:** Shapley-Folkman-type results suggest the per-vehicle duality gap shrinks as fleets grow (many small nonconvex agents), which would prove "price coordination becomes asymptotically exact"; the EV mean-field results (Ma et al.) prove equilibrium existence/convergence in the convex-profile limit but not gap decay for *integer duty* fleets. (Classical tool: Aubin-Ekeland duality-gap estimates `[verify — not retrieved this session]`.)
6. **Asynchrony and truncation:** real operations run one or two price-update rounds per day (day-ahead), i.e., a truncated decomposition; no bounds exist on the suboptimality of k-round stabilized negotiation for fleet+generation systems.
7. **Incentive compatibility of the internal mechanism:** DW-style coordination assumes truthful best responses; nothing found on strategic misreporting by a fleet division inside the CG loop (the Kim 1970 implementation-problems thread stops in the 1970s LP world).
8. **Degeneracy structure:** LR-UC "chattering of identical units" and CG "extreme columns" are documented separately; no analysis of their *interaction* when both sides of the master are degenerate (identical trucks × identical generators) — likely the practically binding stabilization question.

---

## 9. Creative ideas (research-idea sketches)

1. **Theorem: "Tatonnement = Kelley."** Formalize: the naive loop (price ← marginal cost at aggregate fleet load; fleet ← best-response schedule) is exactly (a) an Uzawa subgradient step with unit step size when prices are recomputed from the load, and (b) Kelley's cutting-plane iterate when prices are re-optimized against all past responses. Construct a minimal two-duty, two-period instance where the loop 2-cycles (fleet flip-flops between charging windows; price flip-flops between peak/off-peak) — a discrete Scarf economy. Then prove: du Merle box stabilization (or any generalized-bundle stabilizer per Frangioni 2002) restores finite convergence to the convexified optimum with monotone LP certificates. Deliverable: one crisp paper, "Damping is stabilization: the chicken-and-egg iteration as unstabilized Dantzig-Wolfe."
2. **Algorithm: stabilized price negotiation for EVSP-DR + microgrid.** Reuse the existing EVSP-DR pricing DP unchanged as the fleet oracle; wrap it in a stabilized master (5-piecewise-linear penalty à la du Merle; smoothing à la Pessoa et al. with auto-adjusted parameters; warm-start stability center at historical/TOU prices). Report: iterations-to-certificate vs unstabilized, master LP bound trajectory, and dual-path smoothness (the "price path" a coordinator would actually broadcast — an economically meaningful stability metric no OR paper reports).
3. **Internal uplift atlas.** At CG termination, master duals = convex-hull prices of the integrated economy (Gribik-Hogan-Pope identity via Andrianesis et al.). Define *internal uplift* = restricted-master-MIP value − master LP value, and per-duty lost-opportunity costs under the internal prices. Map uplift as a function of: fleet size (expect O(1/N) per vehicle — see idea 5), charger scarcity, V2G on/off, battery size, trip density. Punchline for practitioners: "how big a make-whole budget does your depot need before prices alone can run it?"
4. **Three-regime welfare ladder on one instance family.** (i) price-taker: EVSP-DR against fixed exogenous prices, then re-dispatch generation against realized load; (ii) strategic: fleet best-responds to an anticipated price function λ(d) (bilevel/MPEC or closed-form linear impact); (iii) dictator: the integrated CG-MIP. Report total-cost gaps (i)−(iii) and (ii)−(iii) as the fleet's share of microgrid load grows. Hypotheses: (i)−(iii) grows superlinearly in price impact; (ii) lies between and can *overshoot* (strategic withholding hurts welfare even as it helps fleet profit).
5. **Theorem: strategic behavior is self-stabilizing (regime ii = proximal step on regime iii's dual).** With affine price impact λ(d)=a+B d (B ⪰ 0), the price-anticipating fleet's objective acquires a quadratic term dᵀBd in aggregate load — formally identical to Ma-Callaway-Hiskens's tracking penalty and to a proximal/augmented-Lagrangian term on the dual of the dictator problem. Conjecture: the strategic best-response iteration converges where the price-taking one cycles, and its fixed point is the dictator optimum *of a modified (B-regularized) problem*, quantifying the "monopsony distortion = over-damping" trade-off. This would unify regimes (ii) and (iii) algorithmically: *the strategic fleet is running a stabilized decomposition of the wrong objective.*
6. **Vanishing-gap asymptotics (Shapley-Folkman for fleets).** Prove per-vehicle duality gap of the dictator problem is O(1/N) as the number of (heterogeneous but uniformly bounded) trucks grows, via Shapley-Folkman/Aubin-Ekeland-type nonconvex duality estimates `[verify base reference]`. Corollary: price-mediated (unstabilized-but-damped) coordination is asymptotically optimal — connecting the mean-field EV results (Ma et al.) to integer-duty fleets and explaining *when* the microgrid/small-fleet case (where the thesis lives) genuinely needs the integrated MIP.
7. **Prices vs quantities inside the dictator.** Implement the quantity-directed dual: Benders/Kornai-Liptak-style allocation of per-depot, per-period energy budgets to the fleet subproblem (which prices them internally), vs the price-directed DW. Compare convergence, certificate quality, and robustness to degeneracy; connect to the Burton-Damon-Loughridge (1974) resource-allocation-vs-transfer-pricing dichotomy and to Weitzman-style prices-vs-quantities intuition under uncertainty `[verify Weitzman citation if used]`. Practical payoff: quantity coordination may be the right *day-ahead contract format* between a transit authority and a utility.
8. **Truncated-negotiation bounds ("how many phone calls does coordination take?").** In practice the utility and fleet exchange k rounds (k=1 in day-ahead TOU reality). Using stabilized CG's monotone bound sequence, derive/measure suboptimality-after-k-serious-steps; propose the *negotiation-round count to ε-certificate* as the headline comparison metric between stabilizers (it is also the communication complexity of the implied market mechanism).
9. **Degeneracy surgery for two-sided masters.** Study the interaction of fleet-side degeneracy (identical trucks ⇒ massively multiple optimal duals) and generation-side flat spots (identical gensets ⇒ chattering): characterize the dual optimal face; test minimum-norm/interior dual selections (cf. minimum-norm-multiplier CG, MDPI *Mathematics* 14(6):931) as "canonical internal prices" with maximal marginal interpretability; propose symmetry-reduced convexity rows.
10. **Internal O'Neill settlement layer.** After the final restricted-master MIP, compute O'Neill-style prices (fix integer duty choices, take LP duals) and compare with the CG/CH prices: two internal transfer-price systems (multi-part exactly-supporting vs uniform minimum-uplift) for the same physical solution. Evaluate which better guides *incremental* decisions (adding a truck, shifting a trip) — an organizational-economics experiment no one has run on a real scheduling model.

---

## 10. Curated bibliography (verified identifiers only)

**Theory/stabilization:** Dantzig & Wolfe 1960 (10.1287/opre.8.1.101); Marsten, Hogan & Blankenship 1975 (10.1287/opre.23.3.389; discrete-optimization companion 10.1007/bfb0120702); du Merle, Villeneuve, Desrosiers & Hansen 1999 (10.1016/s0012-365x(98)00213-1); Frangioni 2002 (10.1137/s1052623498342186); Briant et al. 2008 Math. Prog. (PDF verified, DOI not captured); Frangioni & Gendron 2013 (10.1007/s10107-012-0626-8); Pessoa, Sadykov, Uchoa & Vanderbeck 2018 (10.1287/ijoc.2017.0784); Lemaréchal 2001 LNCS 2241 (no DOI); Kelley-variant arXiv:1409.2636; Lübbecke & Desrosiers survey (Optimization Online 2002/580, no DOI).

**Economics lineage:** Arrow & Hurwicz 1951 RAND P-223 (chapter DOI 10.1007/978-3-0348-0439-4_2); Scarf 1960 (10.2307/2556215); Anderson, Granat, Plott & Shimomura (10.7907/pvhqy-8kz29); Kim 1970 (10.1111/j.1540-5915.1970.tb00790.x); Kornai & Lipták 1965 (10.2307/1911892); Baumol & Fabian 1964 (10.1287/mnsc.11.1.1); Burton, Damon & Loughridge 1974 (10.1111/j.1540-5915.1974.tb00617.x); Hirshleifer 1957 (10.1086/294136); Maiti & Sengupta 1973 (10.1287/mnsc.19.12.1459); quadratic transfer pricing (10.1287/mnsc.14.6.b310).

**Pricing under indivisibilities / uplift:** Gomory & Baumol 1960 (10.2307/1910130); Alcaly & Klevorick 1966 (10.2307/1909864); Wolsey 1981 (10.1007/bf01589344); IP-pricing revisited (10.1093/imaman/8.3.203); O'Neill et al. 2005 (10.1016/j.ejor.2003.12.011); Gribik, Hogan & Pope 2007 (working paper, no DOI); Hua & Baldick 2017 (10.1109/tpwrs.2016.2637718); Andrianesis, Bertsimas, Caramanis & Hogan 2021 (10.1109/tpwrs.2021.3122000; arXiv:2012.13331); CH-price first-order benchmark arXiv:2504.01474.

**Power systems coordination:** Bragin 2023 survey (10.48550/arxiv.2301.00573); LR-UC dual-algorithm evaluation (10.5370/jeet.2012.7.1.17); improved LR-UC (10.24084/repqj05.202); Najafi & Fripp 2023 (10.1016/j.egyai.2023.100277; arXiv 10.48550/arxiv.2302.00166); Anjos, Lodi & Tanneau 2018 (10.1109/tpwrs.2018.2867476); Gan, Topcu & Low 2013 (10.1109/tpwrs.2012.2210288; CDC 10.1109/cdc.2011.6161220); Ma, Callaway & Hiskens 2013 (10.1109/tcst.2011.2174059; CDC 2010 10.1109/cdc.2010.5717547); Ma, Zou, Ran, Shi & Hiskens 2016 Automatica 69:35–47 (no DOI captured); ADMM DR performance study (10.1109/jsyst.2023.3234709); ADMM MIP penalty study (10.48550/arxiv.2511.08750).

**Integrated transport-energy:** Cho, Lodi & Scaglione 2025 (10.48550/arxiv.2508.06752); Yetkin, Augustino, Lamadrid & Snyder 2024 (10.1007/s11081-023-09878-w); Wei, Mei, Wu, Shahidehpour & Fang 2016 (10.1109/tsg.2016.2612239); Wei, Wu, Wang & Mei 2017 (10.1109/tsg.2017.2723016); Wei et al. 2019 review (10.1007/s40565-019-0516-7); Gan, Shahidehpour et al. 2020 (10.1109/tsg.2020.2989751); Cui, Hu & Duan 2021 (10.1109/tsg.2021.3053026); elastic flexible UC with electric fleets, IJEPE 2023 (no DOI captured); e-bus + charger LR scheduling, Systems 14(3):235 (10.3390/systems14030235); e-bus charging LR, Applied Energy (S030626192201769X, no DOI captured); integrated e-bus control arXiv:2309.00523; Brown et al. 2018 (10.1016/j.energy.2018.06.222); ACER 2024 co-optimization report (no DOI); PyPSA-DE arXiv:2510.09414.

**EVSP baseline:** van Kooten Niekerk et al. 2017 (10.1007/s12469-017-0164-0); capacitated-charging EVSP, Transportation Science (10.1287/trsc.2022.0253); Klein & Schiffer TRISTAN 2022 (no DOI).

**Strategic fleet (regime ii):** EVA Stackelberg bilevel, Sustainability 15(20):15127 (DOI not captured); prosumer strategic aggregation, Applied Energy 2020 (S0306261920306711, DOI not captured); stochastic bilevel EV aggregator, Energies 12(20):3813 (DOI not captured).
