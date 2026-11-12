# Novelty verdict, round 2 (12 November 2026)

One entry per claim: the closest prior statement found, a verdict, and what the paper should concede or cite. Sources and access status are in `LIT_REVIEW_R2.md`; new bib keys are in `references_r2.bib`. A verdict of "new" means only that this search found no prior statement. It is not a priority guarantee.

| # | Claim | Verdict |
|---|---|---|
| 1 | Projection theorem (`thm:projection`) | **New but incremental.** Lossless charge-only core is near-folklore; the losses, exports and gross-budget version is new as far as found |
| 2 | One-fee bound (`prop:onefee`) | **Partly known.** Not a Shapley–Folkman corollary, but a short consequence of classical matching facts |
| 3 | Support-failure anatomy and bands (`prop:anatomy`, `prop:bands`) | **New but incremental.** Elementary consequences of the 1-D frontier; no prior statement found |
| 4 | Price iteration (`thm:iteration`) | **Partly known.** Frank–Wolfe/ergodic parts known; myopic 2-cycles in coupled EV-grid pricing published (Alizadeh et al. 2017) |
| 5 | Separation message (duty-first) | **New as a theorem, for a narrow class.** Empirical sequential-vs-integrated gaps are published (Nath et al. 2024: 4.1% mean) |

---

## 1. Projection theorem

**Closest prior statements.**
- *Fixed population:* Mukhi–Loho–Abate (2026, TSG) and Panda–Tindemans (2024, EPSR). Aggregate EV flexibility is a Minkowski sum or g-polymatroid; for a fixed matching and lossless charging, our per-matching aggregate is a special case (a Minkowski sum of intervals).
- *Computing r_m:* Dell'Amico–Martello (1997), k-cardinality assignment. Convexity of r_m in m: min-cost flow, Murota (2003). Sorted opposite-order pairing: Monge arrays, Burkard–Klinz–Rudolf (1996).
- *Population as a decision:* E-VSP models with joint assignment and charging (de Vos et al. 2024; Wu et al. 2022; Zhou et al. 2025). These optimize at one price vector. None asserts that one assignment's attainable load set contains all others'.

**What I could not find.** Any statement, in aggregation, E-VSP or discrete-convexity literature, where the vehicle-to-task assignment is a decision and one assignment's *attainable set* contains every other assignment's at the same fleet size. I also found no two-window aggregate with conversion losses, exports and a *gross* connector budget.

**Verdict: new but incremental.** A referee will say the lossless charge-only case follows in a few lines: the bound sums are invariant and only R(M) moves, so containment is monotonicity in one scalar. Most of the theorem's weight sits in the losses/V2G/gross-budget construction and serial realizability. That is where the paper should place its claim.

**Concede or cite.**
- Cite `dellamicoMartello1997kcard` where r_m is defined for a general graph.
- Cite `murota2003dca` for discrete convexity of r_m (appendix "Monotonicity, convexity"); this replaces an uncited proof of a classical fact.
- Cite `burkard1996monge` for the sorted pairing (currently "a classical exchange argument").
- Add one sentence in Related work: for lossless charge-only, the per-matching aggregate is a special case of g-polymatroid aggregation (`mukhiLohoAbate2025exact`, `pandaTindemans2024`). The new element is the containment across matchings and its persistence under losses, exports and the gross budget. Patch block (1) does this.

## 2. One-fee bound

**Closest prior statements.**
- *Udell–Boyd (2016) Thm. 1 and Aubin–Ekeland (1976):* gap ≤ Σ of the min(m̃, n) largest ρᵢ, or ≤ min(m+1, n)·ρ_max. Bertsekas et al. (1983) apply the same idea to unit commitment.
- *Ravi–Goemans (1996), Berger–Bonifaci–Grandoni–Schäfer (2011):* the Lagrangian optimum of a matching problem with one side constraint lies between two adjacent matchings, which differ by one alternating path or cycle.

**Analysis.**
- With buses or services as blocks, the matching gives n_B coupling constraints. Shapley–Folkman-type bounds then give about (n_B + 2)·f, which grows with fleet size. **The one-fee bound is therefore not their corollary, and is tighter by a factor of order n_B.**
- Treating the fleet as one block (as the paper's CH does) gives the trivial bound D − CH ≤ ρ(c), where c is the fleet value function in (E, L). `prop:onefee` is exactly the claim ρ(c) < f.
- ρ(c) < f follows in two lines from discrete convexity of the min-cost k-matching value. Equivalently, for the lossless charge-only matching case: the hull equals the matching-polytope LP with one side constraint, whose optimum lies on an edge between two matchings of cardinality differing by ≤ 1.
- Independence of G ("any convex grid cost including hard limits") is automatic once the bound is written as ρ(c). It is not an additional result.

**Verdict: partly known.** The statement does not appear in this exact form in what I found, but every step is classical. An OR referee will likely regard it as a remark.

**Concede or cite.**
- Rewrite the paragraph after `prop:onefee` along the lines of patch block (2): cite `aubinEkeland1976`, `bertsekas1983scheduling` and `udellBoyd2016gap` for what Shapley–Folkman gives, and why that is weaker here.
- Cite `raviGoemans1996cmst` and `berger2011budgeted` for the adjacency route.
- Drop "independent of fleet size" as a selling point. Say instead that the nonconvexity is one-dimensional in the pair count.
- Consider demoting `prop:onefee` to a corollary or remark.
- Keep the sharpness example; it is useful.
- Do **not** cite Chao (2019) for any "one unit's cost" uplift bound; none was found in its accessible abstract.

## 3. Support-failure anatomy and intercept bands

**Closest prior statements.**
- The support criterion (gap = 0 iff supported) is classical, and the paper already concedes it (`huembs2022complete`, Gribik–Hogan–Pope, Hua–Baldick).
- The "price must exceed fixed cost divided by quantity" threshold is the standard average-cost/marginal-cost tension in nonconvex pricing (O'Neill et al. 2005).
- I found no statement of the κη²/8 bound or of exact intercept failure intervals for a fleet or for any 1-D piecewise-linear convex frontier plus a strictly convex cost.

**Verdict: new but incremental.** These are elementary 1-D convex-analysis consequences of the frontier, specific to this model. Their value is diagnostic: a referee is unlikely to say "known" but may say "routine". The telescoping-width result (`prop:bands`) is the most distinctive piece.

**Concede or cite.** State that the threshold f/η is the per-kWh form of the classical nonconvex-pricing condition. No new citation is needed beyond O'Neill et al. and Gribik–Hogan–Pope.

## 4. Price iteration

**Closest prior statements.**
- Already conceded: Frank–Wolfe on the hull (Jaggi 2013); Ma et al. (2016) damped update; ergodic recovery (Larsson et al. 1999; Nedić–Ozdaglar 2009).
- **New concession:** Alizadeh et al. (2017, §V-A, Table II) publish a two-period oscillation of myopic marginal pricing in a coupled EV–grid system that has a convex social optimum and supporting prices. Gan–Topcu–Low (2013) show a proximal term restores convergence.
- Wei et al. (2018) give only local convergence of the price-OPF loop; Roozbehani et al. (2012) give instability conditions for real-time price feedback.

**Verdict: partly known.** "Undamped prices can cycle even when a supporting price exists" is published (Alizadeh et al.). The application-specific content survives: period ≤ 2 for an endpoint selection on a 1-D frontier, the trapping band, the role of exact ties, and the observation that face optima cycle with or without a gap.

**Concede or cite.** Add the coupled-pricing paragraph (patch block 3). In the contribution list, replace "can cycle even when a supporting price exists" with a sentence that credits Alizadeh et al. for the phenomenon and claims the characterization.

## 5. Separation message (duty-first)

**Closest prior statements.**
- *Sequential vs. joint, transit:* Nath, Rambha and Schiffer (2024, TR-C; already cited). Joint charge scheduling and trip assignment lowers total cost by 4.1% on average and operating cost by 14.1% vs. sequential, over 14 networks with 432–3,337 trips. The per-network range is 0.13–7.7%, and the totals include charger siting.
- *Logistics:* Klein and Schiffer (2023, Transportation Science). Flexible departure times save 1–5% under day-ahead prices, scaling with price variance.
- *Assign first, then charge as a min-cost flow:* Sassi and Oulamara (2017, IJPR). A heuristic, with an NP-hardness result for the joint problem.
- *Possible near-match, unverified:* Wang et al. (2026, TR-B 206, 103430). A snippet states that sequential vehicle–crew then charging scheduling did not affect global optimality in their experiments. Full text not accessible.

**Search result.** No theorem giving conditions under which duties chosen before prices lose nothing, and no bound on the integration loss (33 queries; see `LIT_REVIEW_R2.md` §C).

**Verdict.**
- The theorem-backed statement "in this class an operator can fix duties before prices without loss of attainable load–cost set" is new, as far as this search found.
- Its scope is narrow (two synchronized batches, common windows). The empirical side of the message is partly known. That integration helps on general instances by a few percent is established (Nath et al.). The paper's ≤ 2.04% upper bound on 64 synthetic hourly instances is consistent with and below Nath's 4.1% mean, so it adds a data point but not a new finding.

**Concede or cite.**
- Add patch block (4): Sassi–Oulamara, Perumal et al., Nath et al. numbers, Klein–Schiffer, Abdelwahed et al., He et al., Zhang et al. 2024.
- State that published integration gains are computational and of order 0–8% of total cost (Nath et al.).
- Distinguish them from charging-only gains on fixed schedules (14–78%), which are larger and support duty-first plus optimized charging.
- Do not cite Wang et al. (2026) until read.
- Replace the Zhou et al. "abstract only" caveat. The full accepted manuscript is now read (patch block 5). Note that its abstract's "8.5%" disagrees with its own Table 6 (16.9%).

