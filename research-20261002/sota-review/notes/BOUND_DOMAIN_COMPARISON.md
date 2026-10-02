# Which relaxation bounds which object?

2 October 2026. Part of the aggregate-load structure review; no experiments or data inspection. The distinctions below are deductions for the proposed EGG method, not a claim of new approximation theory.

## A directly relevant electric-bus precedent

Marelot de Vos, Rolf van Lieshout and Twan Dollevoet, **Electric Vehicle Scheduling in Public Transit with Capacitated Charging Stations**, *Transportation Science* 58(2), 279–294 (2024), DOI [10.1287/trsc.2022.0253](https://doi.org/10.1287/trsc.2022.0253). Journal metadata and final abstract were verified on the [authors' institutional record](https://research.tue.nl/en/publications/electric-vehicle-scheduling-in-public-transit-with-capacitated-ch/). The final PDF timed out; the relevant methods were inspected in the [2022 author preprint, §§4.2.1–4.2.3](https://arxiv.org/html/2207.13734v2), whose title and experimental results differ from the published record.

That preprint separates a conservative time/SOC network for feasible duties from an optimistic network for lower bounds. It explicitly warns that a lower bound for the conservative discretization need not bound the underlying problem. The optimistic network includes a representation of every original duty; feasible-schedule generation and certification therefore use different networks. This is an important precedent for EGG's separation of proposals and bounds. Its flat operational cost model and endpoint conditions cannot be imported unchanged into EGG's price-dependent oracle.

## Mapping feasibility alone is not enough when prices change

For an alternative pricing relaxation \(Y\) to certify \(V(p)\), establish for every original fleet \(x\) a representation \(y\in Y\) with
\[
c_Y(y)+p^Te_Y(y)\le c(x)+p^Te(x).
\]
If the mapping preserves the grid-load vector and never increases intrinsic cost, this holds for every price. If it shifts charging between times or changes purchased energy, it needs an additional objective-direction proof for the whole allowed price domain. An optimistic SOC rounding rule alone supplies no such proof. In particular, moving load from a low-price interval to a higher-price interval can invalidate the comparison even when all prices are positive. Negative prices require further care if the construction deletes energy purchases.

For a single mapping independent of \(p\), unequal load vectors cannot support this inequality over all \(\mathbb R^T\) with only a finite intrinsic-cost offset: choose a large price vector in the direction of their difference. This does not rule out price-dependent mappings or a restricted price domain; it states what those alternatives must prove.

## Three domains, three different conclusions

| Construction | Valid use after proving the stated mapping | Missing implication |
|---|---|---|
| Restricted graph or conservative duty set | Replayed complete fleets give physical and hull upper bounds | Its minimization lower bound does not bound the full fleet oracle |
| Aggregate load/cost outer model | Global pricing lower bound; a convex outer cost/load model also bounds the complete-fleet hull | An aggregate load need not disaggregate into executable buses |
| Route-column LP with shared-resource constraints | A pricing relaxation if every original fleet has a cost-valid representation | It need not equal the convex hull of complete coupled fleets |

The comparison baseline matters. Energy-balance and occupancy inequalities implied by the original continuous relaxation cannot strengthen its exact projection merely by being written separately. Their prospective benefit is a small reusable model evaluated across many prices, possibly enriched by complete-fleet oracle certificates. Compare construction plus repeated-query cost against a warmstarted full relaxation; do not call the aggregate model stronger without proving that claim.
