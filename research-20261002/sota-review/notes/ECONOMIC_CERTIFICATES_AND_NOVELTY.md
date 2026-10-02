# Economic certificates, bound reuse and the novelty boundary

Working derivations, 2 October 2026. No solver or cluster experiment was run. These are elementary consequences of weak duality and convex analysis, written to prevent an invalid algorithmic claim. They are not asserted to be new theorems. A later review should assess whether a sharper, fleet-specific result is available.

## Definitions and assumptions

Let \(X\) contain all physically feasible complete-fleet schedules under the original timetable, charger and battery constraints. Let \(c(x)\) be intrinsic fleet cost and \(e(x)\in\mathbb R^T\) its grid-load vector. Let \(F\) be proper closed convex supply cost, including its supply-feasibility domain. Assume the quantities evaluated below are finite. Write

\[
D=\inf_{x\in X}\{c(x)+F(e(x))\},\qquad
V(p)=\inf_{x\in X}\{c(x)+p^\top e(x)\}.
\]

The complete-fleet hull value is

\[
CH=\inf_{(\bar e,\bar c)\in\operatorname{cl}\operatorname{conv}\{(e(x),c(x)):x\in X\}}
\{\bar c+F(\bar e)\}.
\]

Fenchel weak duality gives \(q(p)=V(p)-F^*(p)\le CH\le D\) for every price with finite \(V(p)\) and \(F^*(p)\). Attainment/equality between \(\sup_pq(p)\) and \(CH\) requires the usual additional closure/regularity conditions; none of the one-sided bounds below silently assumes it. The institution's price-taking response set is the same \(X\) throughout. If it also requires supply feasibility for every deviation, put that requirement in \(X\) explicitly.

## 1. Separate the two jobs done by a pricing oracle

A learned restriction \(X_R\subseteq X\) can return a useful physically validated candidate \(x_R\). Its pricing objective \(v_R=c(x_R)+p^\top e(x_R)\) is an **upper** bound on \(V(p)\). It can supply a new complete-fleet column. A lower bound from minimizing over \(X_R\), however, need not lower-bound \(V(p)\).

Counterexample: the full pricing problem has two feasible schedules with objective values 0 and 10. If pruning discards the first, the restricted solver proves its optimum is 10. Substituting this number for a global pricing lower bound raises the claimed dual bound by 10. Exact solution of the restricted problem does not fix that error.

Instead obtain \(\ell(p)\le V(p)\) from an unpruned oracle, a proven relaxation, or a safely screened equivalent formulation. Let \(\widehat F^*(p)\ge F^*(p)\) be exact or an independently certified upper enclosure for the conjugate. Then

\[
L(p)=\ell(p)-\widehat F^*(p)\le CH.
\]

Numerically maximizing \(p^Te-F(e)\) produces a conjugate incumbent **lower** bound; that is the wrong direction for \(\widehat F^*\). Use an analytic value, a verified optimization upper bound, or a rigorous upper enclosure. An unpruned solver output is still tolerance-qualified unless its formulation, outer-approximation direction and numerical uncertainty are validated.

Finite convex weights on replayed complete-fleet columns give a feasible hull point and hence an upper bound

\[
U_{CH}=\sum_j\lambda_jc(x_j)+F\!\left(\sum_j\lambda_je(x_j)\right),
\quad \lambda\ge0,\quad\sum_j\lambda_j=1.
\]

This upper bound does not require the restricted master to be solved optimally. It does require a valid mixture, a mean load in \(\operatorname{dom}F\), valid column costs/loads and a certified evaluation if the result is presented as an exact enclosure. A physical-plan upper bound additionally requires that individual plan's load to lie in \(\operatorname{dom}F\). Floating-point master feasibility and solver tolerances must be accounted for separately.

**Algorithmic implication:** use learned solves to generate columns and unrestricted bounds to certify. First verify \(\max_kL(p_k)\le U_{CH}\); a negative reported width is an inconsistency, not successful termination. Then stop on \(U_{CH}-\max_kL(p_k)\le\epsilon\), not on failure of the learned oracle to find an improving column. Retain the strongest valid bounds across iterations. The regularized master objective is not a replacement for the unregularized economic objective.

## 2. Price support has a different stopping target from a good schedule

For a fixed feasible schedule \(x\), price-taking regret is

\[
r(x;p)=c(x)+p^\top e(x)-V(p)\ge0.
\]

If a validated pricing incumbent gives \(V(p)\le v(p)\), then

\[
\max\{0,c(x)+p^\top e(x)-v(p)\}\le r(x;p)
\le c(x)+p^\top e(x)-\ell(p).
\]

Include \(x\) itself among response incumbents if desired. A loose global lower bound explains a wide regret interval even when the recommended schedule is excellent. A cheap response incumbent can prove a profitable deviation; it cannot prove that none exists. Thus the best algorithm for finding a cheap schedule need not be the best algorithm for certifying its support.

For a supply-compatible plan with \(F(e(x))<\infty\) and an actual \(p\in\partial F(e(x))\), Fenchel equality yields
\[
r(x;p)=c(x)+F(e(x))-q(p)\ge c(x)+F(e(x))-CH.
\]
If independently valid physical and hull intervals satisfy \(D_L>CH_U\), no physical schedule is supported by its own marginal prices under this institution. An arbitrary schedule's positive regret is a different finding: it could reflect that schedule's physical suboptimality. A zero-containing gap interval proves neither support nor non-support.

These statements concern price-taking deviations at a posted price, not strategic anticipation of the operator's price impact. A proper closed convex supply cost need not have a subgradient at every boundary point. At nonsmooth supply costs, finding a bad price in a nonempty marginal-price set does not show that every admissible marginal price is bad.

## 3. A useful bound-reuse candidate, not yet an originality claim

Suppose a previous unrestricted solve certified \(\ell_k\le V(p_k)\). Let \(\mathcal E\) be any **proven outer set** containing \(e(X)\). For another price \(p\),

\[
V(p)\ge\ell_k+\inf_{z\in\mathcal E}(p-p_k)^\top z.
\]

Proof: for every \(x\in X\), its old pricing objective is at least \(\ell_k\); its load belongs to \(\mathcal E\). Add the two inequalities and take the infimum over \(x\). The maximum over cached certificates is still a valid lower bound.

If a hardware-derived componentwise bound is \(0\le e_t(x)\le\bar E_t\), an inexpensive expression is
\[
\ell_{\rm cache}(p)=\max_k\left\{\ell_k+
\sum_t\bar E_t\min(0,p_t-p_{k,t})\right\}.
\]

The bound is usually weak over large price changes, but it may make nearby price queries cheap. Tighter valid energy/capacity relaxations could improve it. Training-set load extrema and incumbent fleet counts are not valid global hardware bounds. Convert power to interval energy when \(e_t\) measures energy; export requires signed load bounds. A tariff change can reuse this argument only when the physical set and intrinsic costs remain unchanged, including units, efficiency, discretization and any tariff terms embedded in \(c\). Changed hardware, timetable or cost definitions need a new justification. Supply-function changes can reuse \(V\) if its definition is unchanged, but require the new conjugate.

This suggests a budget rule: first evaluate cached bounds and retained columns at a candidate price, then invoke an expensive unrestricted oracle only if the desired economic certificate remains unresolved. Compare with ordinary retained columns, stabilized CG and warmstarted full pricing at equal end-to-end time. Search parametric optimization, Lipschitz bounds and inexact bundle literature before asserting novelty. Merely writing this inequality is not an OR-level contribution.

## 4. What the new paper would have to add

Direct prior art already covers incumbent-imitation GNN arc reduction for electric buses: [Gerbaux, Desaulniers and Cappart, COR 2025](https://doi.org/10.1016/j.cor.2024.106848). Learning initial duals to accelerate certified column generation also exists: [Sugishita, Grothey and McKinnon, IJOC 2024](https://doi.org/10.1287/ijoc.2022.0140). See the companion source reviews for the actual inspected texts and limits.

A plausible research direction is an algorithm that allocates effort between learned feasible schedule search and unrestricted economic certification, handles route/price distribution shift through recoverable restrictions, and quantifies when an approximate operational schedule is or is not economically supportable. The distinguishing evidence would be reusable conclusions about this tradeoff, not just a new model architecture or another pruning percentage.

The current E0/E9 reports give a reason to pursue that direction, not its completion. E0 has small, tolerance-qualified positive gaps on four development timetables. E9 improves hull enclosures with learned seed plans, but the cost of obtaining those seeds precedes the nominal hull budget; cold-start and amortized comparisons must be reported separately. Larger cases still lack decisive support gaps. Numerical failures remain failures until a separately measured correction passes the original physical checks.

## Open proof/research checks

- Can fleet structure produce a materially tighter \(\mathcal E\) at negligible cost, or does price coupling make cached bounds unhelpful?
- Can a prospective oracle-allocation policy improve time to *both* feasible quality and certified regret without tuning on evaluation outcomes?
- Which quantities require rigorous arithmetic, which have native tolerance-qualified bounds, and what uncertainty margin is needed before declaring a tiny economic gap positive?
- Does a proposed route-column decomposition describe exactly the original complete-fleet hull? A strong route relaxation can be useful without being the same economic object.
- What is new beyond existing inexact/stabilized CG? A missing closest-paper match is not proof of novelty.
