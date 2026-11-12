# Novelty verdict, round 2 (12 November 2026)

One entry per claim: the closest prior statement found, a verdict, and what the paper should concede or cite. Sources and access status are in `LIT_REVIEW_R2.md`; new bib keys are in `references_r2.bib`. A verdict of "new" means only that this search found no prior statement. It is not a priority guarantee.

| # | Claim | Verdict |
|---|---|---|
| 1 | Projection theorem (`thm:projection`) | **New but incremental.** Lossless charge-only core is near-folklore; the losses, exports and gross-budget version is new as far as found |
| 2 | One-fee bound (`prop:onefee`) | **Known, up to presentation.** Non-strict form is a Udell–Boyd/Shapley–Folkman corollary under a per-marginal-pair blocking |
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

**Closest prior statement.** Udell–Boyd (2016) Theorem 1; see also Aubin–Ekeland (1976) and Bertsekas et al. (1983). For a separable objective with m̃ simultaneously active coupling constraints, the gap is at most the sum of the m̃ largest nonconvexities ρᵢ.

**Derivation** (`LIT_REVIEW_R2.md` §A, item 3). Write the fleet with one block per marginal pair:
- x_m ∈ [0, η_m], where η_m = ℓ_m − ℓ_{m−1};
- the block earns −f only at x_m = η_m;
- one coupling constraint, ℓ₀ + Σx_m ≤ E;
- the convex grid cost G is a separate block, with hard limits as its domain.

The paper's discrete convexity of ℓ_m (η_m nondecreasing) makes this block problem's physical value equal D. Its convexification is a fractional knapsack that reproduces the paper's hull frontier. Since ρ(f_m) = f and m̃ = 1, Theorem 1 gives **D − CH ≤ f**, for any G and any fleet size. The adjacency device for budgeted matching (Ravi–Goemans 1996; Berger et al. 2011) gives the same bound directly on the matching polytope.

**Verdict: known, up to presentation.** The non-strict bound is a direct corollary of the Shapley–Folkman family (or of the fractional-knapsack LP gap). The model-specific ingredient is discrete convexity of the min-cost k-matching value, which is classical. The strict inequality and the f(t − ⌊t⌋) form add one line.
- Caution: ρ(fleet value function) equals f, not less. Strictness comes from evaluating at the attained hull optimum.
- An earlier draft of this note said the bound was "not a corollary, tighter by a factor of n_B". That held only for a per-service blocking and is withdrawn.

**Concede or cite.**
- Demote `prop:onefee` to a remark or corollary. State that it follows from Udell–Boyd Thm. 1 (`udellBoyd2016gap`; also `aubinEkeland1976`, `bertsekas1983scheduling`) applied to a per-marginal-pair blocking, given discrete convexity of the thresholds (`murota2003dca`).
- Do not sell fleet-size or grid-cost independence as contributions.
- Keep the sharpness example and the counterexample showing discrete convexity is needed.
- Do not cite Chao (2019) for any "one unit's cost" bound; none was found in its accessible abstract.

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
- Its scope is narrow (two synchronized batches, common windows). The empirical side of the message is partly known. That integration helps on general instances by a few percent is established (Nath et al.). The paper's ≤ 2.04% upper bound on 64 small synthetic hourly instances (8–12 trips) is numerically below Nath's 4.1% mean. The settings differ too much (real networks of 432–3,337 trips, charger siting included) to claim agreement. Wang et al. (2026, TR-B), which reportedly finds sequential charging scheduling harmless, could not be read and is the most direct unread threat.

**Concede or cite.**
- Add patch block (4): Sassi–Oulamara, Perumal et al., Nath et al. numbers, Klein–Schiffer, Abdelwahed et al., He et al., Zhang et al. 2024.
- State that published integration gains are computational and of order 0–8% of total cost (Nath et al.).
- Distinguish them from charging-only gains on fixed schedules (14–78%), which are larger and support duty-first plus optimized charging.
- Do not cite Wang et al. (2026) until read.
- Replace the Zhou et al. "abstract only" caveat. The full accepted manuscript is now read (patch block 5). Note that its abstract's "8.5%" disagrees with its own Table 6 (16.9%).

