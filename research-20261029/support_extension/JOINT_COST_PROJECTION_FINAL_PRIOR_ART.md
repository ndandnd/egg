# Final bounded joint-cost projection falsification check

Outcome: **a substantive cost-aggregation overlap was verified; direct subsumption of the narrow assignment-dependent matching reduction was NOT established. Novelty remains un-cleared.** Read current related_work.tex and ASSIGNMENT_PROJECTION_TARGETED_PRIOR_ART.md before searching. Exactly four targeted queries and three new primary works were considered. No Al Taha/Mukhi/Wu refetch, blocked SSRN/MDPI retry, broad citation expansion, code, data, certificate work or manuscript edit followed.

## Exact search boundary

1. `"electric vehicle" aggregation "fleet size" "polytope" cost`
2. `"flexibility" "aggregation" "assignment" "cost" exact projection fleet`
3. `"electric vehicles" "aggregate" "optional" "convex hull" cost`
4. `"Aggregation and Disaggregation of Energetic Flexibility" cost PDF`

Queries1–3 were batched, then query4 targeted the strongest cost-aggregation lead. Only direct primary pages/author PDFs for the following three works were pursued. A blocked route was not repeatedly retried; the accessible arXiv author version below is a separate primary route to the same work. Unrelated airline, ML-assignment and secondary EV summaries were not used as evidence of theorem overlap.

## Strongest verified overlap: explicit aggregation of costs

Fabian L. Müller, Jácint Szabó, Olle Sundström and John Lygeros, *Aggregation and Disaggregation of Energetic Flexibility from Distributed Energy Resources*, IEEE Transactions on Smart Grid10(2),1205–1214, DOI10.1109/TSG.2017.2761439. The inspected primary full text is the [2017 author preprint](https://arxiv.org/pdf/1705.02815); [publisher metadata](https://doi.org/10.1109/TSG.2017.2761439) confirms the later journal record. The ETH route returned403.

Sections IV–V fix a population of resource sets. Equations(12)–(13) retain flexibility costs and optimize disaggregation; (14)–(16) construct separable piecewise-linear convex aggregate cost by minimizing individual costs under aggregate-generator equality and box limits. Equation(17) uses that cost in aggregate optimization. Exactness here is conditional on the stated zonotope/common-generator and separable-cost representation, not arbitrary original resource polytopes. The inspected formulation fixes the resource index set; it does not establish endogenous service pairing or a minimum-cardinality-matching replacement theorem. **Cost-aware aggregate representation and economically optimal disaggregation are therefore established overlap, not defensible broad novelty claims for our draft.**

## Other two primary works and access limits

**Lilliu, Brusokas and Pedersen (2024), *Device-independent metrics for explicit, a priori measurement of energy flexibility*, ACM e-Energy2024, DOI10.1145/3632775.3661965.** Inspected the [primary publisher-version PDF in Aalborg's repository](https://vbn.aau.dk/ws/portalfiles/portal/752531538/3632775.3661965.pdf), particularly Section2.2's offer lifecycle and Section4.2's set-based definitions. Offer acceptance precedes aggregation/scheduling, and lossless aggregation is defined by both sum inclusion and disaggregation inclusion. The visible mathematical target is flexibility measurement/metrics for supplied offers. This provides positive optional-acceptance context, but no verified joint service-to-vehicle assignment, paid-fleet layers or scalar matching-statistic projection. The word “assignment” in a metric is not by itself a vehicle-assignment theorem.

**Gao et al. (2024), *Aggregation formulation for on-site multidepot vehicle scheduling scenario*, DOI10.1111/mice.13217.** The [primary publisher record](https://onlinelibrary.wiley.com/doi/10.1111/mice.13217) was search-indexed with discussion of connection/network aggregation and set-partitioning/shortest-path cost structure. Direct opening timed out; full mathematical formulation/theorem access is **UNKNOWN**. No conclusion about exact energy/cost projection, endogenous charging flexibility or the minimum-requirement statistic can be drawn from that preview. It is a relevant scheduling-aggregation lead, not a demonstrated subsumption or verified exclusion.

## Effect on the narrow claim

Version precision: the consumed primary PDF explicitly prints
`arXiv:1705.02815v1 [cs.SY] 8 May 2017` on its first line. The bibliography
therefore pins version1 rather than inferring a version from an unversioned
URL. This records the original read, not a new fetch or audit.

This review falsifies a broader framing that existing aggregate flexibility descriptions omit costs or cannot support cost-optimal disaggregation. Current comparison should explicitly recognize that cost aggregation itself is established. An aggregate *minimum-cost value function* and our complete joint load/cost layers are different mathematical objects, but that difference alone does not establish significance: ordinary c+F and tariff-response optimization already asks for the lower cost envelope.

The remaining precise candidate contribution is physical: an endogenous partial service matching changes fleet size and battery-exchange boxes, yet one minimum summed positive requirement per cardinality contains the FULL purchase/export polygon of every other matching, with individual SOC-feasible finite serial realization under common windows/losses/shared occupancy. The cost coordinate survives those assignment-created alternatives. Neither an operational MILP with costs nor prescribed-resource cost aggregation automatically proves that replacement statement. Conversely, an uninspected scheduling/resource-allocation theorem could still subsume it. The stronger paper should state that theorem and its restrictive action law, not rely on “cost-labelled aggregation” as a novelty slogan.

No direct theorem subsumption was verified within these bounds, but this is not evidence that no such theorem exists, a first-result claim or a clearance across optimization literature. Gao's full formulation and the previously documented inaccessible leads remain unresolved. The paper's generic convexification, matching, time-sharing, finite-generator and pricing tools remain classical regardless of this search outcome. This bounded task is now stopped; it authorizes no additional survey or access loop.
