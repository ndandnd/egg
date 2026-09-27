# Independent review: quadratic radius-dependent regret bound

**Verdict: PASS under the stated finite-dimensional compactness and differentiability assumptions.** The identity and regret inequality in QUADRATIC_REGRET_RADIUS_DERIVATION_20260927.md are correct for singular as well as positive-definite \(B\succeq0\). The result needs no interior-load or supplier-conjugate assumption. Its stated scope should remain a single complete-fleet opportunity set with one common intrinsic cost/load pair model.

## Check of the argument

Write a physical pair as \(y=(c,L)\in K\), where \(K\subset\mathbb R\times\mathbb R^m\) is compact, and let \(y^*=(c^*,L^*)\) minimize \(c+F(L)\) on \(\operatorname{conv}K\). For \(p^*=a+BL^*\), differentiability and convex first-order optimality on that convex hull give

\[
c+p^*\cdot L\ \geq\ c^*+p^*\cdot L^*\qquad((c,L)\in\operatorname{conv}K).
\]

Thus the minimum of this linear private objective over physical schedules equals its value at \(y^*\): a linear functional has the same minimum on \(K\) and \(\operatorname{conv}K\), and the inequality gives the reverse comparison. In particular, \(V(p^*)=c^*+p^*\cdot L^*\).

For any physical schedule \(s\), put \(H=c(s)+F(L(s))-CH\), \(d=\|L(s)-L^*\|_B\), and \(R_B=\max_{u,v\in S}\|L(u)-L(v)\|_B\). The quadratic identity gives

\[
\mathrm{LOC}(s;p^*)=c(s)+p^*\cdot L(s)-V(p^*)=H-\tfrac12d^2\geq0,
\]

so \(d\leq\sqrt{2H}\). Let \(t\) minimize \(c(t)+p_s\cdot L(t)\), with \(p_s=a+BL(s)\). Compactness ensures this response exists. Since \(c(t)+p^*\cdot L(t)\geq V(p^*)\),

\[
\begin{aligned}
r(s;p_s)
&\leq \mathrm{LOC}(s;p^*)+(L(s)-L^*)^TB(L(s)-L(t))\\
&\leq H-\tfrac12d^2+dR_B\\
&\leq H+\sqrt{2H}\,R_B.
\end{aligned}
\]

The second line uses Cauchy–Schwarz after applying the symmetric PSD square root \(B^{1/2}\). That proof works when \(B\) is singular: \(\|\cdot\|_B\) is a seminorm, no inverse is used, and the square-root map also handles directions in its kernel. For every physical planner optimizer \(s\), \(H=\Delta\), yielding the proposed bound. For a nonoptimal physical schedule the correct quantity is its excess \(H(s)=c(s)+F(L(s))-CH\), not the global gap alone.

## Attainment, boundary, and scope

The relevant compactness requirement is that the finite-dimensional physical cost/load image \(K\) be compact. Then its convex hull is compact, the relaxed optimum is attained, the private response minimum is attained, and \(R_B\) is finite and attained. A continuous charging decision or other continuous physical choices do not change the proof. If the cost/load image is noncompact, the stated proof may lose one or more attained minimizers and a finite diameter; an infimum-only replacement needs additional hypotheses and is outside this result.

At a nonnegative-load boundary, the gradient is valid because this is a globally differentiable quadratic (or, more generally, because a differentiable convex extension exists on a neighborhood of the hull). The first-order inequality is only applied along feasible hull directions; no interior optimizer is needed. The proof itself never forms the supplier conjugate or requires \(p^*\) to support an unconstrained supplier optimum. With the stated quadratic restricted to \(L\geq0\), its conjugate is also finite at these gradient prices: completing the square gives a finite maximum, attained at \(L^*\) for \(p^*\) and at \(L(s)\) for \(p_s\). But that fact is not needed for the regret bound.

If \(\Delta=0\) at a physical optimum, the identity forces \(d=0\) and \(\mathrm{LOC}(s;p^*)=0\). Hence \(p_s=p^*\) and \(r(s;p_s)=0\). This agrees with the zero-gap support result; it is not an exceptional failure of the square-root bound. Conversely, the inequality does not claim regret is determined by the gap alone: the physical load diameter in the \(B\)-seminorm also matters.

## Optional sharpening

Retaining the negative quadratic term and maximizing over \(0\leq d\leq\sqrt{2H}\) yields the valid sharper envelope

\[
r(s;p_s)\leq
\begin{cases}
H+R_B^2/2,&R_B\leq\sqrt{2H},\\
\sqrt{2H}\,R_B,&R_B\geq\sqrt{2H}.
\end{cases}
\]

This is simply the maximum of \(H-d^2/2+dR_B\) on that interval. The derivation's simpler \(H+\sqrt{2H}R_B\) bound is also correct and is easier to state. In the cited cyclic replication, \(R_B=\sqrt{40n}\), \(d=\sqrt{2\Delta}\), and the second branch gives \(40|\delta|\), consistent with the archived exact regret calculations. This is an upper bound, not a claim that the diameter term is tight.

## Interpretation limit

The \(O(1/n)\) gap together with an \(O(\sqrt n)\) load diameter permits an \(O(1)\) whole-fleet upper bound, so it does not contradict the replicated example's nonvanishing whole-operator regret. A bounded participant-specific radius can give a different normalization only after the opportunity set and reserved-resource rights for that participant have been specified. Nothing here extends automatically to unreserved independently owned fleets, strategic market power, or a general shared-charger game.
