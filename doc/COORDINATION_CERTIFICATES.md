# Price support for complete fleet schedules: a certificate interpretation

Research note, 12 September 2026. Status: mathematical derivation and
solver-independent verification; independent review pending. This note changes
no experimental result, registered gate, evidence contract or settlement rule.

## 1. Question and contribution boundary

Can a realized fleet schedule be optimal at the marginal electricity prices
created by its own charging load? The answer is characterized by the gap
between the physical planner and the complete-schedule convexification. A
positive lower bound on that gap also bounds the incentive to deviate at every
realized schedule's own price. This connects price-iteration observations to a
static, algorithm-independent obstruction.

The equilibrium/convexification principle and minimum-uplift interpretation are
established economic theory. The proposed EGG contribution is the precise
model mapping, numerical certificate interpretation, and operational study of
mandatory, indivisible fleet duties. This is neither a first claim for
nonconvex demand pricing nor a new general welfare theorem. The comparison in
Section 7 is targeted and does not verify exclusivity.

## 2. Model and price-support proposition

Let S be the **same complete feasible physical schedule set** in the planner,
price-response oracle and convexification. Write c(s) for intrinsic operating
cost, L(s) for slot charging energy, and

\[
P=\{(c(s),L(s)):s\in S\},\qquad K=\operatorname{conv}P.
\]

Let F be convex and differentiable on an open neighborhood of the feasible
load hull. A convenient sufficient regularity assumption is that P is nonempty
compact: this guarantees attainment and finite values below, even if charging
is continuous. Finiteness of S is unnecessary. The inequalities below also hold
with infima without physical attainment; the converse explicitly needs it.

Define

\[
h(s)=c(s)+F(L(s)),\quad z_D=\min_{s\in S}h(s),\quad
z_{CH}=\min_{(\bar c,\bar L)\in K}\{\bar c+F(\bar L)\},\quad
\Delta=z_D-z_{CH}\ge0.
\]

For a posted price p define the global response value
V(p)=min over u in S of c(u)+p·L(u). For a physical schedule s, let
p_s=∇F(L(s)) and r(s)=c(s)+p_s·L(s)−V(p_s).

**Proposition 1 (physical price support and unavoidable regret).**

1. For every physical s, r(s) ≥ h(s)−z_CH ≥ Δ.
2. Δ=0 if and only if some physical schedule is a best response at its own
   price. When Δ=0, **every** physical planner optimizer has this property.

**Proof.** A linear functional has the same infimum over P and conv P. Thus
for every convex mixture,

\[
\bar c+p_s\cdot\bar L\ge V(p_s),\qquad
F(\bar L)\ge F(L(s))+p_s\cdot(\bar L-L(s)).
\]

Adding and minimizing gives z_CH ≥ h(s)−r(s). If r(s)=0, then
z_CH ≥ h(s) ≥ z_D ≥ z_CH, proving equality and physical optimality.
Conversely, when Δ=0 a physical planner optimizer s* also minimizes the
convexified objective. Its one-sided directional derivative toward any
(c(u),L(u)) in P is nonnegative:

\[
c(u)-c(s^*)+\nabla F(L(s^*))\cdot(L(u)-L(s^*))\ge0.
\]

This is exactly the global best-response inequality. ∎

This is a statement about the best-response **correspondence**. It does not
promise convergence of a deterministic selection rule, a unique physical
schedule, or a fixed point under strategic bill minimization.

**Attainment matters.** Set S=[0,1] excluding 1/2, c=0, L(s)=s, and
F(L)=(L−1/2)². The physical infimum and convexified minimum both equal zero,
and conv P is compact, but no physical optimum exists. At any s<1/2 its own
negative gradient makes 1 the best response; at any s>1/2 its positive gradient
makes 0 the best response. Neither is s. Compactness of the convex hull alone
therefore cannot justify the converse. The helper requires a separate physical
attainment premise before reporting zero-gap existence.

## 3. Approximation, units and interval arithmetic

Suppose s is an ε-best response at a posted price p̃, and
||p̃−∇F(L(s))||∞ ≤ η. Let D₁ bound max over u,v in S of
||L(u)−L(v)||₁. Comparing the two linear private objectives gives

\[
r(s)\le \epsilon+\eta D_1,\qquad
\Delta\le\epsilon+\eta D_1.
\]

The comparison price must be the gradient at the **same realized physical
load**, not the gradient at a fractional mean. D₁ must cover the entire
feasible set, not just observed columns. For the current nonnegative-load
model, a coarse model-derived bound is
D₁ ≤ T × charge_power_kw × slot_min/60 × max_vehicles, using the per-slot
ceiling in `regimes._l_max`; tighter bounds require their own justification.

EGG's load entries are kWh per slot. Prices and η are currency/kWh; D₁ is kWh;
ε, Δ and ηD₁ are currency. No additional duration multiplier belongs in p·L.
A relative presentation must divide all monetary quantities, including ε and
ηD₁, by the same strictly positive reference cost. The helper performs no
implicit currency, power, duration or normalization conversion.

Given genuine outer enclosures
z_D∈[L_D,U_D], z_CH∈[L_CH,U_CH],

\[
\Delta\in[L_D-U_{CH},\;U_D-L_{CH}].
\]

The raw lower endpoint is preserved; intersection with Δ≥0 gives a separate
tightened interval. A lower endpoint greater than ε+ηD₁ **strictly** excludes
that approximate-equilibrium class. Equality at the threshold does not.
An interval crossing zero neither proves nor disproves exact existence.
A nonpositive upper gap can establish zero only if the outer enclosure is
rigorous and compatible with Δ≥0, and the physical minimum is attained.

A positive-gap conclusion needs a valid **physical lower bound** and a
**convexified upper bound**. A replay-feasible convex mixture from a restricted
pool can supply the latter: complete column enumeration or a tight global
convexified lower bound is not required for this direction. Conversely,
a restricted-master optimum is generally not a global lower bound and cannot
establish zero gap by itself. An alternative relaxation, such as a duty-level
LP with a different feasible convex hull, must not be substituted silently.

### Pure arithmetic interface

`src/egglab/coordination_certificates.py` contains `CostBounds`, `Premises` and
`coordination_certificate`. It has no file, optimizer or experiment imports.
Its premise fields are caller assertions, **not authenticated evidence or
verified physical facts**. An upstream adapter must prove them and bind source
identity. No such population adapter is supplied here.

Exact strings, integers, `Decimal` and `Fraction` inputs become rational
numbers; all arithmetic is exact. Floats, booleans, nonfinite numbers,
reversed intervals, negative allowances and currency mismatches are rejected.
Source rounding uncertainty does not disappear when a decimal string is
parsed: the caller must enclose it or supply `absolute_error`, which widens
both objective endpoints before subtraction. The helper cannot infer a
serialization, solver, feasibility or reconstruction allowance from a solver
status string. Already enclosed errors should not be counted a second time.

All conclusions are conditional. The required premises are common complete
physical models, convex differentiable F, and valid outer bounds including
all errors. A positive η additionally requires same-load price accuracy and a
global diameter bound. Exact zero gap only establishes existence when
`physical_minimum_attained=True`; false conclusion fields mean unresolved,
not the opposite conclusion.

For example, in a Python session started from `src`:

```python
from egglab.coordination_certificates import (
    CostBounds, Premises, coordination_certificate,
)
premises = Premises(
    common_complete_schedule_model=True,
    convex_differentiable_system_cost=True,
    certified_bounds_include_all_errors=True,
    physical_minimum_attained=True,
    price_error_at_same_physical_load=True,
    global_load_diameter_bound=True,
)
certificate = coordination_certificate(
    CostBounds("4", "4", "synthetic_currency"),
    CostBounds("3", "3", "synthetic_currency"),
    premises=premises, epsilon_cost="0.1",
    price_error_per_kwh="0.2", load_diameter_kwh="4",
)
assert certificate.regret_lower == 1
assert certificate.excludes_approximate_equilibrium  # 1 > .1 + .2*4
```

These numbers come from the independently computed example in Section 6,
not any experiment population.

## 4. Exact mapping to the current implementation

Inspected baseline: `44a152e2914ae7f06940259e2c8df0128ad4f40d`.

| Mathematical object | Code/specification and interpretation |
| --- | --- |
| F(L) and ∇F(L) | [`market.py` lines 41–55](https://github.com/ndandnd/egg/blob/44a152e2914ae7f06940259e2c8df0128ad4f40d/src/egglab/market.py#L41-L55): `system_cost_delta` is (a+bU)·L+Σ b_t L_t²/2; `price` is a+b(U+L). `marginal_outlay` has 2bL and belongs to the different strategic bill. |
| c(s), L(s), complete S | [`b2a2.py` lines 178–234](https://github.com/ndandnd/egg/blob/44a152e2914ae7f06940259e2c8df0128ad4f40d/src/egglab/b2a2.py#L178-L234): `column_from_solution` uses a complete replay-validated fleet schedule, `ops_cost` and physical charging load. |
| Global response V(p) | [`b2a2.py` lines 628–638](https://github.com/ndandnd/egg/blob/44a152e2914ae7f06940259e2c8df0128ad4f40d/src/egglab/b2a2.py#L628-L638): economic posted price is **p=−π**, with π the LP link-row dual. The reconstructed incumbent is a response upper bound; `sol.stats.bound` is the lower bound. |
| z_D enclosure | [`regimes.py` lines 79–112](https://github.com/ndandnd/egg/blob/44a152e2914ae7f06940259e2c8df0128ad4f40d/src/egglab/regimes.py#L79-L112): true physical objective supplies `adaptive_ub`; tangent-relaxation global bounds supply `adaptive_lb`. |
| z_CH enclosure | [`b2a2.py` lines 23–70](https://github.com/ndandnd/egg/blob/44a152e2914ae7f06940259e2c8df0128ad4f40d/src/egglab/b2a2.py#L23-L70): the clean restricted master is evaluated with true F for UB_CH; global pricing bounds enter the Lasdon lower bound. Tangent-model objective alone is not the true upper bound. |
| Published interval convention | [`B3_UPLIFT_BASELINE_SPEC.md` lines 48–68](https://github.com/ndandnd/egg/blob/44a152e2914ae7f06940259e2c8df0128ad4f40d/doc/B3_UPLIFT_BASELINE_SPEC.md#L48-L68): `(z_d_ub-tol_d)-ub_ch` through `z_d_ub-lb_best`, conditional on the stated dictator tolerance and serialization allowances. No cells are reinterpreted here. |

The old settlement task brief calls raw π the posted price. This differs from
the implemented p=−π convention; it is a documentation issue, not evidence
that the implemented pricing sign is wrong. A later reviewed adapter must
reconcile the exact schemas instead of copying the brief's symbols.

## 5. Fleet and supply accounting

In the affine incremental-supply interpretation use L≥0 and
F*(p)=sup over L≥0 of p·L−F(L). At any price with finite conjugate, the
fleet and supplier lost-opportunity costs for a balanced physical schedule are

\[
\operatorname{LOC}_{fleet}=c(s)+p\cdot L(s)-V(p),\qquad
\operatorname{LOC}_{supply}=F(L(s))-p\cdot L(s)+F^*(p).
\]

Both are nonnegative. With d(p)=V(p)−F*(p), their sum is

\[
h(s)-d(p)=\Delta+[h(s)-z_D]+[z_{CH}-d(p)].
\]

At a planner-optimal physical dispatch and a dual-optimal common price,
assuming convexified strong duality, the sum equals Δ. This is the standard
Lagrangian minimum-uplift identity in EGG notation. At the realized own price,
Fenchel equality makes supplier LOC zero, and fleet LOC is r(s), which is
bounded **below** by Δ. At a common convex-hull price, fleet LOC alone need
not equal or exceed Δ. These are different conditioning prices.

For b_t>0, F*_t(p)=max(0,p−a_t−b_t U_t)²/(2b_t). For b_t=0 the conjugate is
zero when p≤a_t+b_t U_t and infinite otherwise. Negative-price extensions,
network constraints or restricted supplier domains require renewed model
matching; this note does not attribute those features to the current
synthetic model.

A final tangent-master dual is not automatically an exact convex-hull price.
The settlement price needs its own dual value d(p) (or a certified lower
bound), rather than only a historical `lb_best` collected at other prices.
With approximate dispatch/price, report the two additional nonnegative terms
instead of asserting total LOC=Δ. Neither equality nor a payment covering a
participant's regret establishes budget balance, voluntary participation,
truthfulness or funding of mandatory public service.

PR [#40](https://github.com/ndandnd/egg/pull/40), pinned at
`80d0ffd42a0de619674a6dae8cfae713f1fb94db`, already provides participant
price-conditioned regret/settlement arithmetic and a separate joint-identity
contract. Its evidence/identity premises must be satisfied by a later adapter.
That branch is not merged by this work; its parser and payment calculator are
not duplicated here.

## 6. Worked examples and existing physical witness

Take two **abstract** allowed schedules with c=0, L¹=(2,0), L²=(0,2) kWh,
and F(L)=L₁+L₂+(L₁²+L₂²)/2. Both physical schedules cost 4. Any convex
mixture is L=(2t,2(1−t)), with F(L)=3+4(t−1/2)², so z_CH=3 and Δ=1.
At physical L¹ its own price is (3,1), and switching to L² lowers the posted
bill from 6 to 2: regret is 4. The other schedule is symmetric. At the common
CH price (2,2), fleet regret is zero while supplier LOC is 1. Randomizing
between physical schedules on different days still incurs expected system
cost 4, rather than F of the mean, 3.

Replacing F by L₁+L₂ gives exact zero gap and supports both physical
optimizers at gradient (1,1). Section 2's punctured feasible set supplies the
nonattainment counterexample. In the positive-gap example, D₁=4; ε=.1 and
η=.2 yield a .9 regret ceiling, which is excluded, while η=.225 gives the
boundary value 1, which is not excluded. The tests also show how explicit
rounding allowances remove an apparent small positive gap.

Run the bounded verification artifact, without a solver or experiment input:

```bash
python3 src/tests/test_coordination_certificates.py -v
# Or with pytest available:
python3 -m pytest src/tests/test_coordination_certificates.py -q
```

The checks combine exact rational worked examples with bound-direction,
large-cancellation, unit/premise rejection and threshold tests. Finite sample
checks of a polynomial identity are not a substitute for the analytic proof.
The test file's infinite-set example checks a sequence and its analytic
construction; it does not claim enumeration of that set.

The existing physical witness belongs to PR
[#39](https://github.com/ndandnd/egg/pull/39), pinned at
`2ad05f5cf8340ed50e17ad985c57a245f76f894f`. Its
[`STRICT_TWO_CYCLE_WITNESS.md`](https://github.com/ndandnd/egg/blob/2ad05f5cf8340ed50e17ad985c57a245f76f894f/doc/STRICT_TWO_CYCLE_WITNESS.md)
describes four trips, two vehicle slots, continuous charging, discrete
structure margins, near-optimal load-face bounds and a necessary-planner
lemma. It claims 1-minimality on tested deletion axes, not global minimality.
The present note reuses this reference rather than reconstructing its
minimizer or running another seed search. Its unmerged enumeration changes
were not imported or executed. A reviewed adapter from its physical evidence
to the new interval helper remains pending; the two-slot example above is
**not** claimed to be a verified fleet instance.

## 7. Primary literature and remaining research questions

Selected full-text passages were inspected for the following comparisons.
They support the stated assumptions and results, not a full-paper correctness
audit or a comprehensive novelty review.

- **Madani, Ruiz, Siddiqui and Van Vyve**, arXiv:1804.00048v1,
  30 March 2018, [Section 3, Theorem 1, equations (29)–(31)](https://arxiv.org/html/1804.00048v1#S3).
  Nonconvex demand bids appear explicitly; dual-optimal prices minimize the
  stated aggregate opportunity-cost uplift. EGG's distinction must come from
  mandatory fleet feasibility and certified application.
- **Andrianesis, Bertsimas, Caramanis and Hogan**, arXiv:2012.13331v1,
  24 December 2020, [Sections II–III](https://arxiv.org/html/2012.13331v1#S3).
  Dantzig–Wolfe and column generation already compute convex-hull prices from
  complete participant schedules. EGG's use of a schedule oracle is not itself
  a novel pricing method.
- **Gu and Qin**, arXiv:2510.26036v4, 9 September 2026,
  [Section II-C, Assumptions 1–2; Section III-A, Theorem 1 and Corollary 1](https://arxiv.org/html/2510.26036v4#S2.SS3).
  Their linear load map, compact convex decision set and strictly convex
  collective preference yield a convex equilibrium characterization. Their
  continuous amount/count relaxation is the key contrast to physical atomic
  duties. Collective preference may differ from social disutility, so an
  efficiency comparison also requires objective matching. Their price-taking
  premise is distinct from strategic anticipation of one's market impact.
- **Yao, Liu, Scaglione, Bekhor and Zhang**, arXiv:2505.04532v1,
  7 May 2025, [Sections II-A–D, Propositions 3–5 and Appendix IV-B/C](https://arxiv.org/html/2505.04532v1#S2.SS4).
  Perturbed-utility MDP flows respond continuously to prices under the stated
  assumptions; the OPF continuity proposition is local and requires unchanged,
  linearly independent active constraints. Applying their Brouwer argument
  requires a compact convex invariant price domain with global continuity.
  The comparison does not establish failure of their numerical equilibrium;
  it identifies premises that atomic EGG schedules cannot inherit.
- **Milgrom and Watt**, *Review of Economic Studies* 93(3), May 2026,
  pp.1995–2020; online 16 September 2025,
  [Section 3, Theorem 1; Section 4 and Appendix B](https://academic.oup.com/restud/article/93/3/1995/8255713).
  Their welfare-loss bound uses rationing losses and budget surplus; their
  markup mechanisms and Shapley–Folkman construction offer an aggregation and
  settlement comparator. Mandatory service cannot silently inherit their
  buyers' zero-bundle option and disposal/operating-reserve assumptions.

A relevant older antecedent is Bikhchandani and Mamer,
[*Competitive Equilibrium in an Exchange Economy with Indivisibilities*](https://www.sciencedirect.com/science/article/pii/S0022053196922693),
JET 74(2), 1997, pp.385–413. Publisher metadata and an indexed original-paper
excerpt of Section 3, Proposition 2, p.394 were checked, but direct full-text
retrieval failed. A complete model comparison is pending; this note supplies
its own proof and does not label that source fully audited.

The next discriminating questions are:

1. How large is certified unavoidable regret relative to a justified service
   cost and price-impact scale, after all endpoint errors are enclosed?
2. Can the existing PR #39 witness and PR #40 settlement evidence be connected
   to this theorem without weakening their feasibility and common-price
   premises?
3. Which performance-contingent payment and funding rule supports mandatory
   service, with participation rights and supplier accounting explicit?
4. Does distributing comparable service across independent fleets reduce
   relative regret, or do shared chargers and route complementarities prevent
   useful aggregation? Physical aggregation differs from day-to-day lotteries.
5. Can a convex network dispatch value function replace affine F while
   preserving a properly qualified subgradient-price theorem and certificate?

No answers to protected A6 or B3 outcome questions are asserted here.
