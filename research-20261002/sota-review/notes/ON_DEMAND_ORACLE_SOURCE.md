# On-demand oracle source audit

Status: bounded access audit, 2 October 2026. **Full primary text not obtained; source gap remains open.** This note does not upgrade the review to theorem-verified coverage.

## Sources, access and version limits

Requested work: W. de Oliveira and C. Sagastizábal, *Level bundle methods for oracles with on-demand accuracy*, Optimization Methods and Software 29(6), 1180–1209 (2014), [DOI 10.1080/10556788.2013.871282](https://doi.org/10.1080/10556788.2013.871282).

Three substantive access routes were investigated, without downloading papers or expanding the literature search:

1. [Optimization Online author deposit](https://optimization-online.org/2012/03/3390/): accessible abstract and metadata, dated published 15 March 2012 / updated 4 November 2013. The rendered page exposes no manuscript download. Its citation still says forthcoming in 2013, so it is not evidence of the final journal text.
2. A title-specific web discovery search returned the [publisher article page](https://www.tandfonline.com/doi/full/10.1080/10556788.2013.871282), indexed as “Get Access,” with abstract and publication metadata rather than theorem text. It lists accepted author version 9 December 2013 and publication online 14 February 2014. Search also surfaced a ResearchGate manuscript extract labelled version 25 November 2012; that extract was not inspected as a complete primary manuscript and is not used to establish equations or convergence conditions.
3. [Coauthor's publications page](https://www.ime.unicamp.br/~sagastiz/publications/), entry “Level bundle methods for oracles with on-demand accuracy” under the 2014 publications: accessible author abstract and DOI link, with no PDF link for this entry. Reading that entry completed this route; no additional access route was pursued.

Consequently, exact section, algorithm, equation and theorem numbers, signed error conventions, termination thresholds and regularity assumptions remain **unverified**. The statements below distinguish author-abstract evidence from implementation implications.

## What the primary author abstracts establish

The setting is nonsmooth convex minimization. An oracle evaluates a feasible point and supplies objective and subgradient information. Exact information is computable but costly. Calls additionally receive a descent target and an inexactness bound. Reaching the target with the function estimate requires the associated error to satisfy the requested bound; if the oracle determines the target cannot be reached, estimates may be rough with unknown accuracy. This is a conditional accuracy contract, not a claim that every call must be solved exactly.

The coauthor's abstract specifically says requested accuracy tends to zero at selected iterates, yielding asymptotic exact solution. It also restricts the stated agreement with exact-method convergence rates to some variants on compact feasible sets. Neither statement proves that an arbitrary adaptive allocation scheme has those properties. The accessible material does not specify what counts as target detection, whether returned errors are explicit, which subsequence must become accurate, or all hypotheses of the convergence results.

## Implementable implications for the proposed EGG pilot

These are design deductions, not assertions that the existing protocol implements the paper's algorithms. A useful oracle interface would pass a point, an objective target and an absolute requested error; return validated bounds, a candidate/cut and a classification of certified target attainment, certified target rejection, or unresolved budget exhaustion. The outer method should control refinement using observed certified uncertainty and retain reliable information across calls. Serious/descent decisions must account for estimation error. A theorem-faithful implementation would additionally require the full paper's cut validity, level construction, projection/stability-center updates, bundle maintenance and accuracy-refinement rules before claiming convergence.

For EGG's convex price objective, mapping requires particular care with signs and domains. A replay-valid complete fleet provides an affine upper model of the concave pricing value V(p), hence an affine lower model of −V(p). An unrestricted pricing enclosure ell(p) ≤ V(p) ≤ u(p) gives an error bound u(p)−ell(p) for that candidate model at the queried price. Adding F*(p) needs its own verified value/subgradient treatment; an upper enclosure sufficient for a hull lower bound does not by itself supply every oracle quantity required by a bundle theorem. Restricted candidate search alone supplies no global pricing error bound.

The [matched oracle protocol](../protocols/MATCHED_ORACLE_PROTOCOL.md) already distinguishes candidate generation from global certification, preserves best valid L/U, and requires stopping on a validated nonnegative hull width. Those are compatible practical ingredients, but its finite solver allowances and wall-clock cap permit unresolved calls. A timeout does not establish target rejection or requested accuracy. Increasing time allowances does not prove shrinking error on the required iterates. A finite run does not establish asymptotic convergence, and hull enclosure width is not automatically the paper's level-model stopping quantity. Arbitrary prices do not establish compactness, bounded subgradients or existence of a minimizer.

Use this paper as motivation for certification-driven adaptive effort. Do not attribute its convergence guarantees, rate, exact stopping criterion or precise oracle assumptions to the pilot until a complete primary version is inspected and the mapping is proved. No solves, training, cluster work or protected data access occurred in this audit.
