# Additional primary-source positioning checks

These checks follow the 16-source matrix and do not change its original access
record. Checked 27 September 2026. Neither paper was used to certify our
physical model or numerical results.

**Guo, Henderson, Cory-Wright and Yang, “Pricing Discrete and Nonlinear Markets
With Semidefinite Relaxations,” arXiv:2602.15722v1, 17 February 2026.**
[Primary preprint record](https://arxiv.org/abs/2602.15722v1).
Inspected the abstract and version metadata, not the complete proof. The paper
derives prices from an SDP relaxation for discrete/nonlinear markets and states
a conditional LOC bound in terms of its relaxation gap. This reinforces the
need to specify the relaxation, price and direction of the inequality. Our
physical schedule's own-gradient regret lower bound is not a claim to improve
that pricing mechanism. Publication status beyond this preprint was not checked;
do not describe it as a refereed result or transfer its assumptions without
reading the theorem.

**Ahunbay, Bichler and Knörr, “Pricing Optimal Outcomes in Coupled and Non-Convex
Markets: Theory and Applications to Electricity Markets,” Operations Research
73(1), 178–193.** [Publisher record](https://doi.org/10.1287/opre.2023.0401).
The publisher reports online publication 11 June 2024 and issue January–February 2025;
its own citation uses 2024. Inspected metadata and abstract, not paywalled proofs.
The paper treats pricing as a multiobjective problem and proposes a rule aimed
at local deviation incentives while balancing compensation and congestion
signals. Our separate fleet/supply LOC accounts therefore need local, explicit
attribution and cannot be presented as a new tradeoff or settlement mechanism.

Both are candidates for the next manuscript revision after full-text inspection.
The already reviewed working PDF has not been silently recharacterized as
including these additional sources.

## Charging fidelity and a reusable public data source

**Löbel, Borndörfer and Weider (2024), arXiv:2407.14446v1.**
[Author manuscript](https://arxiv.org/abs/2407.14446v1),
[inspected HTML sections 2–4](https://arxiv.org/html/2407.14446v1).
The paper analyzes errors from approximating nonlinear charging and proposes
an increment-domain formulation with dynamic power and grid limits. Replacing
a charge curve by a pointwise lower approximation need not preserve a lower
SOC trajectory. Our inference: the constant-efficiency/no-taper reference must
stay explicitly scoped; adding taper requires a separately justified feasible
set, not cosmetic interpolation. The inspected abstract lists a submitted
manuscript, not a verified journal version. HTML displays an inconsistent
render date; cite the explicit arXiv v1 identity, not that date.

**Sistig, Sinhuber, Rogge and Sauer (2025).**
[Publisher article](https://doi.org/10.1038/s44333-025-00030-y),
[versioned public dataset](https://doi.org/10.6084/m9.figshare.26088190.v1).
The study uses twenty German GTFS-based networks, heuristic vehicle/crew
schedules and electrification scenarios. Its supplementary data includes trips,
itineraries, stops and possible deadheads, with CC BY 4.0 metadata. This supplies
a stronger candidate for reproducible timetable/movement intake than forcing
unresolved private movement gaps. It does not identify a convex electricity
supply function or prove our own-price effect. Local archive/format inspection
is pending; do not call it model-ready merely from its description.

**Ricard, Desaulniers, Lodi and Rousseau (2026).**
[Publisher record](https://doi.org/10.1016/j.ejor.2026.05.046), available online
1 June 2026, corrected proof. Title: *Chance-constrained battery management for
electric bus scheduling*. The inspected publisher highlights describe stochastic
energy, probabilistic SOC limits, branch-and-price, nonlinear partial charging
and charger capacities. This is an abstract/highlights-level check, not a proof
or full-method review. Its relevance is the boundary between our deterministic
certificates and operational uncertainty; no novelty claim for those charging
features is justified by our prototype.

## Aggregation and individual incentive scope

Kerdreux, Colin and d’Aspremont, *An Approximate Shapley-Folkman Theorem*,
arXiv1712.08559v3 (1July2019), primary abstract inspected at
https://arxiv.org/abs/1712.08559v3. It relates aggregation of uniformly bounded
nonconvex sets to finite-sum duality-gap bounds. Full proof comparison was not
performed. This motivates checking whether a growing whole-operator regret is
being confused with one small participant's incentive; it does not establish
the EGG formulas by citation. A new algebraic normalization note explicitly
reserves connectors per A/B service-pair operator and derives individual regret
<=20/n, despite the known possible constant aggregate limit. Independent review
of that new note is pending. Starr1969 is a relevant classical antecedent; its
author-hosted PDF was located but timed out, so no full-text-review claim is made.
