# What the fleet solver can supply to an inexact bundle method

2 October 2026. Algebraic interface check; no optimizer, data or cluster access. This is standard convex-analysis bookkeeping, not a new convergence theorem.

Let \(V(p)=\inf_{x\in X}\{c(x)+p^Te(x)\}\), and minimize the convex negative dual \(f(p)=F^*(p)-V(p)\). At the queried price \(p\), assume finite values, a replay-valid fleet \(x\), and a valid unrestricted lower bound
\[
\ell\le V(p)\le v:=c(x)+p^Te(x).
\]
Also assume \(g\in\partial F^*(p)\) exists. With \(\varepsilon=v-\ell\ge0\), the solver provides
\[
F^*(p)-v\le f(p)\le F^*(p)-\ell,
\quad d=g-e(x).
\]
For every price \(p'\) in the finite-value domain, the candidate fleet gives
\(V(p')\le v+e(x)^T(p'-p)\). Combine this with the subgradient inequality for \(F^*\) to obtain
\[
f(p')\ge f(p)+d^T(p'-p)-\varepsilon.
\]
Thus \(d\) is an \(\varepsilon\)-subgradient, with a measurable upper bound on its error. A price-dependent restricted-model lower bound cannot replace \(\ell\).

## Valid cuts do not require an exact fleet response

The composite minorant
\[
M_x(p')=F^*(p')-c(x)-p'^Te(x)\le f(p')
\]
is globally valid even if the candidate is poor. Linearizing the known supply term at \(p\) also gives the affine minorant
\[
A_p(p')=F^*(p)-v+[g-e(x)]^T(p'-p)\le f(p').
\]
At the query, their gap below \(f\) is \(v-V(p)\le\varepsilon\). Learned restrictions can therefore generate valid cuts from feasible fleets; they do not automatically provide the error control needed by a bundle algorithm. Global pricing bounds, or valid cached bounds at the same query, can provide that control. Retain the strongest compatible lower bound and best response value; if their ordering fails, treat it as an inconsistency.

## Approximate supply calculations require their own guarantees

If only certified conjugate bounds \(F_L^*\le F^*(p)\le F_U^*\) are available, the value bracket becomes
\[
F_L^*-v\le f(p)\le F_U^*-\ell.
\]
Its width is \((F_U^*-F_L^*)+(v-\ell)\). This does not certify a numerical gradient. If \(\widetilde g\) is separately proved to be a supply \(\varepsilon_s\)-subgradient, the combined direction is an \((v-\ell+\varepsilon_s)\)-subgradient. Without that proof, neither the affine cut nor a bundle theorem follows from an accurate conjugate value alone.

For example, take \(F^*\equiv0\) and \(V\equiv0\) on \(\mathbb R\). Values are exact, but using \(\widetilde g=1\) would require \(0\ge p'-p-\varepsilon\) for all \(p'\), impossible for any finite \(\varepsilon\). A bounded price domain and a verified gradient-error bound can support an appropriate uniform error allowance; unconstrained prices cannot be handled that way.

## Allocation and stopping consequences

An alternative mapping matches a constraint-pricing interface. Introduce \(\alpha\) and minimize \(F^*(p)-\alpha\) subject to the convex constraint \(g(p,\alpha)=\alpha-V(p)\le0\). A feasible fleet supplies the global affine minorant \(\alpha-c(x)-p^Te(x)\); the oracle bracket is \(\alpha-v\le g\le\alpha-\ell\). Given a finite compatible price \(p_0\) and certified \(\ell_0\le V(p_0)\), choosing \(\alpha_0=\ell_0-\delta\), \(\delta>0\), gives a strict margin \(g(p_0,\alpha_0)\le-\delta\). This constructs a Slater point for this constraint when the point also belongs to the required base domain and has finite objective. It does not establish the rest of Kiwiel–Lemaréchal's algorithmic or convergence assumptions; those remain a separate mapping task.

The interval width separates two possible tasks: improve \(v\) through cheap feasible proposals, or improve \(\ell\) through global bounds. It does not predict which task has the better gain per second. A time limit does not guarantee that either task attains a requested \(\varepsilon\); an unresolved oracle request must stay unresolved when the budget expires.

An implementable interface can record target status and accuracy status separately. For a fixed queried price and a convex-objective target \(\tau\), a certified upper value \(f_U\le\tau\) proves target attainment there; a certified lower value \(f_L>\tau\) rejects it **at that price only**; a bracket straddling \(\tau\) is unresolved. Independently, the value-accuracy request \(\epsilon_{\rm req}\) is met when \(f_U-f_L\le\epsilon_{\rm req}\). Target attainment can precede sufficient accuracy. None of these tests rejects a target globally over all prices. This is a proposed bound-based interface, not a transcription of either published algorithm.

Small oracle error at one price is not a small global optimization gap. Final economic certification still uses independently valid hull upper/lower bounds, with consistent nonnegative width and explicit numerical margins. Convergence claims additionally require the chosen method's model, domain, accuracy and iteration assumptions; a finite-budget scheduling heuristic inherits none automatically. The companion primary-source notes determine which published oracle contracts match this interface.
