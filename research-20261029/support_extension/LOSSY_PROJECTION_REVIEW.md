# Independent mathematical review: common-loss efficient projection

Reviewed `LOSSY_PROJECTION_CANDIDATE.md` analytically, including the fixed-matching construction, shared connectors, global reduction and capped-idle argument. No numerical calculation tools, imports, tests, actual artifacts, execution, new cases, paper edits or commits were used.

**Assessment: the efficient-projection result is valid for the declared zero-reserve model.** No counterexample or required algebraic correction was found. It is substantially narrower than equality of the complete physical projection or a general lossy support classification, and the candidate correctly retains those distinctions.

## Fixed matching and physical realization

The paired, A-only and B-only battery-exchange boxes correctly encode full initial inventory, early capacity and nonnegative inventory after all assigned services. For example, a paired bus has inventory B−a+x before B and B−a+x−b after it, giving x≥a+b−B and x≤a. The lower endpoints sum to T=S−NB, their positive part sums to R, and the aggregate negative capacity is R−T. The positive lower coordinates are necessarily paired; all remaining coordinates contain zero, which is essential to the construction.

For cycle-free exchange, C≥R/α and E=C−D imply D≥[R/α−E]+. At fixed E, accounting makes terminal L nondecreasing in D and gives the stated minimum curve. For E below R/α, choosing all mandatory positive exchanges at their lower endpoints and distributing only negative exchanges on coordinates containing zero attains the lower bound whenever D≤δ(R−T). For E above R/α, distributing positive exchange from R to P and using no negative coordinates attains it. These distributions fill intervals continuously; they do not treat positive and negative capacities of the same bus as independent simultaneous choices.

Substituting that construction yields gross early throughput max(E,2R/α−E), hence both E≤K and E≥2R/α−K. The lower raw endpoint is (1/α−δ)R+δT and upper raw endpoint P/α. Requiring both affine pieces of L_R(E)≤H yields precisely the two terminal lower bounds in the displayed maximum. Together these conditions are necessary and sufficient; discarded empty cardinalities cannot be rescued by larger exported throughput.

The construction is physically implementable, not merely aggregate accounting. Each bus's monotone early action remains inside its SOC box; service endpoint inventories remain in [0,B]. Terminal battery deficits are nonnegative and at most B, hence require at most B/α grid energy per bus. All relevant buses share each window, accept the same connector's grid power, and can serialize their actions whenever aggregate gross early and terminal grid demands fit. Zero-power cases require zero corresponding energy, as stated. Positive reserve, unequal per-bus acceptance, noncommon windows or time-dependent within-window obligations are not covered by this proof.

## Matching and frontier claims

At fixed cardinality, every term in t(R,N) and L_R(E) is nondecreasing in R. Thus using an allowed matching attaining r_m preserves any feasible original E and weakly lowers terminal load at exactly the same bus fee. Arbitrary allowed graphs and singleton service options cause no additional construction problem. Finite matching minima suffice; the sorted complete-graph shortcut is not assumed.

Discrete convexity of t_m follows from convex interpolation of r_m and the affine inventory term in m: each threshold term is convex and nondecreasing, and so is their maximum. Sampling that convex function at consecutive integer cardinalities preserves nondecreasing discrete increments. This supports the initial feasible cardinality segment but does not establish the old one-dimensional cost-versus-E hull criterion. The candidate explicitly avoids that inference.

Each fixed-cost curve is strictly decreasing in terminal load with increasing early load, so its own distinct points cannot dominate one another. Across cardinalities, pruning is necessary. Every cycle-free physical point is dominated by a point in the finite segment union, and every union point is physical. These two inclusions prove equality of the nondominated frontiers after pruning. Segment endpoints/kinks generate the union's convex hull exactly.

## Cycles, objective scope and paid idles

Within-bus neutral-cycle removal preserves battery exchange and terminal demand while weakly decreasing gross connector use and early net grid load. Common-window monotone reconstruction preserves feasibility. Combining this with the fixed-cardinality replacement proves that every full physical point is dominated or matched by a physical point in Z. It does not erase the other, dominated points from the complete projection. The old same-E/different-L counterexample therefore remains valid.

Monotonicity is unnecessary for the set-theoretic efficient-frontier statement, but is necessary for the claimed physical and hull optimal-value reductions. Hull reduction follows by replacing each whole-plan mixture component with its dominating point before comparing the mean loads. Convexity of F permits the intended convex planning interpretation; coordinatewise monotonicity on the relevant signed domain is what justifies discarding dominated components. Nonnegative fixed prices give the analogous value reduction, but zero prices can retain tied discarded responses. No assertion of all response minimizers or a universal threshold support criterion follows.

For k identical idle buses under the total cap N≤2n, k≤m permits deletion of k matched edges. The replacement has the same bus count and fee, the same T, and no larger R; it can therefore attain the original E with no larger terminal load. This proves efficient-value dominance, not equality of complete joint projections. No uncapped conclusion is justified, as the candidate states.

## Small presentation clarification before integration

Write the cardinality range explicitly as `m=0,…,ν` in both occurrences currently compressed as “m0..nu.” There is no independently defined m0 in this candidate, and the lossless theorem uses a different m0 for a zero-threshold block. This notation clarification avoids suggesting that initial cardinalities have been dropped. It is not a mathematical defect.

Any manuscript integration should state zero reserve and common efficiencies/windows prominently, keep full-projection and efficient-frontier language separate, and label this an analytical result without numerical implementation qualification or public/empirical V2G evidence. Within those limits, the proof is ready for parent mathematical review.
