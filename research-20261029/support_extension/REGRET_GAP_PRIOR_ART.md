# Planning gap, own-price regret and closest primary results

Bounded primary-source check following framework.tex, ownership.tex, related_work.tex and references.bib. No numerical work, code execution, evidence replay or manuscript edits. Three works considered; relevant full text inspected for two, with the third explicitly abstract-only. The exact proposed smoothness/diameter inequality was **not located** in these inspected sources. This is not an absence or novelty claim.

## Closest verified results

**Hua and Baldick (2017), A Convex Primal Formulation for Convex Hull Pricing.** [Author-hosted full text](https://users.ece.utexas.edu/~baldick/papers/convex_hull_2017.pdf), IEEE TPWRS32(5),3814–3823, DOI10.1109/TPWRS.2016.2637718. Inspected SectionsII.B–III.A, especially p3816, equations(6)–(9) and Theorem1. Price-taking lost opportunity cost compares best private profit with dispatched profit. Its sum equals the price-dependent primal–dual gap; optimizing the dual price minimizes it. Theorem1 identifies the convexified primal. This is the closest conceptual precedent: “gap versus incentive” must distinguish the selected price and the participants included. It does not equate a physical load's marginal supply price with an optimal convex-hull price.

**Bertsekas and Sandell (1982), Estimates of the Duality Gap for Large-Scale Separable Nonconvex Optimization Problems.** [Author-hosted full text](https://web.mit.edu/dimitrib/www/Duality_Gap.pdf), CDC1982,782–785. Inspected Section2, assumptionsA1–A3, proposition on p783 and proof/discussion p784. Their gap estimate is (m+1) times the largest defined per-term nonconvexity quantity, independent of the number of terms; dividing by term count yields a vanishing average gap under the stated uniform controls. This concerns separability, rounding feasibility and normalized welfare error, not a composite owner's own-price deviation. It supplies no uniform shrinking bound for that distinct absolute incentive merely from aggregation size.

**Hreinsson, Scaglione, Alizadeh and Chen (2021), New Insights From the Shapley-Folkman Lemma on Dispatchable Demand in Energy Markets.** [Publisher record](https://ieeexplore.ieee.org/document/9376954/), DOI10.1109/TPWRS.2021.3065913, TPWRS36(5),4028–4041; corroborated by the [author publication list](https://web.ece.ucsb.edu/~alizadeh/publist.html). Only the publisher's abstract/metadata and author entry were accessible in the focused routes; the author entry points back to IEEE. The abstract concerns approximate aggregate convexity in actions/cost, strict convexity under conditions and reduced-order models. No theorem/page claim about individual or whole-owner regret is verified here. Do not cite it as proving or contradicting the proposed inequality without the full relevant text.

## What the proposed inequality actually adds

The following is an elementary derivation for interpretation, not a result attributed to the sources above. Let compact Z consist of whole-plan pairs (u,c), let (u,c) be a physical planner optimum, let (u*,c*) minimize c+F(u) over conv(Z), and put Delta=D−CH. Assume F is differentiable, mu-strongly convex and has L-Lipschitz gradient on a convex domain containing all loads, with one fixed Euclidean norm, mu>0. Let R be the diameter of the physical load set (also the diameter of its convex hull). Define p*=gradF(u*) and p=gradF(u), and r_x(q)=c+q·u−min_Z(c_y+q·u_y).

Hull optimality makes (u*,c*) a private-score minimizer at p*. Consequently

    r_x(p*) = Delta − B_F(u,u*) <= Delta,
    Delta >= B_F(u,u*) >= (mu/2)||u−u*||².

The regret function for this fixed x is R-Lipschitz in price, since it is the maximum of affine functions with slopes u−u_y. Thus

    r_x(p) <= Delta + R||p−p*||
            <= Delta + L R sqrt(2 Delta / mu).

Ties and zero gradients do not break this reasoning. If price admissibility is restricted, the bound remains an algebraic score comparison, but interpreting p or p* as admissible economic prices requires that qualification separately. Neither a strategic tariff reset nor a repeated-price convergence claim follows.

The first identity is especially useful beside convex-hull pricing: with convex supply treated as another participant, its lost opportunity cost at p* is B_F(u,u*), so fleet regret plus supplier regret is Delta. At the physical own-load gradient the supplier is privately optimal, but that different price need not minimize total lost opportunity cost. There is therefore no conflict with the classical identity/minimization result.

## Value for this paper

**Useful as a short explanatory bound, not another lead theorem.** It identifies the uniform controls that would make small Delta imply small own-price regret: bounded load diameter, smoothness and a nonvanishing strong-convexity modulus, or an explicit vanishing combination of their factors. It replaces an easily misunderstood unqualified “small gap says nothing” slogan by a conditional quantitative statement.

In the existing replication family, loads scale with n, while F_n has Hessian proportional to1/n; hence R_n is proportional to n and both L_n and mu_n are proportional to1/n. Along the stated Delta_n proportional to1/n subsequence, the second term need not vanish. That exactly explains why a composite owner's absolute regret can stay positive while per-owner/per-bus incentives shrink. The physically realizable ownership example and its exact constants remain the application-specific content; generic convex analysis and the duality/LOC connection are prior machinery.

Recommendation: one compact corollary or paragraph following the ownership theorem, explicitly tied to the price distinction and scaling assumptions. Do not claim a new general approximate-equilibrium principle, or represent bounded search as evidence that no equivalent estimate exists elsewhere. The Hreinsson full-text limitation remains unresolved.
