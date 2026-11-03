# Theory development and a rigorous public-support resolution plan

Scope: source-only reading of public_case.tex, model_theory.tex,
exact_results.tex and the support-extension proof. No numerical run, import,
hash, native solve, data audit or literature search was performed. The separate
primary-source literature task is not duplicated here. The following are
proposed certificate designs, not completed certificates.

## What is currently known

For the declared depot15 ideal rational model, the manuscript establishes

    429.22 <= CH <= D <= 512.77,
    0 <= D-CH <= 83.55,

with outward-rounded exact bounds. This does not determine whether D=CH.
The old tolerance-qualified native flat optimum does not settle even the
ideal flat optimum, and the flat objective has D=CH by linearity regardless
of integer fleet assignments. Depot16 has a numerical rather than exact
physical upper witness; it should not be conflated with depot15's exact case.

Use precisely the same complete-fleet feasible set, stored-input rational
interpretation, 30-hour horizon, full initial/final400 inventory, one360kW
connector, declared movement/waiting energy and fee100 throughout a certificate.
The nonlinear objective is

    F(e)=sum_t(e_t/5 + e_t^2/1800).

Its economically selected marginal price is p_t=1/5+e_t/900, including at zero
load. Do not add arbitrary nonnegative-domain normal vectors as price choices.

## Route A: prove zero gap by supporting one complete physical plan

This is the cleanest affirmative certificate and does not require finding
physical and hull optima in separate campaigns. Supply a rational physical
witness x, compute its own gradient p exactly, and prove the global inequality

    c(y)+p.e(y) >= c(x)+p.e(x) for EVERY feasible complete fleet y.

An exact lower bound on the global linear response matching the witness's
bill is enough. Then x is supported, D=CH=c(x)+F(e(x)), and physical planning
optimality follows automatically. The proof packet consists of the physical
witness and full inventory/connector replay, exact price vector, exact bill,
and independently checkable global linear-response lower certificate.

A finite plan bank can discover x or a violating deviation. It cannot prove
the displayed universal inequality. A restricted response optimum also cannot.
An exact rational LP relaxation bound that happens to match the physical bill
would suffice, even if that relaxation normally has an integrality gap.
Otherwise use a complete branch-and-bound/disjunctive certificate covering
every feasible discrete assignment and all continuous charging choices.

For a fixed discrete route/visit pattern, optimize its continuous convex QP
before testing own-price support. Rational linear constraints and the rational
quadratic imply a rational optimal projected solution on an active face;
rational KKT multipliers can certify that fixed-pattern optimum. This does
not establish optimality against other patterns. Positive own-price regret
only rejects the tested x; it does not reject existence of another supported x.

## Route B: prove strictly positive gap by separated global bounds

Find a globally valid rational physical lower bound L_D and a rational
feasible mixture giving hull upper bound U_CH, with L_D>U_CH. Then

    D-CH >= L_D-U_CH > 0.

Neither exact D nor exact CH is required. The physical lower bound must hold
for all fleets, not just the retained bank or a chosen bus count. The hull
upper certificate needs only complete replay-feasible physical components,
nonnegative rational weights summing to one and exact evaluation of the
mean-load objective. Average supply cost across days is the wrong quantity.

A useful cheap construction begins with two physical witnesses x,y. Put
d=e(y)-e(x), A=c(y)-c(x)+gradient F(e(x)).d and B=||d||^2/1800. Along their
mixture the exact objective is C(x)+lambda*A+lambda^2*B. If A<0 and B>0,
lambda=min(1,-A/(2B)) is rational and gives a strict improvement over C(x).
If B=0 the expression is linear. A fixed-price improving deviation thus gives
a constructive hull upper bound; it does not alone prove positive global gap.

Prioritize a narrow bound-producing question, not an open solver campaign:
can a cardinality-conditioned path/energy relaxation give L_D above a known
two- or three-fleet mixture? If not, report the overlap and stop claiming a
sign resolution. A small native gap or rounded equality is not this certificate.

## Route C: exact hull certificate plus physical nonimplementability

There is an alternative to globally optimizing the physical nonlinear model.
Certify an exact hull optimum (e*,c*) using both a feasible rational mixture
and an attained price p*=gradient F(e*), together with a global linear pricing
certificate V(p*). Verify exactly

    c*+F(e*) = V(p*)-F*(p*).

The quadratic is strictly convex in the entire load vector. Therefore every
hull optimizer has the same load e*, and then the same operating cost c*.
Consequently D=CH iff that projected point is implemented by a physical plan.
For the declared public objective c(x)=100 times the integer used-bus count,

    c*/100 not an integer  ==>  D>CH.

This is a particularly useful potential certificate: a fractional hull bus
cost, once globally certified, proves strict failure without exact physical
D or a numerical feasibility threshold. Compactness makes the positive
minimum separation attained. The rational mixture must include operating
costs of complete plans, not fractional duty columns. Integer c*/100 is
necessary for implementability, not sufficient; it leaves a genuine physical
feasibility problem at e*. If any additional operating costs enter the model,
the simple100-lattice test must be withdrawn or replaced by its true cost set.

If the lattice test fails, test e* exactly for physical implementation at the
required bus count. A rational feasible implementation proves zero gap.
A complete exact infeasibility certificate proves positive gap. An LP or
duty-column relaxation's feasible solution and an unsuccessful native search
prove neither. This route requires globally certified hull pricing; a fitted
restricted master optimum cannot supply it.

The identity behind a quantitative separation is

    C(x)-CH = [c(x)+p*.e(x)-V(p*)] + ||e(x)-e*||^2/1800.

Both terms are nonnegative. A complete disjunction proving every physical
plan has either linear premium>=epsilon or squared load distance>=1800epsilon
would give gap>=epsilon. The lattice argument establishes strict positivity
without itself supplying a convenient numerical epsilon.

## What can strengthen the global lower bound

Partition by integer bus count k. One bus is already excluded exactly. For
every remaining k, let E_k be a valid total-energy floor. Since charging is
possible in at most24 unit market intervals, Jensen gives

    C(x) >= 100k + E_k/5 + E_k^2/(1800*24).

This is a physical lower bound for that count; a minimum across all admissible
counts is a global physical lower bound. Per-hour availability caps and
mandatory energy by time can strengthen the relaxed quadratic allocation.
Use an exact convex relaxation and rational KKT/dual verification for these
continuous subproblems. Relaxing chronological or charger constraints is safe
for a lower bound; silently imposing constraints that exclude real fleets is
not. The public text only excludes k>=3 from improving one particular dual
certificate. It does not presently exclude those fleets from physical optimum.

For exact linear pricing at a chosen p, combine valid cardinality/path-cover
relaxations, energy/time cuts, and exact LP dual multipliers. If relaxation
bounds do not close, a complete discrete proof may branch on route connections,
service assignments, visits or bus count; every child must cover its parent's
physical possibilities. Rational checking must admit the original ideal model,
not merely the solver's rounded matrix. No big-M value, omitted connection
mode or auxiliary constraint may be justified by the incumbent bank alone.

A tangent to convex F is a global affine lower bound. Multiple rational
tangents can strengthen a physical MILP relaxation, but their max remains a
lower approximation; optimizing it is not exact nonlinear optimality unless
its global lower bound closes against a verified physical/hull upper witness.
Likewise a rationalization of floating dual multipliers must check all signs,
equalities, reduced costs and residual compensation; printing more digits
does not make a numerical certificate exact.

Generic flow integrality alone is insufficient. Battery states, route-dependent
energy, visit choices and the shared charger couple service-path decisions.
To obtain zero gap from convex structure, prove that the *projected complete-
plan set relevant to the hull optimum* is physically implementable, or give a
valid integral extended formulation preserving those couplings. A minimum-fleet
path-cover theorem does not do this. Convex charging on a fixed route pattern
likewise does not settle comparisons across all patterns.

## Recommended bounded sequence and honest stopping conditions

1. Freeze one exact public scenario and identify the certificate target before
   running anything: supported physical witness, separated L_D/U_CH, or exact
   hull plus nonimplementability. Keep depot15 and depot16 evidence separate.
2. Use already admissible physical witnesses only as discovery inputs and
   mixture upper certificates. Select a promising rational own-load or hull
   price; determine whether an exact relaxation can certify its complete
   response globally. Do not expand a finite bank and relabel it full pricing.
3. Prefer Route A if a physical witness and its global response lower bound
   coincide. Prefer Route C if a globally certified hull mixture has fractional
   bus cost. Prefer Route B if cheaper hull mixtures make existing physical
   relaxations plausibly separable. None is guaranteed to finish in the time
   allowance; exact global pricing is the common hard step for A/C.
4. Retain all unknown/failed/partial outcomes. An interval containing zero is
   unresolved. A positive incumbent regret is incumbent-specific. A native
   optimality status is tolerance-qualified. A complete finite proof with exact
   arithmetic is a different object and should be named separately.

## A readable theory-paper hierarchy

Lead with one scientific question: can marginal supply tariffs support a
complete fully replenished fleet when service assignments are indivisible?
Define the participant and posted-tariff institution immediately. Introduce
physical optimum D, whole-plan hull CH and own-price regret in one coherent
section. Present the classical support equivalence as a short attributed
proposition that supplies the language, not as the paper's novelty claim.

The main new analytical arc can then be: (i) a minimal replenished construction
and a strictly feasible positive-gap neighborhood; (ii) what additions preserve
or erase the obstruction, including the exact battery/fee region and the
fee8 counterexample to a tempting shortcut; (iii) participant scale, where a
vanishing planning gap coexists with nonvanishing whole-owner absolute regret.
These statements answer different substantive questions and should not be
buried among solver screens. Put the detailed algebra in an appendix, with
one precise picture of physical branches and hull geometry in the main text.

Nonsmooth generation is a short extension that clarifies price selection:
support means existence of an admissible price, while one selected multiplier
can show a larger regret. The ramp example demonstrates that distinction.
The two-cycle and dual-averaging experiments illustrate particular algorithms;
they are optional supporting material, not evidence of universal nonconvergence.

Public evidence should be a compact certification case with the exact status
prominent. If the sign remains open, title it an unresolved timetable-scale
case rather than confirmation of the mechanism. Move exploratory solver/ML
comparisons to the supplement unless an actual independently verified method
or generalization result is obtained. The expansion proof improves the paper
by answering robustness to richer alternatives; it does not by itself establish
practical importance, originality against primary literature, or a major
computational-method contribution. With the public sign unresolved, the most
defensible product remains a focused analytical application paper.

## Quantifiers and ownership that must remain explicit

* Weak support means the selected plan belongs to the complete fixed-price
  argmin; alternative plans may tie. It does not mean unique implementation.
* Existence of some supported physical plan is equivalent to D=CH under the
  qualification. It is different from supporting every feasible plan.
* With nonsmooth F, existence uses some admissible p in its subdifferential.
  Failure at a selected p does not exclude all prices. Positive D-CH excludes
  support at every admissible subgradient for every physical plan.
* If D=CH, every physical planner optimum is supported by each attained common
  hull-dual optimizer. This does not say every subgradient at that plan supports
  it. Differentiable quadratic supply has the stated unique gradient convention.
* An individual whole-fleet owner's deviation can replace every service
  assignment. Separate owners require explicit compatible resource rights;
  reserved-pair results do not automatically extend to a shared depot.
* Bills evaluated at fixed posted prices are not a strategic tariff-reset game,
  and lost opportunity is not automatically an implemented uplift payment.

No public sign resolution, external replication, universal pricing claim, or
new ML result is asserted by this planning document.
