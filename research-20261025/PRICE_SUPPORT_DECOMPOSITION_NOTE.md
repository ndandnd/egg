# Price-support decomposition: valid identity, limited contribution

25 October2026. Algebraic/static review only; no computation, import, solver,
protected outcomes or new literature search. This concerns the planner objective
in SCIENTIFIC_EVIDENCE_AUDIT.md, not an atomic clearing-price payment objective.

## Conditions and derivation

Let j index physically feasible COMPLETE schedules, including their charging
profiles. For several coupled fleets, j must be a joint feasible allocation;
independently selected fleet columns need not satisfy shared constraints.
Assume finite c_j and L_j, B symmetric positive semidefinite, and

`S(L)=a'L+½L'BL`, `z_j=c_j+S(L_j)`.

Suppose the convex-hull minimum is attained by nonnegative weights λ* summing
to1, with `L*=Σλ*_j L_j`, `c*=Σλ*_j c_j`, and `z_CH=c*+S(L*)`.
The feasible catalog must be complete for a full-problem statement. A finite
complete catalog suffices; an infinite family additionally needs attainment
and the stated mixture/support representation. No strict positive definiteness
or uniqueness is required; the B expression may be a seminorm.

First-order optimality on the convex hull gives, for every feasible j,

`c_j+p*'L_j >= c*+p*'L*`, where `p*=a+BL*`.

The λ*-weighted average attains equality. Therefore
`η*=min_j(c_j+p*'L_j)=c*+p*'L*`, and every positive-weight column has scoreη*.
Expanding the quadratic then proves exactly

`z_j-z_CH = [c_j+p*'L_j-η*] + ½(L_j-L*)'B(L_j-L*)`.

The first term is nonnegative global linear-pricing opportunity loss. The
second is the quadratic Bregman divergence from the convexified load. This is
an equality, without omitted cross terms. For a supporting column the first
term is zero; a tied minimizer with zero λ may still have a large divergence.

For J+=support(λ*), averaging gives

`Σ_{j∈J+} λ*_j(z_j-z_CH) = ½Σ_{j∈J+} λ*_j ||L_j-L*||²_B`.

Consequently the best supporting pure column has loss to z_CH no greater than
that weighted load variance. It also has loss to the best pure optimum no
greater than the same bound, since z_CH is a lower bound. This is feasible
whole-column selection, not independent rounding of coupled fleet schedules.
Finding the full hull/pricing optimum and obtaining its columns may be costly;
the extraction bound grants no free computational advantage.

## What the identity does NOT establish

For a restricted menu, the same algebra/variance statement applies to that
menu's convex optimum, not automatically the full problem. For a selected menu
column, the full relaxation gap also includes
`z_CH(menu)-z_CH(full)`. An unverified omitted-column minimum cannot be calledη*.
With an arbitrary price p, the standard certificate is

`z_j-[η(p)-S*(p)] = [c_j+p'L_j-η(p)] + [S(L_j)+S*(p)-p'L_j]`.

An actual unrestricted pricing lower bound can replaceη(p) to give a safe,
possibly loose lower bound; that does not make either residual an exact full
optimality decomposition. The load-domain/conjugate conventions, numerical
tolerances and pricing-bound provenance must match. The repository already
uses pool linear scores/conjugates in `src/egglab/native_hull.py`'s
`pool_certificate` and `fenchel_bound`; a pool minimum is not unrestricted pricing.

Selecting a price-taking minimizer at p* does not prove market clearing after
deploying it: generally `a+BL_j != p*`. The variance term can stay positive even
with the entire feasible catalog present. More columns/Carathéodory sparsity
therefore do not imply a zero pure indivisibility gap. Nor does this establish
strategic truthfulness or an atomic fleet's payment-minimizing behavior; that
payment uses a different quadratic coefficient unless an institution says
otherwise. Changing time resolution must preserve supply-cost units, including
the appropriate interval-length scaling of curvature.

## Prior-art status and a meaningful research test

This is standard Fenchel–Young duality plus the Bregman/Jensen remainder for a
quadratic. The support bound is weighted-average≥minimum. These observations
should be presented as an explanatory lemma, not a novel theorem or a paper's
main contribution. No new priority/novelty claim is made by this note.

An exact small-catalog experiment can measure the two terms, the actual best
pure gap, the variance bound's slack, and the difference between full and
restricted menus. It should also compare planner cost with explicitly defined
uniform-price payment, so an objective mismatch cannot masquerade as a
price-support mechanism. It establishes magnitudes only for its stated complete
catalog/physical discretization, not arbitrary EV scheduling.

A substantive contribution would require additional structure: a nontrivial
bound on attainable variance under realistic coupled charging/fleet scaling;
an economically interpretable condition for small implementable loss; or a
budgeted algorithm that obtains useful certified columns/prices more cheaply
than strong classical column generation/search. Learning would need to improve
those measured outcomes over those baselines. Small residuals caused simply by
low curvature, near-identical loads or a small toy catalog are nuisance
explanations to test, not evidence for the learned architecture.

## A directly relevant theory lead, checked by the parent

[Udell and Boyd (2016)](https://stanford.edu/~boyd/papers/duality_bound.html)
bound the loss from convexification in a separable nonconvex problem using
active coupling constraints and component nonconvexity. The author's
[paper, Theorem 1 and related-work section](https://web.stanford.edu/~boyd/papers/pdf/duality_bound.pdf)
was inspected for the result and domain assumptions, not re-proved here. This
suggests an appropriate question: does a physically meaningful decomposition of
fleet decisions have few effective coupling constraints? It does not justify
claiming that more buses automatically remove the gap. Trip coverage and shared
charging may prevent separability or make the bound uninformative; discrete
domains require the appropriate extension.

[Dubois-Taine and d'Aspremont (2024 preprint)](https://arxiv.org/abs/2406.18282)
describe a constructive approach using primal feasible points, convexification
and approximate Caratheodory representations. Only the primary abstract was
checked here. It is a method lead, not an EGG guarantee or newly established
novelty. Verify the full assumptions and available oracle before any adaptation.

This optimization/economic connection is substantially closer to the present
question than a superficial chemistry or biology analogy. A new result would
need an explicit EGG mapping, a nonvacuous bound and independently evaluated
decision consequences, rather than a restatement of approximate convexity.
