# Network congestion and negative marginal prices

**Verified primary source:** Kyri Baker and Harsha Gangammanavar, *Locational Marginal Prices Obey DC Circuit Laws*, author preprint v1, 27 March 2024, [full HTML](https://arxiv.org/html/2403.19032v1), [PDF](https://arxiv.org/pdf/2403.19032), [persistent identifier](https://doi.org/10.48550/arXiv.2403.19032). One source suffices for the requested fact; no broader survey was pursued.

## Exact evidence and access scope

Inspected the full relevant primary text: Section II, PDF p.2, equations (P)/(2)–(4) and dual/optimality equations (5); and **Section V-B, PDF p.5, Figure 5 and its accompanying three-bus explanation**. Section V-B expressly attributes negative LMPs to congestion without negative bids, must-take output, ramping or minimum on/off constraints. Its example has a 10 MW line limit, no generation upper bounds, a cheapest marginal generator costing $20/MWh, and bus-1 LMP **−$60/MWh**. The optimization is a **continuous linear DC-OPF**, not an AC nonconvexity or unit-commitment example. The paper's nonnegative linear generation offers suffice: increasing total generation costs do not imply nonnegative nodal load sensitivities.

No model was executed or independently numerically reconstructed. The HTML/PDF prose and equation text were accessible; a separate HTML figure-image retrieval failed, so no unexposed graphical parameter is asserted. This is a verified author-preprint claim and explicit worked illustration, not an independently reproduced numerical certificate.

## Safe use in this manuscript

Suggested attribution: “Even convex lossless DC dispatch with nonnegative generation offers can have negative nodal marginal prices because of transmission congestion (Baker and Gangammanavar, 2024, Section V-B, Figure 5).” This existing phenomenon should be cited as a limitation of extending the present monotone-supply reduction, not claimed as a new contribution.

The mathematical distinction is between generation cost as a function of generation and the optimized network-dispatch value as a function of **nodal demands**. Convexity of the latter does not ensure coordinatewise monotonicity: an extra withdrawal can change feasible flow patterns and relieve a binding constraint. Thus positive generation marginal costs alone are not a sufficient hypothesis for replacing a fleet plan by a componentwise lower-load plan under network dispatch. One must establish monotonicity/nonnegative relevant marginal prices on the admitted domain, or retain the otherwise discarded alternatives.

Two cautions prevent overstatement. A **negative congestion component** alone does not prove a negative total LMP; the total price must cross zero. Also do not reuse the source's later qualitative circuit-location sentence as a general necessary-and-sufficient negative-price theorem: this note relies only on its explicit DC-OPF example and direct congestion statement. No claim about strictly increasing marginal-offer curves, AC-feasible realization, operational prevalence or this paper's public timetable follows from the linear-offer example. A separate symbolic strictly convex example, if proved by the parent, would supply that stronger illustration independently.

```bibtex
@misc{bakerGangammanavar2024prices,
  author = {Baker, Kyri and Gangammanavar, Harsha},
  title = {Locational Marginal Prices Obey {DC} Circuit Laws},
  year = {2024},
  eprint = {2403.19032},
  archivePrefix = {arXiv},
  primaryClass = {math.OC},
  doi = {10.48550/arXiv.2403.19032},
  note = {Version 1, 27 March 2024; Section V-B, Figure 5}
}
```
