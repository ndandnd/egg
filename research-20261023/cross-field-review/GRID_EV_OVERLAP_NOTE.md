# Grid-aware EVSP: decisive prior-art check

Checked 23 October 2026. No experiments or solver execution.

**Verified reference:** Weitiao Wu, Yue Lin, Ronghui Liu, Wenzhou Jin (2022), *The multi-depot electric vehicle scheduling problem with power grid characteristics*, Transportation Research Part B: Methodological 155, 322–347. [DOI](https://doi.org/10.1016/j.trb.2021.11.007); [University of Leeds/White Rose record](https://eprints.whiterose.ac.uk/id/eprint/180812/); [accepted manuscript](https://eprints.whiterose.ac.uk/id/eprint/180812/1/Wu%20et%20al%20-%20TRB2021%20-%20EV%20scheduling%20-%20WWR.pdf).

**Access:** institutional abstract and complete 41-page accepted manuscript accessible. Selectively inspected §§3.1–3.5 and abstract/method outline; no proof reproduction. Manuscript's “2021, in press” footer differs from final January 2022 issue year.

## What the inspected formulation establishes

This paper already couples multidepot trip scheduling, TOU charging cost and concurrent charging. A time-expanded network supports cost-first lexicographic optimization, then peak reduction within an allowed cost increase. The method uses branch-and-price, heuristics and a trip-chain pool. Its peak variable represents maximum simultaneous charging buses, with station-capacity constraints. Assumptions A1–A2 require full charging and fixed full-charge duration; A3 assumes deterministic travel times. These are consequential model restrictions, not generic grid physics. See manuscript §§3.1–3.5.

## Implications for EGG (our assessment)

Do not claim that joint vehicle scheduling, electricity tariffs, charger scarcity or peak-load coordination are themselves new. This paper is closer than a title-only survey citation suggests and belongs in the main positioning discussion and nonlearned baseline design.

An EGG distinction would need a side-by-side mathematical comparison. Candidate differences worth testing include genuinely variable charging quantity/power, time-varying aggregate supply limits, cross-site supply coupling, or another explicitly modeled resource absent from the inspected formulation. Merely replacing a count of simultaneously charging buses with its fixed-power equivalent is unlikely to establish a substantial new mechanism. This note does not assert exhaustive absence of every such extension from this paper or the broader literature.

A discriminating experiment would first align EGG with the paper's fixed-duration/full-charge special case, then introduce each additional coupling separately. Compare total cost and peak demand at fixed fleet count, followed by the time required for a valid full-model gap. This reveals whether the proposed learning method benefits from the additional resource structure or from a different underlying formulation and time budget. Reimplementing the full branch-and-price is a significant task; an aligned compact-model baseline can provide an initial diagnostic without claiming a replication.

## Parmentier metadata follow-up

Verified final publication through the [authors' institutional research record](https://researchportal.ip-paris.fr/en/publications/electric-vehicle-fleets-scalable-route-and-recharge-scheduling-th/): Axel Parmentier, Rafael Martinelli, Thibaut Vidal (2023), *Electric Vehicle Fleets: Scalable Route and Recharge Scheduling Through Column Generation*, Transportation Science 57(3), 631–646, [DOI 10.1287/trsc.2023.1199](https://doi.org/10.1287/trsc.2023.1199). The EV review now includes final metadata while identifying the inspected February 2023 preprint revision.
