# Joint cached-price certificates: proof and novelty boundary

2 October 2026. Algebra and primary-source review only; no solver, optimization, cluster, or evaluation-data access. The constructions below are demonstrated mathematics; fleet performance and originality remain research questions.

## 1. Valid joint bound and its direction

Use the unchanged complete-fleet problem
\[
V(p)=\inf_{x\in X}\{c(x)+p^\top e(x)\}.
\]
Assume nonempty \(X\), finite intrinsic costs, a nonempty compact outer set \(\mathcal E\supseteq e(X)\), and finitely many finite certificates \(\ell_k\le V(p_k)\), \(k=1,\ldots,K\), \(K\ge1\). Define
\[
g(z)=\max_k\{\ell_k-p_k^\top z\},\qquad
J_{\mathcal E}(p)=\min_{z\in\mathcal E}\{g(z)+p^\top z\}.
\]
This equals the proposed epigraph program with \(t\ge\ell_k-p_k^\top z\). For every feasible schedule, every cached certificate implies \(c(x)\ge\ell_k-p_k^\top e(x)\), hence \(c(x)\ge g(e(x))\). Consequently
\[
B(p):=\max_k\left\{\ell_k+\min_{z\in\mathcal E}(p-p_k)^\top z\right\}
\ \le\ J_{\mathcal E}(p)\ \le\ V(p).
\]
The first inequality is \(\max\min\le\min\max\); the second follows by relaxing the schedule's cost/load pair. Compactness and continuity ensure the displayed minima exist. Convexity of \(X\) or \(\mathcal E\) is unnecessary for these inequalities. Adding certificates or shrinking \(\mathcal E\) while preserving outer validity cannot decrease \(J\). Also \(J(p_k)\ge\ell_k\). Both \(V\) and \(J\) are concave in prices because they are infima of affine functions.

The relaxation is an outer description of the cost/load epigraph: intersect \(z\in\mathcal E\) with half-spaces \(t+p_k^\top z\ge\ell_k\). It is not a collection of tangent lower planes to a concave value function. A feasible schedule instead produces the affine **upper** bound \(V(p)\le c(x)+p^\top e(x)\).

## 2. Mixtures, concavity, and the missing convexity condition

Let \(\Delta_K=\{\lambda\ge0:\sum_k\lambda_k=1\}\), \(\bar p_\lambda=\sum_k\lambda_kp_k\). Weighted certificate inequalities give, for every \(\lambda\in\Delta_K\),
\[
h(p,\lambda)=\sum_k\lambda_k\ell_k+
\min_{z\in\mathcal E}(p-\bar p_\lambda)^\top z\le V(p).
\]
Equivalently, concavity gives \(V(\bar p_\lambda)\ge\sum_k\lambda_k\ell_k\), and the outer load set transports that lower bound to \(p\). At simplex vertices this recovers \(B\).

If \(\mathcal E\) is additionally convex, the continuous bilinear expression
\(f(z,\lambda)=\sum_k\lambda_k\ell_k+(p-\bar p_\lambda)^\top z\)
has compact convex domains. The minimax theorem gives
\[
J_{\mathcal E}(p)
=\min_{z\in\mathcal E}\max_{\lambda\in\Delta_K}f(z,\lambda)
=\max_{\lambda\in\Delta_K}h(p,\lambda).
\]
This is a direct application of [Sion, *On general minimax theorems*, Pacific Journal of Mathematics 8(1), 171–176 (1958), Theorem 3.4](https://msp.org/pjm/1958/8-1/pjm-v8-n1-p14-s.pdf).

**Compactness alone does not justify equality.** For a compact nonconvex set, linear minimization is unchanged by taking its convex hull, so
\[
\max_\lambda h(p,\lambda)=J_{\operatorname{conv}\mathcal E}(p)
\le J_{\mathcal E}(p).
\]
Thus the mixture expression remains valid but may discard useful nonconvex information. In practice a proven convex polyhedral outer set makes the joint epigraph problem an LP; this observation does not establish that solving it is cheap for the actual fleet dimensions.

## 3. Exact strict improvement, without computation

Take \(\mathcal E=[0,1]\), cached \((p_1,\ell_1)=(0,0)\), \((p_2,\ell_2)=(2,1)\), and query \(p=1\). Three feasible cost/load pairs are
\[
(e,c)=(0,1),\quad(1/2,0),\quad(1,0).
\]
They give \(V(0)=0\), \(V(2)=1\), so both certificates are exact, and \(V(1)=1/2\). Yet
\[
B(1)=\max\{\min_{[0,1]}z,\ 1+\min_{[0,1]}(-z)\}=0,
\]
whereas
\[
J(1)=\min_{0\le z\le1}\max\{z,1-z\}=1/2.
\]
The crossing at \(z=1/2\) proves the minimum; the mixture \(\lambda=(1/2,1/2)\) gives the same certificate. Joint reuse is strictly stronger and exact here.

For the convexity qualification, instead take \(\mathcal E=\{0,1\}\) and just pairs \((0,1),(1,0)\). The same cached values remain exact, but \(J_{\mathcal E}(1)=V(1)=1\), while the mixture maximum is \(1/2\). This is an exact minimax-gap counterexample.

## 4. Certificate invalidations and usable numerical direction

- Cached values must lower-bound the original pricing problem. Restricted-oracle bounds and feasible incumbents cannot replace \(\ell_k\). The physical set, intrinsic cost, units, efficiency, and load coordinates must match across caches.
- \(\mathcal E\) must contain every unrestricted feasible load. Observed load extrema, retained routes, or an incumbent fleet count do not prove this. Export needs signed bounds; power and interval energy need consistent conversion.
- A feasible solution of the **minimization** defining \(J\) supplies an upper bound on \(J\); it need not lower-bound \(V\). Use a certified minimization lower bound. Alternatively any feasible simplex weight supplies a valid bound through \(h\), provided its linear minimum is exact or enclosed from below. An incumbent for that linear minimization has the wrong direction too. Approximate weights must actually satisfy the simplex constraints.
- For a hull certificate subtract a valid upper enclosure of the applicable supply conjugate: \(J(p)-\widehat F^*(p)\le CH\). Floating objectives remain tolerance-qualified unless uncertainties are enclosed. A changed supply function requires its new conjugate.

There is also a direct hull relaxation **when \(\mathcal E\) is closed and convex**:
\[
R=\inf_{z\in\mathcal E,t}\{t+F(z):t+p_k^\top z\ge\ell_k\ \forall k\}\le CH.
\]
All cost/load pairs satisfy its affine inequalities; their closed convex hull also satisfies them and has loads in \(\mathcal E\). This proves the direction even with extended-valued supply feasibility. Fenchel's inequality additionally gives \(J(p)-F^*(p)\le R\) for every finite admissible price. Thus optimizing supply cost on the outer epigraph can outperform evaluation at one price. Retained complete-fleet columns provide the corresponding inner hull approximation and upper bound. This is standard cutting-plane outer approximation, not a new theorem. A certified lower bound on \(R\), rather than a minimization incumbent, is required to lower-bound \(CH\). For a nonconvex \(\mathcal E\), convexify it before asserting this hull bound.

## 5. Primary prior art and contribution assessment

Sources accessed on 2 October 2026; access scope is explicit here.

1. **Geoffrion and Nauss (1977)**, [*Parametric and Postoptimality Analysis in Integer Linear Programming*, Management Science 23(5), 453–466, DOI 10.1287/mnsc.23.5.453](https://pubsonline.informs.org/doi/10.1287/mnsc.23.5.453). Publisher metadata was verified. The indexed [author-hosted original paper](https://www.anderson.ucla.edu/faculty/art.geoffrion/home/docs/e25.pdf), p. 461, Corollary 3.3.1, explicitly strengthens valid parametric lower-bound functions using their upper concave envelope. Direct PDF extraction/rendering failed, so the inspected evidence is the indexed original-paper passage, not a complete reread. This is a close, affirmative precedent for the interpolation idea.
2. **Kiwiel and Lemaréchal (2009; online 2007)**, [*An inexact bundle variant suited to column generation*, Mathematical Programming 118, 177–206, DOI 10.1007/s10107-007-0187-4](https://link.springer.com/article/10.1007/s10107-007-0187-4). Publisher abstract and metadata inspected; full text was subscription-restricted. It already couples column generation with expensive oracles of unknown accuracy. Its specific assumptions/convergence guarantees cannot be transferred from the abstract to this fleet method.
3. **de Oliveira and Sagastizábal (2014)**, [*Level bundle methods for oracles with on-demand accuracy*, Optimization Methods and Software 29(6), 1180–1209, DOI 10.1080/10556788.2013.871282](https://doi.org/10.1080/10556788.2013.871282). Publication metadata verified on the publisher collection; the [authors' repository abstract](https://optimization-online.org/2012/03/3390/) was inspected. It controls oracle accuracy using a descent target and an error bound, with asymptotic exactness. Effort allocation between cheap estimates and expensive accurate evaluations is therefore established prior art, although this review did not inspect its full proof.

**Assessment:** the joint inequality is useful certificate bookkeeping and standard outer-epigraph/minimax mathematics. Concavity interpolation and adaptive inexact oracles already have primary precedents. No novelty follows from failing to find this exact fleet notation. A credible fleet-specific component would require a proven inexpensive load relaxation and evidence that it changes time to certified economic/regret accuracy, against separate caches, retained columns, warmstarted full pricing, and inexact/stabilized methods at equal total effort.

## 6. Conditional fleet energy facets

A derivable starting point is a correctly accounted aggregate battery balance. Suppose every schedule satisfies
\[
B_H-B_0=\sum_t\eta_t e_t-W,
\]
with nonnegative grid purchases, fixed charge efficiencies, total battery-side withdrawal \(W\ge W_{\min}\), and a proven boundary bound \(B_H-B_0\ge\delta_{\min}\). Then
\[
\sum_t\eta_t e_t\ge W_{\min}+\delta_{\min}
\]
is a valid outer facet. With replenishment \(B_H\ge B_0\), \(W_{\min}>0\), and \(\eta_t\le\eta_{\max}\), also \(\sum_te_t\ge W_{\min}/\eta_{\max}\). The same telescoping argument gives prefix facets when corresponding withdrawal/battery boundary bounds are proved. Charging opportunities and aggregate storage bounds may yield upper facets.

These are conditional deductions, not established EGG facts. Variable fleet membership, free initial charge, route-dependent deadhead, regeneration, export, losses, and charging/discharging conventions must be represented in the balance and uniform bounds. A service-energy total alone does not prove purchased-energy equality. Whether such facets tighten joint certificates enough to justify their construction and evaluation cost is an untested hypothesis.
