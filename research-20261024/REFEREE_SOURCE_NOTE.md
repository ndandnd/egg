# Bounded primary-source check for referee perspective

Checked 2026-10-24. This is a targeted check of five primary works, not a new literature review. No experiments or solver work were performed. The useful referee distinction is between a plausible algorithmic improvement, a proved relaxation property, and an implementation or incentive guarantee.

## 1. Pessoa et al. (2018): stabilization merits a controlled test

A. Pessoa, R. Sadykov, E. Uchoa, F. Vanderbeck, *Automation and Combination of Linear-Programming Based Stabilization Techniques in Column Generation*, **INFORMS Journal on Computing 30(2), 339–360**. [Publisher/DOI](https://pubsonline.informs.org/doi/10.1287/ijoc.2017.0784).

**Inspected:** publisher abstract and bibliographic record. It reports practical convergence improvements from smoothing and penalty methods, self-adjusting parameters, and cumulative benefits from combining methods. This supports stabilization as a serious candidate baseline or extension. It does **not** support a guaranteed EGG speedup of 3–5 times or a theorem based solely on the number of dual coordinates.

**Access limit:** the publisher's PDF endpoint returned the abstract/landing content, not the article body. The institutional [HAL manuscript endpoint](https://inria.hal.science/hal-01077984/document) returned an Anubis access-denied page; alternate HAL endpoints were inaccessible. No tables or body-level theorem claims from this paper are asserted here. Publication year is 2018; an earlier manuscript exists, so manuscript dates should not replace the journal year.

## 2. du Merle et al. (1999): degeneracy matters, and performance depends on choices

O. du Merle, D. Villeneuve, J. Desrosiers, P. Hansen, *Stabilized column generation*, **Discrete Mathematics 194, 229–237**. [DOI/publisher](https://doi.org/10.1016/S0012-365X(98)00213-1); [readable original text uploaded by coauthor Jacques Desrosiers](https://www.researchgate.net/publication/2250769_Stabilized_Column_Generation).

**Inspected:** introduction, pp. 230–231; airline crew-pairing example and Table 1, p. 234. The original text connects slow convergence to degeneracy and proposes a perturbation/penalty stabilization scheme within LP. In one crew-pairing instance, Table 1 reports speedup factors **0.75, 5.57, and 7.41** for different initial parameter intervals, against the unstabilized reference. Thus even this favorable original example includes a slower configuration.

**Limit:** these are results for particular formulations, instances, parameter schedules, and hardware, not dimension-based bounds or transferable EGG forecasts. The publisher abstract was search-readable, but direct publisher opening failed; body inspection used the coauthor-uploaded original article's extracted text. Its OCR is imperfect, although the relevant prose and table entries are readable. Journal year is 1999; repository/upload dates differ.

## 3. Wentges (1997): smoothing has a convergence rationale, not a universal time ratio

P. Wentges, *Weighted Dantzig–Wolfe Decomposition for Linear Mixed-integer Programming*, **International Transactions in Operational Research 4(2), 151–162**. [Publisher/DOI](https://onlinelibrary.wiley.com/doi/10.1111/j.1475-3995.1997.tb00071.x).

**Inspected:** publisher abstract and citation record. It describes pricing at a weighted average of previous multipliers and the master solution, a convergence proof, and computational results for capacitated facility location. It explicitly frames Dantzig–Wolfe as solving a **Lagrangian dual** after relaxing complicating constraints.

**Limit:** abstract-level access only; the convergence proof and numerical tables were not inspected. Convergence is not a wall-clock acceleration bound. Cite **1997**, matching the volume and citation record, rather than the page's later “first published” electronic date (24 August 2006).

## 4. EUPHEMIA (18 December 2025): actual exclusive groups retain acceptance restrictions

PCR/NEMO Committee, *EUPHEMIA Public Description: Single Price Coupling Algorithm*, **18 December 2025**. [Official complete PDF](https://www.nemo-committee.eu/assets/files/euphemia-public-description.pdf). The [OTE version index](https://www.ote-cr.cz/en/short-term-markets/market-coupling-day-ahead-market/pcr-price-coupling-of-regions) labels this version valid from 19 December 2025.

**Inspected:** §§5.4, 5.4.2 (pp. 36–38), §§7.3–7.5 (pp. 45–52), §7.11 (pp. 68–69). Exclusive groups constrain the **sum of acceptance ratios to at most one**; when each block has minimum acceptance ratio one, at most one may execute. Curtailable blocks can permit partial acceptance, subject to their minimum ratios. The algorithm pursues economic surplus with integer acceptance decisions and price-feasibility checks; it can reject an integer master solution when the price subproblem fails. It starts from an integrality relaxation and uses branch-and-cut. Stopping criteria include a time limit.

**Limit:** public algorithm description, not source code or a claim that every operational run certifies the global optimum. “EUPHEMIA-compatible menu” therefore needs a mapping to actual order types and acceptance rules; a fractional Dantzig–Wolfe mixture alone is insufficient.

## 5. Hua and Baldick (2017): an individual convex hull is a dual relaxation object

B. Hua, R. Baldick, *A Convex Primal Formulation for Convex Hull Pricing*, **IEEE Transactions on Power Systems 32(5), 3814–3823**. [Author-hosted full paper](https://users.ece.utexas.edu/~baldick/papers/convex_hull_2017.pdf); [DOI](https://doi.org/10.1109/TPWRS.2016.2637718).

**Inspected:** §§II.B–II.C, equations (6)–(9); §III.A, Assumption 1 and Theorem 1, pp. 3815–3817. With compact individual feasible sets and linear system constraints, the formulation using individual convex hulls and convex cost envelopes recovers the **Lagrangian-dual value** and prices. It does not assert equality to the nonconvex commitment optimum. For the balance-only setting, the nonconvex primal–dual gap equals total lost-opportunity-cost uplift, which convex-hull pricing minimizes. Section II explicitly assumes price-taking units.

**Limit:** this is a US unit-commitment model, not an EUPHEMIA mechanism theorem. Price-taking dispatch support and minimum uplift do not prove truthful strategic reporting. Journal year is 2017; the DOI and early publication date are from 2016.

## Formal implications for the referee response (our deductions)

- **Stabilization:** oscillation/degeneracy is a defensible diagnostic to investigate. A larger dual dimension alone implies neither those symptoms nor any fixed speedup. Treat 3–5 times as an empirical hypothesis requiring comparable runs and full wall-clock accounting, not an established consequence of the cited theory.
- **Sparse menus:** Carathéodory bounds the support needed to represent a point in a convex hull (using the relevant affine dimension). It does not change that point into an executable indivisible allocation. Convexifying each participant before imposing coupling constraints generally differs from taking the convex hull of jointly feasible allocations.
- **Elementary counterexample:** a supplier offers either 0 or 2 units at total costs 0 or 2; demand can consume at most 1 unit with value 3 per unit, and balance is exact. The indivisible optimum trades nothing, with welfare 0. The supplier hull permits half of the 2-unit offer, supplying 1 at cost 1 and welfare 2. A two-point menu already gives the gap; support compression cannot remove it. This is a mathematical illustration, not an operational EUPHEMIA instance.
- **Strategy:** a representation theorem concerns feasible quantities and objective values. Truthfulness needs a defined report space, allocation/payment rule, and incentive argument. Neither a sparse hull representation nor the cited price-taking convex-hull-pricing result supplies that argument.

Recommended posture: acknowledge the referee's stabilization suggestion and the practical relevance of exclusive-group menus, while keeping acceleration, convexified welfare, executable clearing, and strategic incentives as separate claims with separate evidence.
