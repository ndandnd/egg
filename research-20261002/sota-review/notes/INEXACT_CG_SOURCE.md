# Kiwiel–Lemaréchal: primary-source gap closure

2 October 2026. Literature and algebra only; no optimization, cluster, model code, or evaluation-data access.

## Access and version

Retrieved the full institutional [RCIN PDF](https://rcin.org.pl/Content/139759/PDF/RB-2007-72.pdf), linked from the [Systems Research Institute repository record](https://rcin.org.pl/dlibra/publication/175229/edition/139759). The record identifies research report RB/72/2007. The 36-page scan contains institutional covers followed by a 30-page Springer-layout paper bearing the requested DOI, both authors, acceptance date 7 August 2007, and Springer copyright 2007. Thus this is an institutional deposit containing publication-layout text, not merely an abstract or the earlier October 2006 “Conic” draft. It was not compared byte-for-byte with the [final journal issue](https://doi.org/10.1007/s10107-007-0187-4), Mathematical Programming 118, 177–206 (2009).

Bounded access sequence: (1) targeted title search, (2) institutional PDF retrieval and targeted section reads, (3) direct download attempt. Web extraction succeeded; screenshot rendering failed and shell download failed DNS resolution. Equations missing from scan OCR are not represented as visually verified transcriptions below. References use printed section/equation numbers; PDF pages are zero-based when specified.

## Verified technical substance

Section 1 assumes a simple closed convex set, convex real-valued objective/constraint, and an available strict Slater point. Oracle values underestimate the constraint; associated approximate subgradients generate globally valid affine minorants (§1, (1.3)–(1.7)). Proposition 3.1 permits any actual LP column, not necessarily the maximizing column.

Noise need not vanish. Interpolation toward Slater controls center feasibility (Lemma 2.1). Increasing the proximal stepsize attenuates noise (§2.2; Algorithm 4.1). Better accuracy matters at descent steps (Remark 2.2).

Theorem 5.8 requires bounded oracle errors and neither termination nor infinite internal looping. With finite optimum it establishes a subsequence of vanishing residuals; objective limit is at most the optimum and feasibility error is bounded by asymptotic interpolation error. This is not unconditional exact feasibility/optimality. Theorem 6.2 yields approximate primal optimality with multiplier-scaled asymptotic error.

Algorithm 4.1 stops at zero residual and nonpositive δ; positive residual/δ tolerances are allowed (§4). An optimizer norm bound R gives objective excess at most δ+Rρ, alongside oracle-dependent feasibility error.

Remarks 2.3 and 3.5 explicitly use oracle upper bounds to restore certified dual feasibility and primal lower bounds via interpolation, including branch-and-bound pricing.

## EGG interpretation: conditional mathematical mapping

Using the unchanged pricing definition from JOINT_PRICE_BOUND_REVIEW.md, let a feasible complete-fleet incumbent have value U(p), and let a globally valid certificate satisfy ℓ(p)≤V(p)≤U(p). Then U(p)−ℓ(p) bounds its pricing suboptimality. Negating pricing converts this minimization interval into the maximization direction used for constraint pricing in the paper. A feasible incumbent supplies a valid column/affine function; a restricted-oracle bound cannot replace ℓ.

This is a strong precedent for pairing approximate feasible columns with global pricing certificates and stabilization. It does not establish convergence of the current EGG procedure: transferring its theorem requires a specific convex master formulation, strict Slater construction, prescribed model/aggregation and step rules, bounded errors, and control of descent/interpolation error. Nor does it establish fleet runtime improvement or novelty of cached joint price bounds. EGG’s supply conjugate, full-fleet domain, signed load coordinates, and certificate directions still require their own proofs.
