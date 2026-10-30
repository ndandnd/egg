# Theory and averaging check (29 September 2026)

## Decision

The proposed upgrade is valid **for the exact two-service quadratic replay**, with a short model-specific proof. Cite the primal-recovery literature as context; do not say that either named paper directly proves convergence for this run. The replay uses \(\alpha_k=0.5/\sqrt{k}\), hence \(\sum_k\alpha_k=\infty\), \(\alpha_k\to0\), but \(\sum_k\alpha_k^2=\infty\). Larsson–Patriksson–Strömberg (1999) study ergodic recovery for convex Lagrangian programs; their step-weighted theorem relies on dual-iterate convergence, and their standard dual-convergence hypotheses are summarized with square-summable steps in the later open primary paper by Gustavsson–Patriksson–Strömberg (2015, Proposition 3 and Theorem 1). Anstreicher–Wolsey (2009) explicitly restrict the *primal-estimate* result in their publisher abstract to Lagrangian duals of **linear programs**. Full text for the 1999 and 2009 papers was unavailable through the publisher; the 2015 article is fully open and verifies the step assumptions. No stronger theorem claim should be attributed to the paywalled texts. [1999 publisher record](https://doi.org/10.1007/s101070050090); [2009 publisher record](https://doi.org/10.1007/s10107-007-0148-y); [2015 full open article](https://doi.org/10.1007/s10107-014-0772-2).

## Tailored proof for the plotted replay

Let \(A_K=\sum_{k=1}^K\alpha_k\), \(\bar e_K=A_K^{-1}\sum_{k=1}^K\alpha_ke(x_k)\), and \(\bar c_K=A_K^{-1}\sum_{k=1}^K\alpha_kc(x_k)\). The exact example has \(0\le e_E(x_k)\le10\), \(20\le e_L(x_k)\le30\), and supply oracle
\[
s(p)=\bigl(5[p_E-4]_+,\;5[p_L]_+\bigr).
\]
For \(k\ge7\), \(5\alpha_k<1\). If \(p_{E,k}\ge4\), its unprojected successor is a convex combination of \(p_{E,k}\) and \(4+e_E(x_k)/5\le6\); if \(p_{E,k}<4\), its successor is below \(4+10\alpha_k<6\). The late-terminal coordinate is a convex combination of \(p_{L,k}\) and \(e_L(x_k)/5\le6\). The first six iterates are finite, so the entire projected price sequence and all supergradients are bounded despite \(P=\mathbb R_+^2\) being unbounded.

In fact the same coordinate argument shows the projection is **inactive for every \(k\ge7\)**: all late unprojected successors are nonnegative. Put \(d_k=e(x_k)-s(p_k)\) and \(S_K=\sum_{k=7}^K\alpha_k\). Then
\[
\frac1{S_K}\sum_{k=7}^K\alpha_kd_k
=\frac{p_{K+1}-p_7}{S_K}\longrightarrow0,
\qquad
\frac1{S_K}\sum_{k=7}^K\alpha_kp_k^\top d_k
=\frac{\|p_{K+1}\|^2-\|p_7\|^2-\sum_{k=7}^K\alpha_k^2\|d_k\|^2}{2S_K}\longrightarrow0.
\]
Both limits use bounded prices/oracles, \(S_K\asymp\sqrt K\), and \(\sum_{k\le K}\alpha_k^2=O(\log K)\). The finite prefix has vanishing weight. With the attained dual price \(p^*=(107/20,93/20)\), the standard projection inequality gives
\[
0\le \frac1{A_K}\sum_{k=1}^K\alpha_k[CH-Q(p_k)]
\le\frac{\|p_1-p^*\|^2+M^2\sum_{k=1}^K\alpha_k^2}{2A_K}\longrightarrow0.
\]
The exact-oracle identity \(c(x_k)+F(s(p_k))=Q(p_k)-p_k^\top d_k\) therefore implies that the step-weighted mean of \(c(x_k)+F(s(p_k))\) tends to \(CH\). Jensen gives \(\bar c_K+F(\bar s_K)\le A_K^{-1}\sum\alpha_k[c(x_k)+F(s(p_k))]\). The load mismatch above tends to zero, and quadratic \(F\) is uniformly continuous on the bounded loads here. Hence \(CH\le\bar c_K+F(\bar e_K)\le CH+o(1)\). Compactness and the **unique** complete-hull optimizer \((e^*,c^*)=((27/4,93/4),371/40)\) force \((\bar e_K,\bar c_K)\to(e^*,c^*)\). Every fleet response has intrinsic cost 7 (one bus) or 14 (two buses), so \(\bar c_K=14-7\times\)(step-weighted one-bus frequency), which tends to \(371/40\). Thus the **step-weighted one-bus frequency tends to \(27/40=0.675\)**. Both bus-count responses occur infinitely often. This argument does not need convergence of individual prices or physical loads, and it gives no finite-\(K\) error bound for the reported 0.6603 frequency at 20,000 calls. The averaged point is in the convexified fleet set and is generally not an executable one-day schedule.

Suggested minimal insertion after the replay numbers: “For this quadratic example, the step-weighted averages of exact fleet responses converge to the unique hull optimizer: their mean early load tends to \(27/4\), and their one-bus weight tends to \(27/40\). To see this, the supply response is \(s(p)=(5[p_E-4]_+,5[p_L]_+)\). With the stated steps, prices and oracle responses stay bounded and projection is inactive from the seventh update onward. The summed updates make weighted fleet–supply imbalance vanish; the dual projection bound, the update norm identity, and convexity then make the averaged hull cost tend to \(CH\). This convexified average need not be a physical daily fleet. Classical ergodic-primal-recovery papers provide context [cite Larsson et al. 1999; Gustavsson et al. 2015]; the argument here establishes the claim for the displayed \(0.5/\sqrt{k}\) replay.” Anstreicher–Wolsey can remain in a source note, since its primal-estimate result is LP-specific.

## Corollary and scaling check

The new corollary and proof in `model_theory.tex` and `proof_appendix.tex` are correct: if \(e(x)=e^*\) for a hull optimizer and strong duality attains \(p^*\), the two nonnegative Lagrangian/Fenchel slacks at \((e^*,c^*)\) vanish. Hence \(p^*\in\partial F(e(x))\), \(V(p^*)=c^*+(p^*)^\top e^*\), and \(r(x;p^*)=c(x)-c^*=H(x)\). The existing lower bound gives \(r(x;p)\ge H(x)\) for every \(p\in\partial F(e(x))\). For a restricted **marginal-price** set \(P_x\subseteq\partial F(e(x))\), equality requires that it contain an attained hull-dual price; if it excludes all such prices, the exact minimum statement does not follow. If “admissible prices” allows nonmarginal prices, even the lower bound can fail. In the nominal \(n=1\) example, the hull-optimal load \((27/4,93/4)\) **is** physical on the continuous two-bus branch, with cost 14; the corollary gives \(H=r=14-371/40=189/40\) there. It does not apply to the physical planner optimum at load \((10,20)\).

In the replicated family, the exact formulas imply \(0\le\Delta_n\le5/n\), while along \(n=40k+1\) the absolute whole-operator regret tends to \(351/40>0\); per-pair regret under separately reserved connectors is at most \(20/n\). Thus the family has \(O(1/n)\) gap and \(O(1)\) aggregate regret on that subsequence. The Shapley–Folkman lemma concerns Minkowski sums of **separate participant sets in fixed dimension**, leaving at most the dimension's number of summands convexified; a uniform \(O(1)\) objective-gap corollary additionally needs bounded participant nonconvexities and suitable coupling/regularity. It does **not** bound this whole operator's own-price regret. Hreinsson et al.'s publisher abstract supports approximate convexity of aggregated demand action/cost sets, not this paper's exact rate or regret bound. Bi–Tang give explicit fixed-dimension duality-gap bounds for separable problems with bounded domains/finite nonconvexity; their assumptions should not silently be transferred to shared-charger fleets. [Hreinsson et al.](https://doi.org/10.1109/TPWRS.2021.3065913); [Bi–Tang preprint, Theorem 1 and §4](https://arxiv.org/html/1610.05416v3).

Suggested paragraph: “Shapley–Folkman results explain why sums of many bounded, separate participants can have small *relative* nonconvexity when the coupling dimension is fixed [cite Hreinsson et al.; Bi and Tang]. The present family's stronger \(\Delta_n\le5/n\) follows from its explicit quadratic geometry and integer rounding. Along \(n=40k+1\), the same physical optima have whole-operator own-price regret tending to \(351/40\), because the deviator controls all \(n\) pairs. If each pair instead has a reserved early and terminal connector, its individual regret is at most \(20/n\). This vanishing individual incentive is analogous to the price-taking large-population flow perspective of Alizadeh et al.; it does not identify our reserved-pair model with their traffic and power network equilibrium.” Alizadeh et al. explicitly model a large population of **privately owned EVs**, not a composite fleet, and use class path-flow variables and dual decomposition (their §IV–V, Proposition V.1). [Author-hosted published PDF](https://web.ece.ucsb.edu/Faculty/selected_pubs/Alizadeh-mp/1.pdf).

## Verified BibTeX additions / existing entries

```bibtex
@article{larssonPatrikssonStromberg1999,
  author = {Larsson, Torbj{"o}rn and Patriksson, Michael and Str{"o}mberg, Ann-Brith},
  title = {Ergodic, Primal Convergence in Dual Subgradient Schemes for Convex Programming},
  journal = {Mathematical Programming}, volume = {86}, number = {2},
  pages = {283--312}, year = {1999}, doi = {10.1007/s101070050090}
}
@article{anstreicherWolsey2009,
  author = {Anstreicher, Kurt M. and Wolsey, Laurence A.},
  title = {Two ``Well-Known'' Properties of Subgradient Optimization},
  journal = {Mathematical Programming}, volume = {120}, number = {1},
  pages = {213--220}, year = {2009}, doi = {10.1007/s10107-007-0148-y}
}
```

The manuscript already has verified entries for `hreinsson2021` and `alizadeh2016coupled` (the latter's journal issue is **2017**, though its DOI and preprint date are 2016). Its `related-work/references.bib` already contains Bi–Tang. If citing the 2015 open paper for explicit hypotheses, add Gustavsson, Patriksson and Strömberg, *Mathematical Programming* **150**, 365–390 (2015), DOI [10.1007/s10107-014-0772-2](https://doi.org/10.1007/s10107-014-0772-2).

## Final manuscript transcription check

Read-only check of the new `proof_appendix.tex` §A.1, the averaging paragraph in `generation_dispatch.tex`, and the new replication/participant-scale paragraphs in `exact_results.tex`: **no mathematical or scope error found**. In §A.1 the coordinate updates do make projection inactive for every update from \(k=7\), the two telescoping identities have the correct signs, and the weighted dual-gap bound, Jensen step, and compact unique-hull conclusion are valid. The cost coordinate \(371/40\) yields the stated one-bus limit \(27/40\). An interior limiting weight forces both bus counts to appear infinitely often, hence infinitely many bus-count switches. The main text confines this conclusion to the exact replay. The replication text keeps \(O(1/n)\) planning gap and persistent \(O(1)\) whole-operator regret specific to the family, states the reserved-pair opportunity set, and labels the Alizadeh connection an analogy. No additional claim or correction is needed.
