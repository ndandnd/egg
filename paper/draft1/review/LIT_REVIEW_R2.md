# Literature review, round 2 (12 November 2026)

Adversarial novelty search for draft1 (`main.tex`, revised 3 November 2026). Organized by the brief's topics A–G. It does not repeat the October/November reviews (`INDEPENDENT_REVIEW.md`, `opf-loop-20261102/ref/opf/LIT_REVIEW.md`, `NOVELTY_RISK.md`); where those already covered a source, this file only adds what changes the assessment.

Access labels: **full** = a legitimate complete copy was opened and the cited section read; **partial** = specific sections read; **abstract** = abstract/metadata only; **blocked** = access refused (login, bot check or paywall), not circumvented. "Crossref-verified" means the DOI was resolved against the Crossref API on 12 November 2026 and title, authors, venue, volume and pages matched.

Absence of a match in these searches is not proof of priority.

---

## A. Is the one-fee bound (`prop:onefee`) a corollary of known duality-gap bounds?

### Sources

**A1. Udell, M. and S. Boyd (2016). "Bounding duality gap for separable problems with linear constraints." *Computational Optimization and Applications* 64(2), 355–378. DOI 10.1007/s10589-015-9819-4.** Crossref-verified. Full text read (arXiv:1410.4158v2, §§1–3). Problem (P): minimize Σᵢ fᵢ(xᵢ), xᵢ ∈ Sᵢ compact, subject to Ax ≤ b, Gx = h. Constraints that touch a single block are folded into Sᵢ; the remaining m "complicating" constraints each involve at least two blocks. m̃ ≤ m counts constraints that can be simultaneously active. ρ(f) = sup(f − f̂) (f̂ the convex envelope). **Theorem 1:** some solution x* of the convexified problem satisfies f(x*) ≤ p̂ + Σ_{i=1}^{min(m̃,n)} ρ(fᵢ) (largest ρ first). The paper states that Theorem 1 can be derived from Shapley–Folkman, and that Aubin–Ekeland's bound is p* − d* ≤ min(m+1, n)·ρ(f₁) (§3).

**A2. Aubin, J.-P. and I. Ekeland (1976). "Estimates of the duality gap in nonconvex optimization." *Mathematics of Operations Research* 1(3), 225–245. DOI 10.1287/moor.1.3.225.** Crossref-verified. Not read; the bound min(m+1, n)·ρ_max is quoted from A1 §3.

**A3. Bertsekas, D., G. Lauer, N. Sandell and T. Posbergh (1983). "Optimal short-term scheduling of large-scale power systems." *IEEE Transactions on Automatic Control* 28(1), 1–11. DOI 10.1109/TAC.1983.1103136.** Crossref-verified. Not read (IEEE). A1 §3 states that it applies Shapley–Folkman to unit commitment with univariate objective terms. The well-known form is a gap of at most (number of coupling constraints + 1) × the largest single-unit nonconvexity, so the relative gap vanishes as the number of units grows. I did not check the constant against the original.

**A4. Starr (1969)** and **Hreinsson et al. (2021)** are already cited in the paper (`starr1969`, `hreinsson2021`). Not re-read.

**A5. Chao, H.-p. (2019). "Incentives for efficient pricing mechanism in markets with non-convexities." *Journal of Regulatory Economics* 56(1), 33–58. DOI 10.1007/s11149-019-09385-w.** Crossref-verified. **Abstract only.** Springer redirected to a login. The PJM-hosted report URL returned an HTML page instead of a PDF, and I did not retry. From the RePEc abstract, the paper separates a nonconvex allocation problem from a convexified pricing problem (Lagrangian, convex hull and integer relaxation). Quasi-equilibrium pricing becomes incentive compatible *in the limit*, and side payments become negligible relative to total surplus as the market grows. That is a Starr-type asymptotic statement. **I found no "uplift at most one unit's fixed cost" theorem attributed to Chao in what I could access.** Do not cite Chao for such a bound.

**A6. Berger, A., V. Bonifaci, F. Grandoni and G. Schäfer (2011; online 2009). "Budgeted matching and budgeted matroid intersection via the gasoline puzzle." *Mathematical Programming* 128(1–2), 355–372. DOI 10.1007/s10107-009-0307-4.** Crossref-verified. Full text read (author copy, CWI repository ir.cwi.nl/pub/14736, §§1–3). They dualize the single budget constraint of a maximum-weight matching. Two Lagrangian-optimal matchings M₁, M₂ with c(M₁) ≤ B ≤ c(M₂) are moved along the optimal face until they are *adjacent* in the matching polytope. "For matchings it is known that two solutions are adjacent in the matching polytope if and only if their symmetric difference is an alternating cycle or path" (§1). Lemma 4 gives a feasible matching of weight ≥ opt − 2w_max. The device goes back to **Ravi and Goemans (1996)**, "The constrained minimum spanning tree problem," SWAT 1996, LNCS 1097, 66–75, DOI 10.1007/3-540-61422-2_121 (Crossref-verified; not read).

**A7. Chvátal, V. (1975). "On certain polytopes associated with graphs." *Journal of Combinatorial Theory, Series B* 18(2), 138–154. DOI 10.1016/0095-8956(75)90041-6.** Crossref-verified. Not read. Commonly cited for adjacency on the matching polytope. The adjacency statement used below is quoted from A6 rather than verified in Chvátal.

**A8. Baum, S. and L. E. Trotter Jr. (1981). "Integer rounding for polymatroid and branching optimization problems." *SIAM Journal on Algebraic Discrete Methods* 2(4), 416–425. DOI 10.1137/0602044.** Crossref-verified. Not read. This is the integer round-up property literature (gap of LP vs. IP strictly below one unit after rounding). It is an analogy only: our rounding is round-*down* of a pair count on nested feasible sets, not a covering problem.

**A9. Bi, Y. and A. Tang, "Refined Shapley–Folkman lemma and its application in duality gap estimation," arXiv:1610.05416.** Search hit only; not read. It refines the nonconvexity measure. It does not change the analysis below.

### What these results give for our problem (my derivation, to be checked by a referee)

Write the planner's problem as two "agents" coupled by T = 2 equalities (early load E, late load L): the fleet with value function c(E, L) = min{fN : a whole-fleet plan with loads (E, L) and N buses} (+∞ if infeasible), and the supplier with convex G. The paper's CH (eq. `eq:DCH`) convexifies **complete fleet plans**, i.e. it replaces c by its envelope ĉ. It does not convexify per bus.

1. **Fleet as a single agent (the paper's hull).** Udell–Boyd / Aubin–Ekeland with n = 2 blocks and ρ(G) = 0 give D − CH ≤ ρ(c). This is also the trivial one-line bound: evaluate c at the hull optimum E*. So **`prop:onefee` is exactly the statement ρ(c) < f**, together with the observation that ρ(c) does not depend on G (hard limits included, because they only restrict where E* can lie). Shapley–Folkman adds nothing here, since there is one nonconvex block.
2. **Per-service or per-bus blocks with the matching as coupling.** Take each A service as a block choosing a partner or none. Each B service gives an equality "served exactly once", so there are m = n_B + 2 complicating constraints. Each block's ρ is of order f (a binary pairing choice saves f). Udell–Boyd then gives a gap ≤ Σ of the (n_B + 2) largest ρᵢ ≈ (n_B + 2)·f, and Aubin–Ekeland ≈ (n_B + 3)·f. Both **grow with fleet size**. A per-bus formulation does no better, because the matching constraints remain coupling constraints. **So `prop:onefee` is not implied by Shapley–Folkman-type bounds. It is tighter by a factor of order n_B, and it is a different kind of argument.**
3. **Where the fleet-size independence comes from.** It does not come from aggregation. It comes from the integral structure of bipartite matching:
   - (a) **The paper's route.** r_m is convex in m (min-cost flow value is convex in the flow amount; classical, Murota 2003, see B2). So the breakpoints (ℓ_m, fN_m) are in convex position, the envelope interpolates *adjacent* cardinalities, and the pointwise gap c − ĉ is below f.
   - (b) **An equivalent known route.** The lossless charge-only CH equals the LP over the bipartite matching polytope with a side constraint E ≥ Σ_e w_e x_e, where w_e = (a_i + b_j − B)_+. The matching polytope is integral, and the image of a polytope under a linear map is the hull of its vertex images. The constraint S₀ − N_m B ≤ E is a cardinality upper bound that only tightens with m. Fix E = E*. The LP optimum then lies on an edge of the matching polytope between two *adjacent* matchings (the Lagrangian/adjacency device of A6 and Ravi–Goemans). Adjacent matchings differ by one alternating path or cycle, so their cardinalities differ by at most one. The budget-feasible endpoint loses at most one fee f. With uniform per-pair savings f this reproduces `prop:onefee` for the matching case, **including general (non-complete) compatibility graphs**.
   - Neither route needs anything beyond classical combinatorial optimization.
4. **Hypothesis doing the work.** The discrete convexity of ℓ_m. Without it the bound fails. Example: ℓ₀ = 0, ℓ₁ = ℓ₂ = … = ℓ_{k−1} = 10 − ε, ℓ_k = 10. A mixture of counts 0 and k at E ≈ 5 has mean count k/2, but only count 0 is feasible, so the gap is ≈ (k/2)·f. In the matching application, convexity is automatic, which is why the bound is fleet-size independent there. The "common upper endpoint U" assumption is also used: the hull at count t must not have a smaller upper endpoint than ⌊t⌋.

**Verdict for A.** Not a corollary of Shapley–Folkman / Aubin–Ekeland / Bertsekas / Udell–Boyd. Those give O(n_B)·f here, or the trivial ρ(c) bound once the fleet is treated as one agent. The bound is, however, a short consequence of classical matching-polytope facts: convexity of min-cost flow in the flow value, or adjacency of matchings under one side constraint (Berger et al. 2011; Ravi–Goemans 1996). It should be presented as such, not as a result about grid costs. "Any convex grid cost including hard limits" is inherited automatically from ρ(c) and is not an extra contribution.

---

## B. Is the projection theorem (`thm:projection`) a known fact in disguise?

### Sources

**B1. Dell'Amico, M. and S. Martello (1997). "The k-cardinality assignment problem." *Discrete Applied Mathematics* 76(1–3), 103–121. DOI 10.1016/S0166-218X(97)00120-0.** Crossref-verified. The other DOI suffix circulating, ...00120-2, does not resolve. Abstract only. Assign k rows to k columns at minimum cost. Solvable as a 2-matroid intersection or by min-cost flow/shortest augmenting paths. This is exactly the computation of r_m on a general compatibility graph and should be cited where the paper says "r_m is a minimum-cost matching of cardinality m".

**B2. Murota, K. (2003). *Discrete Convex Analysis*. SIAM. DOI 10.1137/1.9780898718508.** Crossref-verified. Not re-read for this note. The value of a min-cost flow as a function of the supply/flow vector is M♮-convex (the book's network-flow chapter). The scalar case, convexity of the min-cost k-matching value in k, is the textbook successive-shortest-path fact. Appropriate citation for "r_m is nondecreasing and discretely convex" (appendix §"Monotonicity, convexity"), which the paper currently proves without citation.

**B3. Burkard, R. E., B. Klinz and R. Rudolf (1996). "Perspectives of Monge properties in optimization." *Discrete Applied Mathematics* 70(2), 95–161. DOI 10.1016/0166-218X(95)00103-X.** Crossref-verified. Not read. The cost matrix h(a_i + b_j) with h convex is an inverse-Monge array once both batches are sorted, so the anti-diagonal (opposite-order) assignment is optimal. Hoffman (1963) is the classical origin. The paper's "classical exchange argument" for the sorted r_m formula should cite this survey.

**B4. Mukhi, K., G. Loho and A. Abate (2026). "Exact Characterization of Aggregate Flexibility via Generalized Polymatroids." *IEEE Transactions on Smart Grid* 17(3), 2131–2142. DOI 10.1109/TSG.2026.3659513.** Crossref-verified (already in the bib as `mukhiLohoAbate2025exact`). Also **Mukhi and Abate (2023), CDC 2023, 6582–6587, DOI 10.1109/CDC49753.2023.10383521** (the published version of the arXiv preprint already cited as `mukhiAbate2023exact`; Crossref-verified). And **Mukhi and Abate (2025), "Polymatroidal Representations of Aggregate EV Flexibility Considering Network Constraints," ISGT Europe 2025, DOI 10.1109/ISGTEUROPE64741.2025.11305672** (Crossref-verified; not read). All take the EV population as given.

**B5. Panda, N. K. and S. H. Tindemans (2024). "Efficient quantification and representation of aggregate flexibility in Electric Vehicles." *Electric Power Systems Research* 235, 110811. DOI 10.1016/j.epsr.2024.110811.** Crossref-verified; abstract read (arXiv:2310.02729v2). A representation with 2T parameters for a fixed fleet within a request window, independent of fleet size. The population is fixed; there is no task assignment.

**B6. Nayyar, A., M. Negrete-Pincetic, K. Poolla and P. Varaiya (2016). "Duration-Differentiated Energy Services With a Continuum of Loads." *IEEE Transactions on Control of Network Systems* 3(2), 182–191. DOI 10.1109/TCNS.2015.2428491.** Crossref-verified; not read (known for majorization-type feasibility of duration-differentiated loads). Also **Negrete-Pincetic et al. (2018), "Rate-Constrained Energy Services in Electricity," *IEEE TSG* 9(4), 2894–2907, DOI 10.1109/TSG.2016.2623275** (Crossref-verified; not read). These are the majorization characterizations of homogeneous flexible-load fleets with per-device rate limits. Again the population is fixed.

**B7. Al Taha / Vincent / Bitar** (already cited, `altaha2024flexibility`, `altahaBitar2024lossy`). Fixed population; the lossy single-device reformulation is relevant to the loss part of `thm:projection`.

### Assessment

- **Fixed matching ⇒ aggregate.** In the lossless charge-only case each bus's early gain lies in an interval [max(lo_v, 0), hi_v]. The fleet aggregate is the Minkowski sum of intervals: [R(M), P] with R(M) the sum of positive lower endpoints. This is a one-dimensional g-polymatroid (trivially), so **for a fixed matching the lossless charge-only statement is a special case of Mukhi–Loho–Abate / Panda–Tindemans aggregation**. Once losses, exports and a *gross* connector budget C + X ≤ K enter, the per-bus set in (C, X) is no longer an interval. The g-polymatroid theorems as stated (lossless power/energy bounds) do not cover it. The paper's `rem:netinterval` correctly identifies what a net-interval aggregate loses. That loss-and-gross-budget part is the genuinely non-off-the-shelf piece. I found no paper giving the two-window lossy, bidirectional, gross-budget aggregate.
- **Population as a decision, with one assignment dominating.** I searched for aggregate-flexibility or EV-fleet results where the vehicle-to-task assignment is a decision variable and one assignment's flexibility set *contains* all others (set containment, not cost dominance). Queries: "vehicle-to-trip assignment maximizes aggregate charging flexibility…", "electric bus pairing morning peak afternoon peak blocks midday depot charging assignment matching", plus the g-polymatroid and majorization literature above. **I found none.** The closest are the E-VSP models that choose assignments and charging jointly for given prices (topic C) and cost-aware disaggregation (Müller et al., already cited). These optimize under one price vector and do not assert set containment.
- **Is containment "obvious once stated"?** Partly. Given (i) invariance of Σlo, Σhi and fleet cost at fixed cardinality, and (ii) that only R(M) enters, containment follows from monotonicity in one scalar. A referee in combinatorial optimization may call the lossless charge-only version an observation plus a min-cost k-cardinality matching (B1) with Monge structure (B3). The defensible novelty is (a) the exact set statement including losses, V2G exports, a shared gross-budget connector and serial realizability, and (b) the consequence for support analysis.

---

## C. Sequential versus integrated electric-bus planning

*Pending — delegated web search in progress; filled in below when complete.*

---

## D. Coupled power–transport price-loop literature the paper omits

The paper's Section 2 ("Price adjustment") cites only Ma et al. (2016), Jaggi (2013) and ergodic-recovery papers. The following are verified (Crossref, 12 Nov 2026). They are summarized from the 2 November OPF review (`opf-loop-20261102/ref/opf/LIT_REVIEW.md`), with my own re-check where stated.

- **Alizadeh, Wai, Chowdhury, Goldsmith, Scaglione, Javidi (2017).** *IEEE TCNS* 4(4), 863–875, DOI 10.1109/TCNS.2016.2590259. **Re-checked today on arXiv:1511.03611 (HTML).** §V-A "Greedy pricing": the power operator prices assuming charging "will happen exactly as in the last period", and prices "could oscillate indefinitely". §VI, Table II (2.26×10⁴ EVs per epoch): Winters charging alternates 7.227 ↔ 15.87 MWh at $57.38 ↔ $54.50; objective $30,364.61 / $30,333.06 vs social optimum $30,332.55. **This is a published 2-cycle of myopic marginal pricing in a coupled system whose aggregate operating set is convex.** It anticipates `thm:iteration`(b)'s qualitative message ("can cycle even when a supporting price exists").
- **Wei, Wu, Wang, Mei (2018).** *IEEE TSG* 9(6), 6764–6779, DOI 10.1109/TSG.2017.2723016. Price → traffic → charging → OPF fixed-point loop; existence by Brouwer under continuity (Prop. 3); local stability condition Eq. (44); convergence local and initialization-dependent (§IV-B). Per the OPF review, full text was read from a user-supplied copy.
- **Roozbehani, Dahleh, Mitter (2012).** *IEEE TPWRS* 27(4), 1926–1940, DOI 10.1109/TPWRS.2012.2195037. Closed-loop real-time pricing can be unstable; a stability condition uses relative price elasticity < 1 (Cor. 3).
- **Li, Wu, Oren (2014).** *IEEE TPWRS* 29(1), 203–211, DOI 10.1109/TPWRS.2013.2278952. DLMP decentralizes divisible EV charging via KKT. This is existence/implementation at a clearing price, not convergence of a naive loop.
- **Gan, Topcu, Low (2013).** *IEEE TPWRS* 28(2), 940–951, DOI 10.1109/TPWRS.2012.2210288. A decentralized valley-filling protocol with a proximal (squared-deviation) penalty converges for step γ < 1/(Nβ) (Thms. 3–4). The proximal term is the standard remedy for the oscillation an unregularized best response produces.
- **Gong, De Paola, Angeli, Strbac (2019).** *IEEE TCNS* 6(3), 1097–1110, DOI 10.1109/TCNS.2019.2920587. Iterative LMP-based coordination with one-sided marginal prices at kinks; set convergence to Wardrop equilibria.

The proposed paragraph is in `related_work_patch.tex`. It concedes that (i) myopic price-response cycling (Alizadeh et al.) and (ii) damped/proximal remedies (Gan et al.; Ma et al.) are known. It distinguishes the paper's content as the discrete, whole-fleet response and the classification of which cycles coexist with a support gap.

---

## E. German tariff mechanisms

See `TARIFF_FACTS.md`.

---

## F. Zhou, An and Schmöcker (2025)

**Zhou, X., K. An and J.-D. Schmöcker (2025). "Optimization of charging and discharging schedules for battery electric buses under the V2G environment." *Transportmetrica B: Transport Dynamics* 13(1), 2506689. DOI 10.1080/21680566.2025.2506689.** Crossref-verified. **Full text read: the accepted manuscript (41 pp.) in the Kyoto University Research Information Repository, hdl:2433/300766.** The publisher embargo ended 26 May 2026 and the record states the file is public under T&F self-archiving terms; it was retrieved through the repository's normal public file link. The publisher page (tandfonline.com) returned HTTP 403 and was not retried.

- **Model (§2).** Multi-depot connection-network MILP with *binary trip-to-trip assignment* x_kij, fleet size Σz_k at a fixed cost per bus, and charge/discharge between consecutive trips at the nearest depot (y/w/v arcs). Partial charging. Per-depot charger count and power limits (17)–(18). It is therefore a **joint** fleet-size + trip-assignment + (dis)charging model, not a fixed-duty charging model. Overnight charging, 23:30–05:30, is assumed full and outside the optimization (§4.1).
- **Data (§4, Tables 3–4).** Jiading District, Shanghai: 5 routes, 2 depots (1,200 and 1,800 kW), 418 trips; 100 kWh battery, SOC 20–100%; 60 kW chargers (1 kWh/min); fixed cost c_f = 171.2 ¥/bus-day; deadhead 0.5 ¥/min; degradation 0.1 ¥/kWh. Shanghai 2023 commercial TOU: **peak 10:00–15:00 and 18:00–21:00, 1.2893 ¥/kWh; normal 0.8731; off-peak 23:00–07:00, 0.4570**. Discharge revenue = charging TOU price.
- **Results.** ALNS-SA within 0.7% of Gurobi on 50 trips (Table 5); Gurobi finds no feasible solution for 200 and 418 trips in 6 h. Cross-line vs single-line (Table 6): 36 vs 39 buses, total 8,758.3 vs 10,538.2 ¥/day. **The abstract's "8.5% lower" does not match Table 6 (16.9%) or Table 7 (fixed fleet 39: 8,861.4 vs 10,537.9, i.e. 15.9%).** Quote table values, not the abstract. Partial vs full vs fixed-period charging (Table 8): 36/40/49 buses, 8,758.3/9,083.8/10,113.5 ¥.
- **Relation to our paper.**
  - (i) No duty-first-vs-joint comparison and no price-independence claim; the comparison is operating mode (cross- vs single-line) and charging policy.
  - (ii) The midday window is the *peak* TOU block in Shanghai, so midday charging is penalized relative to overnight: spread 1.2893 − 0.4570 = 0.83 ¥/kWh.
  - (iii) A rough check against `prop:anatomy`: f = 171.2 ¥ and forced-charging increments of at most one battery's usable energy (80 kWh) give a critical spread f/η ≥ 171.2/80 ≈ 2.1 ¥/kWh, about 2.6 times the Shanghai peak–off-peak spread. This is a back-of-envelope transfer; Zhou's instances are not two-batch.
  - Suggested wording for the paper: "Zhou et al. jointly choose fleet size, trip chains and V2G charging under a three-level TOU tariff (418 trips, two depots) and report that cross-line operation lowers daily cost by about 17% relative to single-line operation (their Table 6)."

---

## G. Other "this is known" risks

1. **One-agent duality-gap bound (A).** A referee will note that D − CH ≤ ρ(fleet value function) is trivial and that ρ < f follows from convexity of min-cost flow in the flow value (B2) or from budgeted-matching adjacency (A6). **Highest risk for `prop:onefee`.**
2. **Sorted pairing / Monge (B3) and k-cardinality assignment (B1).** Currently uncited; cite them.
3. **Myopic price cycling in coupled systems (D).** Alizadeh et al. 2017 Table II is a direct published 2-cycle. `thm:iteration`(b) must cite it.
4. **Support = integral hull optimum.** Already conceded (Hümbs, Martin and Schewe 2022, `huembs2022complete`; Gribik–Hogan–Pope; Hua–Baldick).
5. **Convex hull pricing for a single nonconvex demand participant.** Madani et al. (arXiv:1804.00048) treat indivisible multi-hour demand bids (per OPF review). The fleet is a structured instance; cite as context.
6. **Recent depot-charging work (2026).** Widmer, Pinter, Moradi and Onder, "Optimal Electric Bus Depot Charging: Cost Savings, Grid Limits, and Robustness Trade-Offs," arXiv:2607.29304 (31 July 2026; abstract only). Four Swiss depots, 7–35 buses, schedules apparently given; >40% grid-capacity reduction and >50% cost reduction vs charge-on-arrival for small depots. Relevant as evidence that the *charging* decision carries most of the value once duties are fixed. Bibliographic status: preprint, not peer reviewed.
7. **Frank–Wolfe / ergodic recovery (`thm:iteration`).** Already conceded; nothing new found.
