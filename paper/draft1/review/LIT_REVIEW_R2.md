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

**A6. Berger, A., V. Bonifaci, F. Grandoni and G. Schäfer (2011; online 2009). "Budgeted matching and budgeted matroid intersection via the gasoline puzzle." *Mathematical Programming* 128(1–2), 355–372. DOI 10.1007/s10107-009-0307-4.** Crossref-verified. Full text read (author copy, CWI repository ir.cwi.nl/pub/14736, §§1–3). They dualize the single budget constraint of a maximum-weight matching. Two Lagrangian-optimal matchings M₁, M₂ with c(M₁) ≤ B ≤ c(M₂) are moved along the optimal face until they are *adjacent* in the matching polytope. "For matchings it is known that two solutions are adjacent in the matching polytope if and only if their symmetric difference is an alternating cycle or path" (§1). Lemma 4 gives a feasible matching of weight ≥ opt − 2w_max. The device goes back to **Ravi and Goemans (1996)**, "The constrained minimum spanning tree problem," SWAT 1996, LNCS 1097, 66–75, DOI 10.1007/3-540-61422-2_121 (Crossref-verified; the LNCS volume number 1097 is not in the Crossref record and is unverified; not read).

**A7. Chvátal, V. (1975). "On certain polytopes associated with graphs." *Journal of Combinatorial Theory, Series B* 18(2), 138–154. DOI 10.1016/0095-8956(75)90041-6.** Crossref-verified. Not read. Commonly cited for adjacency on the matching polytope. The adjacency statement used below is quoted from A6 rather than verified in Chvátal.

**A8. Baum, S. and L. E. Trotter Jr. (1981). "Integer rounding for polymatroid and branching optimization problems." *SIAM Journal on Algebraic Discrete Methods* 2(4), 416–425. DOI 10.1137/0602044.** Crossref-verified. Not read. This is the integer round-up property literature (gap of LP vs. IP strictly below one unit after rounding). It is an analogy only: our rounding is round-*down* of a pair count on nested feasible sets, not a covering problem.

**A9. Bi, Y. and A. Tang, "Refined Shapley–Folkman lemma and its application in duality gap estimation," arXiv:1610.05416.** Search hit only; not read. It refines the nonconvexity measure. It does not change the analysis below.

### What these results give for our problem (my derivation, to be checked by a referee)

Write the planner's problem as two "agents" coupled by T = 2 equalities (early load E, late load L): the fleet with value function c(E, L) = min{fN : a whole-fleet plan with loads (E, L) and N buses} (+∞ if infeasible), and the supplier with convex G. The paper's CH (eq. `eq:DCH`) convexifies **complete fleet plans**, i.e. it replaces c by its envelope ĉ. It does not convexify per bus.

1. **Fleet as a single agent (the paper's hull).** Udell–Boyd / Aubin–Ekeland with n = 2 blocks and ρ(G) = 0 give D − CH ≤ ρ(c). This is the trivial one-line bound: evaluate c at the hull optimum E*. Note that ρ(c) = f exactly in the lossless charge-only case. On (ℓ_{m−1}, ℓ_m), c = fN_{m−1} while ĉ falls linearly to fN_m, so the difference tends to f but never reaches it. The paper's strict inequality D − CH < f therefore comes from the pointwise difference at the (attained) hull optimum, not from ρ(c) < f.
2. **Per-service blocks with the matching as coupling.** Each A service is a block; each B service gives a coupling equality, so there are about n_B + 2 complicating constraints. The bound is then of order (n_B + 2)·f. This blocking is uninformative, but it is not the only one.
3. **Per-marginal-pair blocks: `prop:onefee` IS a Udell–Boyd corollary (non-strict form).**
   - Use the paper's own layers ℓ_m. Let η_m = ℓ_m − ℓ_{m−1}, nondecreasing for m > m₀ by the paper's discrete convexity, with the first increment clipped as in the appendix.
   - Introduce one block per marginal pair: x_m ∈ [0, η_m], with f_m(x_m) = −f if x_m = η_m and 0 otherwise. f_m is lower semicontinuous on a compact domain.
   - Add one convex block G(E) with dom G ⊆ [Lo, U]; hard limits enter as a domain restriction. Impose a single coupling constraint ℓ₀ + Σ_m x_m ≤ E.
   - **Physical value.** Because η_m is nondecreasing, completing any k blocks needs at least Σ_{m≤k} η_m = ℓ_k − ℓ₀ energy. So the block problem's value equals D, with fee measured relative to N₀.
   - **Hull value.** Each envelope is f̂_m(x) = −f·x/η_m. The summed envelopes under the single coupling constraint are a fractional knapsack, which fills blocks in order of decreasing f/η_m, i.e. increasing m. This reproduces the paper's lower hull frontier, so the convexified value equals CH.
   - **Bound.** ρ(f_m) = f, m̃ = 1. Udell–Boyd Theorem 1 then gives **D − CH ≤ f**, independent of fleet size and of G. Equivalently, the LP relaxation of a knapsack with equal item profits loses at most one item's profit.
   - So the non-strict one-fee bound **is** a direct corollary of the Shapley–Folkman family, once the fleet is written by marginal pairs. The only model-specific input is the discrete convexity of ℓ_m, which is itself classical (min-cost flow convexity, B2).
   - The strict "< f" and the refinement f(t − ⌊t⌋) are one more line.
   - Alternative classical route for matchings: the LP over the bipartite matching polytope with the side constraint E ≥ Σ_e w_e x_e, where w_e = (a_i + b_j − B)_+. Its optimum lies between two adjacent matchings, whose cardinalities differ by at most one (adjacency device of A6 and Ravi–Goemans).
4. **Hypothesis doing the work.** The discrete convexity of ℓ_m. Without it, the bound fails. Example: ℓ₀ = 0, ℓ₁ = … = ℓ_{k−1} = 10 − ε, ℓ_k = 10. A mixture of counts 0 and k at E ≈ 5 has mean count k/2, but only count 0 is feasible, so the gap is ≈ (k/2)·f. In the per-marginal-pair blocking this is exactly where the "physical value = D" step breaks: with non-monotone η_m, the cheapest blocks are not the first ones. The common upper endpoint U is also used.

**Verdict for A. Known, up to presentation.** The non-strict bound D − CH ≤ f follows from Udell–Boyd Theorem 1 (equivalently Aubin–Ekeland/Shapley–Folkman, or the fractional-knapsack LP gap) applied to a per-marginal-pair blocking with one coupling constraint. Fleet-size independence and G-independence are automatic in that blocking. What remains model-specific is (i) the discrete convexity of ℓ_m, which is classical for min-cost matching, and (ii) the strict version and the f(t − ⌊t⌋) refinement, which are trivial. The paper should present `prop:onefee` as a corollary or remark and cite Udell–Boyd and Aubin–Ekeland for it.

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

A delegated search covered 33 queries (listed in the Search record at the end of this file). All DOIs below are Crossref-verified by me. The figures for Nath et al. and Abdelwahed et al. were re-checked by me: the Nath abstract on arXiv, and the Abdelwahed EUR repository PDF (§5.3; Table 4 row "OPT 796.30 / FIFS 953.33"). Other numbers are as read by the delegated search from the full texts noted.

**The literature uses three different baselines. Only group (i) measures what the paper's duty-first test measures.**
- (i) Duties or assignments fixed first, then charging optimized, compared with joint optimization.
- (ii) Optimized vs. naive charging on a fixed schedule. This is the value of the second stage, not the integration loss.
- (iii) Integrated optimization vs. rule heuristics.

### (i) Sequential vs. integrated

**C1. Nath, R. B., T. Rambha and M. Schiffer (2024).** *Transportation Research Part C* 167, 104839, DOI 10.1016/j.trc.2024.104839. Already in the paper as `nath2024joint`.
- Access: full text read (arXiv:2403.09763) by the delegated search; I re-checked the abstract.
- Sequential = charger location plus E-VSP first, then charge scheduling with rotations fixed. Joint = charge scheduling inside an iterated local search.
- Instances: 14 GTFS networks with 432–3,337 trips and 20–195 buses.
- **Joint vs. sequential: operating cost −14.1%; total cost −4.1% on average** (abstract), per network 0.13% (SCMTD, 1,830 trips) to 7.7% (Cornwall, Intercity) (Table 9).
- Total cost includes charger-siting effects.
- Prices: PG&E 2023 TOU (peak 4–9 pm roughly 3× off-peak) plus contracted capacity of 654 $/kW. The delegated agent reports the arXiv table prints the tariff in scaled units; per-kWh levels are its inference, unverified.
- **This is the closest empirical comparator to the paper's §5 hourly test.**

**C2. Klein, P. S. and M. Schiffer (2023).** "Electric Vehicle Charge Scheduling with Flexible Service Operations." *Transportation Science*, DOI 10.1287/trsc.2022.0272. Volume and pages are not returned by Crossref; the delegated search reports 57(6), 1605–1626, unverified.
- Access: full text (arXiv:2201.03972v2) by the delegated search.
- Logistics vans with a fixed vehicle-to-operation assignment. "Integration" means flexible departure times.
- Prices: ENTSO-E day-ahead.
- Savings of 2.5% (1 h of flexibility) rising to about 4.6–5.4% (plateau). Savings scale with price variance: 1.1% / 1.95% / 3.7% for low / medium / high-variance TOU.

**C3. Wang, Jin, Ibarra-Rojas, Xu, Cao (2026).** "A branch-and-price algorithm for integrated optimization on vehicle and crew scheduling of electric bus system." *Transportation Research Part B* 206, 103430, DOI 10.1016/j.trb.2026.103430.
- Access: **not accessible** (ScienceDirect 403; PolyU repository embargoed or timing out).
- A search snippet says sequential vehicle–crew then charging scheduling "did not affect global optimality". If true, this supports the paper's direction. **Unverified; do not cite for that claim without reading.**

**C4. Teng, Chen, Fan (2020).** *Journal of Transportation Engineering, Part A* 146(2), 04019073, DOI 10.1061/JTEPBS.0000306. Not accessible (ASCE 403). A circulating "4.37% vs sequential" figure is unverified.

**C5. Sassi, O. and A. Oulamara (2017).** "Electric vehicle scheduling and optimal charging problem: complexity, exact and heuristic approaches." *International Journal of Production Research* 55(2), 519–535, DOI 10.1080/00207543.2016.1192695.
- Access: abstract plus ROADEF 2014 abstract.
- The joint problem is NP-hard. Their heuristic assigns tours first and then schedules charging as a min-cost flow.
- This is a structural analogue of "assign, then charge", **not** a separation result.

### (ii) Charging-only value on a fixed schedule

**C6. Abdelwahed, van den Berg, Brandt, Collins, Ketter (2020).** *Transportation Science* 54(6), 1601–1615, DOI 10.1287/trsc.2020.0982.
- Access: full text (EUR repository).
- Rotterdam: 7 lines, 47 buses, opportunity fast charging, hourly day-ahead prices.
- Optimal charging costs €796.30 vs €953.33 for FIFS and LCHP heuristics, **−16.5%** (re-verified, §5.3).

**C7. He, Y., Z. Liu and Z. Song (2020).** *Transportation Research Part E* 142, 102056, DOI 10.1016/j.tre.2020.102056.
- Access: full text (OSTI accepted manuscript) by the delegated search.
- Salt Lake City: 19 buses, with a large case of 170 buses. Rocky Mountain Power tariff.
- Demand charges: 12.765 $/kW without TOU; 15.40 $/kW on-peak (May–Sep) with TOU.
- Optimized vs. uncontrolled: −47.8% (no TOU), −66 to −78% (TOU); large network −34 to −66%.
- Savings come mainly from demand charges.

**C8. Jahic, Eskander, Schulz (2019).** *Applied Sciences* 9(9), 1748, DOI 10.3390/app9091748. Open access, read by the delegated search. Hamburg depot for 240 buses: peak 7.5 → 5.47 MW in winter (−27%) and 5.7 → 3.27 MW in summer (−43%). No prices.

**C9.** Lacombe et al. (arXiv:2309.00523) and Caustur et al. (arXiv:2509.05940) are preprints with fixed schedules: 11–20% and 5% (demand-charge component). Not Crossref-checked; context only.

### (iii) Integrated vs. heuristics; TOU-aware vs. TOU-blind

**C10. Wu et al. (2022)**, `wu2022grid`. Guangzhou: 379 trips, 5 depots. The integrated model costs $10,866 vs. $13,884 (FIFO) and $14,975 (TOU-aware FIFO). The gain comes from fleet size (28 vs. 39/43 buses). **Charging cost is higher under integration.**

**C11. Zhang, Wang, Gu, Han, Chung, Qu (2024).** "On the role of time-of-use electricity price in charge scheduling for electric bus fleets." *Computer-Aided Civil and Infrastructure Engineering* 39(8), 1218–1237, DOI 10.1111/mice.13134. Abstract only (Wiley 403). Including TOU "can reduce costs by up to 22%". The baseline is unverified.

**C12. Lu, Xing, Li (2025).** *Transportation Research Part E* 196, 104021, DOI 10.1016/j.tre.2025.104021. Abstract only. TOU-aware E-VSP by branch-and-price; no numbers in the abstract.

### Context only (no price-integration numbers)

All abstract-only unless noted; DOIs verified.
- van Kooten Niekerk, van den Akker, Hoogeveen (2017), "Scheduling electric vehicles," *Public Transport* 9(1–2), 155–176, DOI 10.1007/s12469-017-0164-0. **Note: Public Transport, not TR-D.** Model 2 has time-varying prices.
- Perumal, Lusby, Larsen (2022), *EJOR* 301(2), 395–413, DOI 10.1016/j.ejor.2021.10.058. The abstract calls integrated planning crucial; the body was not accessible.
- Li (2014), *Transportation Science* 48(4), 521–539, DOI 10.1287/trsc.2013.0468.
- Wen et al. (2016), *Computers & OR* 76, 73–83, DOI 10.1016/j.cor.2016.06.013.
- Rogge et al. (2018), *Applied Energy* 211, 282–295, DOI 10.1016/j.apenergy.2017.11.051.
- Dirks, Schiffer, Walther (2022), *TR-C* 139, 103628, DOI 10.1016/j.trc.2022.103628.
- Olsen and Kliewer (2020), *Logistics Research* 13:4. Open access was opened by the delegated search, but **the DOI 10.23773/2020_4 does not resolve in Crossref**; cite by URL only.
- Gkiotsalitis, Iliopoulou, Kepaptsoglou (2023), *EJOR* 306(1), 189–206 (as cited in Zhou et al. 2025; DOI not checked).

**Ambiguous / not identified.** "Zhang et al. 2021", "Gkiotsalitis" (several papers; the TR-C 2025 paper by Rizopoulos and Gkiotsalitis is unverified), "Janovec" (no price paper found).

### Synthesis for the paper's "duty-first" claim

- **Theory.** No theoretical separation result was found: no conditions under which duties-then-charging is optimal under TOU, dynamic prices or demand charges, and no bound on the integration loss. The paper's projection theorem appears to be the first such statement, for a narrow class.
- **True sequential-vs-integrated evidence.**
  - Nath et al.: 0.13–7.7%, mean 4.1%, of total cost on 432–3,337-trip networks, including charger siting.
  - Klein and Schiffer: 1–5% in logistics.
  - The paper's 64-instance test (≤ 2.04% upper bound, mean regret ~8 SEK) is numerically within that range. The comparison is loose: 8–12-trip synthetic instances vs. 432–3,337-trip real networks whose gaps include charger siting. It is not evidence that the gaps agree.
- **Larger figures measure something else.**
  - Charging-only optimization on fixed duties: 14–78% (Abdelwahed; He et al.).
  - Fleet-size reduction vs. FIFO rules: Wu et al.
  - These support the paper's design point that the second stage, charging, carries most of the value once duties are fixed.
- **Price assumptions where integration matters.**
  - TOU peak around 2–3× off-peak (PG&E, Guangzhou, Shanghai).
  - Demand charges of 11–15 $/kW·month (US).
  - Day-ahead variance (ENTSO-E).
  - None is in the 0.5–3 EUR/kWh spread range the two-batch analysis says is needed for a support failure. This is consistent with the paper's §6.

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

**Zhou, X., K. An and J.-D. Schmöcker (2025). "Optimization of charging and discharging schedules for battery electric buses under the V2G environment." *Transportmetrica B: Transport Dynamics* 13(1), 2506689. DOI 10.1080/21680566.2025.2506689.** Crossref-verified. **Full text read: the accepted manuscript (41 pp.) in the Kyoto University Research Information Repository, hdl:2433/300766.** **Versions:** the published abstract says cross-line operation is 8.5% cheaper; the accepted manuscript's Tables 6 and 7 imply 16.9% and 15.9%. The published tables were not seen. The publisher embargo ended 26 May 2026 and the record states the file is public under T&F self-archiving terms; it was retrieved through the repository's normal public file link. The publisher page (tandfonline.com) returned HTTP 403 and was not retried.

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

---

## Search record

**Topic A** (my own searches, 12 Nov 2026):
- `Chao 2019 "Incentives for efficient pricing mechanism in markets with non-convexities" Journal of Regulatory Economics`
- `convex hull pricing uplift bounded by largest single unit fixed cost duality gap bound unit commitment theorem` (extended mode)
- `Hreinsson Scaglione Alizadeh Chen "Shapley-Folkman" dispatchable demand arXiv duality gap bound`
- `Berger Bonifaci Grandoni Schäfer "Budgeted matching and budgeted matroid intersection via the gasoline puzzle" arXiv`

The extended search found no "uplift ≤ one unit's fixed cost" theorem. Its hits were Hua–Baldick, Bragin et al. arXiv:2304.07990, a FERC Guan presentation and an Optimization Online convex-hull-pricing formulation paper; these were not opened beyond snippets.

Chao (2019): Springer redirected to a login; the PJM report URL returned HTML, not a PDF; a retry was declined by the session's permission system and not pursued. Only the RePEc abstract was read; its direct quote is "quasi-equilibrium pricing is dominant strategy incentive compatible in the limit".

**Topic B:**
- `Dell'Amico Martello "k-cardinality assignment problem" Discrete Applied Mathematics 1997`
- `vehicle-to-trip assignment maximizes aggregate charging flexibility electric fleet trip assignment flexibility envelope dominance` (extended)
- `electric bus pairing morning peak and afternoon peak blocks midday depot charging assignment matching problem` (extended)
- `Nayyar Negrete-Pincetic Poolla Varaiya "Duration-differentiated energy services with a continuum of loads" arXiv abstract`
- Crossref bibliographic queries for Panda–Tindemans, Nayyar et al., Mukhi–Loho–Abate

**Topic C** (delegated; verbatim list from the delegated report, abbreviated):
1. van Kooten Niekerk 2017 scheduling electric vehicles
2. sequential vs integrated vehicle scheduling charging TOU savings
3. Perumal Lusby Larsen review
4. Nath Rambha Schiffer
5. Olsen Kliewer
6. Li 2014
7. He Liu Song 2020 demand charge
8. Zhang Liu Wang 2021 TOU
9. Wu 2022 MDEVSP
10. "On the role of time-of-use electricity price…"
11. He et al. results
12. Abdelwahed
13. Rogge
14. Dirks
15. Jahic
16. Gkiotsalitis TOU
17. Sassi Oulamara
18. Rizopoulos Gkiotsalitis 2025
19. "sequential approach" compared integrated TOU percent
20. two-stage vs integrated branch-and-price 2023–2025
21. Klein Schiffer
22. Teng Chen Fan 4.37%
23. Wang et al. B&P vehicle–crew TR-B
24. Wen et al. ALNS
25. Perumal orbit.dtu.dk
26. Janovec Koháni TOU
27. Liu Ceder 2020
28. van Kooten Niekerk results/pdf
29. sequential decomposition theorem conditions / integration gap bound
30. "value of integration" / "cost of sequential planning"
31. fixed schedule charging min-cost-flow / TU / polynomial
32. hierarchical price-agnostic duties worst-case bound
33. fix blocks before prices known robust two-stage

Blocked (not bypassed): Springer (login redirect), ScienceDirect (403), Wiley (403), ASCE (403), Utrecht portal (403), HAL and dblp (bot check), core.ac.uk (403), PolyU repository (timeout/500).

**Topic E** (delegated, plus my re-checks):
- Opened: EAM 2026 price sheet and HLZF sheet (re-verified); BK4-13-739 (re-verified); BNetzA AgNes paper of 27 May 2026 (re-verified); e-regio 2026 sheet; N-ERGIE HLZF 2026; BK8-22/010-A; StromNEV §§16, 17, 19 and Anlage 4; EnWG §§14a, 41a, 118; AgNes draft GBK-25-01-1#3; SMARD API.
- Failed: BNetzA Orientierungspunkte_Industr_NetzE.pdf (404); AgNes procedure .html (404); Westnetz 2026 price sheet (403).
- Not found: e-regio HLZF publication; Bayernwerk, Netze BW, Stromnetz Berlin and SWM 2026 sheets and windows; BK6-22-300 original text; any adoption of the AgNes determination after 21 Sep 2026.

**Topic F:** Kyoto repository record and DSpace REST metadata, then the public bitstream; the tandfonline.com full-text page returned 403.

**Could not access (most consequential):**
1. Wang, Jin, Ibarra-Rojas, Xu, Cao (2026, TR-B 206, 103430). This is the most direct unread threat to claim 5.
2. Chao (2019) full text.
3. Perumal et al. (2022) body.
4. van Kooten Niekerk et al. (2017) full text.
5. Zhang et al. (2024) full text.
6. Teng et al. (2020).
7. Bertsekas et al. (1983) and Aubin–Ekeland (1976) originals; their constants are quoted via Udell–Boyd.
