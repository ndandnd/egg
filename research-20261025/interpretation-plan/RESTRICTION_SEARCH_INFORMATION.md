# Restriction, finite-budget search and information

Design/interpretation note only. Condition on a fixed fleet count, physical resources, target tariff and objective $f$. Let $S$ be the original physical feasible set and $S_r\subseteq S$ a route-pruned feasible set containing the common valid prior $p$. Write $z^\star=\inf_{s\in S}f(s)$ and $z_r^\star=\inf_{s\in S_r}f(s)$, assuming finite values. Infima avoid assuming an optimizer is attained. Let $U_r$ be the cost of the best retained, replay-valid member of $S_r$ available within the paid decision clock; startup, scoring, construction, search, extraction and admission all consume that clock.

Define restriction regret $R_r=z_r^\star-z^\star\ge0$ and restricted search error $E_r=U_r-z_r^\star\ge0$. Then the elementary identity is

\[
U_r-z^\star
=\underbrace{z_r^\star-z^\star}_{\text{restriction regret }R_r}
+\underbrace{U_r-z_r^\star}_{\text{restricted search error }E_r}.
\]

For a full-set incumbent $U_{\mathrm{full}}$, define $E_{\mathrm{full}}=U_{\mathrm{full}}-z^\star$. Define gain as full cost minus pruned cost, positive when pruning wins:

\[
U_{\mathrm{full}}-U_r=E_{\mathrm{full}}-E_r-R_r.
\]

Pruning can win when its reduction in search error exceeds its restriction regret. Random compression can therefore improve a finite-budget incumbent without supplying learned information. Scoring overhead is already reflected in the resulting paid-clock incumbent; it is not a free resource. These are classical definitions and algebra, not a novel theorem. Exact optima and both error terms remain unobserved: this decomposition is an interpretation device, not a calculation recoverable from current receipts.

| Comparison or observation | What it can identify under its declared design | What it misses |
| --- | --- | --- |
| Pruned versus full at a common paid budget | Net performance of a restriction/search policy | Separate restriction regret and search error; full-space optimality |
| Learned versus competent classical pruning | Additional value of the particular learned policy under those controls | A causal value of training information or tariff information |
| GNN versus GNN_day | Effect of changing inference-time $a$ for the same frozen model, with the target optimization objective held fixed | Effect of training tariff-aware versus tariff-blind models |
| Fixed-route charging versus route adaptation | A conditional operational contrast, subject to control qualification | An unrestricted fleet optimum or a causal timing/demand decomposition |

A replay-valid feasible incumbent is an upper bound on the corresponding optimum. A restricted-set or fixed-route lower bound concerns that restricted problem; it is not a lower-bound certificate for full $S$. Numerical solver reports additionally retain their numerical/model/replay qualifications. The word “full” here still means the stated fixed-fleet conditional problem.

The nonnegative-error statements assume actual membership in the declared
mathematical feasible set. Current numerical solver/admission flags under stated
tolerances do not alone prove exact ideal-model feasibility or an exact global
certificate. The identity does not upgrade those engineering checks into a proof.

Including $p$ gives $z_r^\star\le f(p)$, but operational $U_r\le f(p)$ additionally requires genuine best-valid retention and timely admission, or continued availability of the already valid fallback when a method fails or returns late. Recovery is monotone only through that retention rule; it does not establish global optimality.

A failed mask that cannot include the prior is outside this construction;
do not assign it a finite restricted optimum or zero restriction regret. Its
operational fallback is reported separately. If physical resources change,
replay or reacquire the prior under those new resources before assuming it is
still feasible. A price-only intervention does not justify that assumption for
battery, SOC or shared-charging changes.

No algebra above identifies information causality. Comparably selected tariff-aware/blind training and controlled inference interventions answer different questions. The current eight development groups do not establish independent generalization or a publication-level contribution. This note changes no current source, model, protocol, criterion or run, and is not a manuscript or a new experiment authorization.
