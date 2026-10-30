# Independent review: transition-energy boundary and controlled common-d extension

Reviewed TRANSITION_ENERGY_BOUNDARY.md analytically. No data, numerical tools, imports, execution, tests or new cases were used.

## Counterexample: PASS for the stated abstract model

The paired-bus lower bound max(0,a+t+b−20) and upper bound a are correct. For every allowed edge, t+b≤20, so each paired interval is nonempty. Since transit and service draw are nonnegative, valid inventory after B plus early capacity ensures feasibility at every intervening prefix. Full terminal refill accounts for every transition unit; no initial inventory credit is used.

Identity matching consumes28 with summed early minimum6. Cross matching consumes40 with summed minimum0. Early upper14 is the sum of A headrooms. Terminal40 accommodates both entire stated segments. All buses share both charging windows, and per-bus acceptance is at least the connector power, so aggregate early energy≤14 and terminal energy≤40 give serial schedules of duration≤one hour in each window. Transit itself occupies the separate positive-duration hour and provides no charging. Thus the construction does not disguise positive transition consumption as instantaneous charging access.

The identity point at early6 is undominated by any cross point with no greater early load, and both full matchings have identical two-bus fee. Standalone/partial alternatives cannot dominate it in joint (E,L,c) when f>0 because they pay for more buses. Under F(E,L)=E+L, all identity full-match points cost2f+28. No plan can use fewer than two buses because services overlap within each batch, or consume less than28 because transitions are nonnegative. Empty matching costs4f+28. The small-service identity edge supplies a minimum-R one-edge plan at3f+28; cross one-edge alternatives consume34 and cannot improve it. Minimum-R full matching retains only the cross branch at2f+40. Therefore the stated excess min(12,f) is strictly positive for EVERY f>0, even granting favorable tie handling in the one-edge layer. At f=0 that strict whole-problem comparison can disappear, as stated.

The example is an available-duty/mandatory-transition model. It does not derive its transition table from a common metric travel/auxiliary law, claim empirical route realizability, or permit transition tasks to be deleted as optional excursions. Zero-energy positive-duration transit and zero-energy resource access are explicit idealizations. If free retiming, different charging locations, extra services or removable detours were admitted, the declared feasible set would change. No claim about all positive-transition models or the public timetable follows.

## Controlled common consumption d: extension is sound with one upper-bound correction

For a common nonnegative d per used matching edge, all size-m matchings have the same total consumption S_m=S+m d and bus count N_m=2n−m. Restrict the fixed allowed graph to edges satisfying b_j+d≤B. Paired battery exchange then has box [a_i+b_j+d−B,a_i]; singleton boxes are unchanged. Positive lower endpoints sum to R, all lower endpoints sum to T_m=S_m−N_m B, and upper endpoints still sum to P. The condition b_j+d≤B is what makes every paired box nonempty; it must not be omitted when declaring the graph.

Consequently the common-loss fixed-matching proof carries through with S replaced by S_m, and minimum R over the allowed size-m matchings suffices because S_m is constant within that layer. In particular

    r_m = min size-m allowed matching Σ[a_i+b_j+d−B]+,
    L_m(E) = S_m/α−E+κ[r_m/α−E]+,
    t_m = max{(1/α−δ)r_m+δ(S_m−N_m B),
              2r_m/α−K, S_m/α−H,
              (S_m/α+κr_m/α−H)/(1+κ)}.

**The physical upper remains U=min(P/α,K), not P/α alone**, because the shared early gross budget still implies E≤K. P/α is only the raw inventory upper before that resource restriction. All other minimum-export, sign construction and serial terminal arguments remain valid under common efficiencies and common windows. Each feasible cardinality again contributes at most two efficient segments; domination across cardinalities still requires pruning.

This extension needs the same zero-reserve/full-start-end assumptions, no other charging/access, constant common grid-side acceptance, positive bus fee/no matching-dependent monetary costs, and nonnegative transit/service consumption. Transitions must occur after the common early window and before the B service without disturbing common charger availability; a real travel-time model that changes these windows is not covered. A common d says nothing about empirical travel geometry. Supply-value reduction still requires coordinatewise monotonicity on all admitted signed loads, and zero-price ties are not enumerated by the efficient reduction.

The r_m matching value function remains discretely convex, and substituting S_m into threshold components adds only affine nondecreasing cardinality terms. However, the original lossless scalar support criterion generally does NOT transfer: even at α=δ=1, different cardinalities lie on different total-energy lines E+L=S_m. The hull now mixes both load coordinates and cost, rather than a common fixed-total-energy cost staircase. Retaining the three-dimensional segment hull and applying general support theory is valid; a universal threshold-location test needs a new proof.

**Recommendation:** accept the counterexample as a precise scope boundary. The common-d model is a legitimate controlled analytical extension with the corrected resource upper and explicit timing/graph conditions, not an implementation qualification or an unrestricted movement-energy theorem.
