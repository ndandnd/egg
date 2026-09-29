# Nonsmooth support and price coordination review

29 September 2026. Scope: theoretical edits to `model_theory.tex`, the opening
proofs in `proof_appendix.tex`, and the replication interpretation in
`exact_results.tex`. No new solver or empirical result is asserted here.

## Support with a convex dispatch value

Let the complete-fleet cost/load image be compact, let `F` be proper closed
convex and finite on every physical load, and set `E = conv{e(x)}`. The hull
minimizes `c+F(e)` over the joint cost/load hull; the physical problem minimizes
the same expression over complete fleets. For every physical `x` and every
`p in ∂F(e(x))`, the fleet response `V(p)=min_y {c(y)+p·e(y)}` gives

`r(x;p)=c(x)+p·e(x)-V(p) >= c(x)+F(e(x))-CH >= D-CH`.

This needs no differentiability. If the subdifferential is empty at a boundary
load, the own-price test is undefined there until an admissible price is
specified. With `ri(E) ∩ ri(dom F) != ∅`, Fenchel–Rockafellar duality gives
an attained maximizer of `Q(p)=V(p)-F*(p)` and `max Q=CH`. A second sufficient
case is a finite convex minorant of `F` on the full vector space that agrees
with `F` on `E`; it covers the manuscript's nonnegative-domain quadratic via
the unrestricted quadratic formula. Thus `D=CH` iff some physical plan is a
best response at some price in its full subdifferential. If equality holds,
every physical planner optimum is supported by every attained dual optimum.
The conclusion for a *restricted* economic price set needs a supporting dual
optimum inside that set. In particular, a boundary normal introduced solely
by imposing `L>=0` on an otherwise unrestricted cost should not be named a
generation marginal price without a corresponding dispatch multiplier.

For convex generator dispatch `H(d)` with background demand `b`, use the
incremental value `G(L)=H(b+L)-H(b)` and the full extended-valued feasible
domain of that dispatch. A balance multiplier of a solved dispatch is an
economic candidate price. With capacity or ramp constraints, `G` may be
nonsmooth and may be infinite at infeasible demand. The full subdifferential
can be larger than the projection of a particular generator dual formulation;
the price-set choice must be declared. If some fleet alternatives are outside
the supply domain, the deviation set or emergency supply rule must also be
declared. Nonconvex generator commitment calls for a separate generator hull
analysis.

## What dual decomposition establishes

At price `p`, choose a global fleet minimizer `x_p` and a convex supply
response `u_p in ∂G*(p)`. Then `e(x_p)-u_p` is a supergradient of the concave
dual `Q(p)=V(p)-G*(p)`, and a projected ascent step is

`p_{k+1}=Π_P[p_k+α_k(e(x_k)-u_k)]`.

Projection must use a declared closed convex price set `P`; restricting to
`P` changes the dual problem unless it contains an unrestricted optimizer.
The fleet solve must be global for an exact supergradient. Standard bounded
subgradient arguments give a best-iterate or stepsize-weighted average dual
value guarantee under a bounded price region, bounded supergradients, and
stepsizes with divergent sum and suitable cumulative squared-step control.
For `α_k=0.5/√k`, `Σα_k²` diverges logarithmically. The textbook bound is of
order `log(K)/√K` for the best or weighted-average dual suboptimality, not
automatically for each last iterate or a unique price. A vanishing or
square-summable schedule can support stronger statements under its own
assumptions; those cannot be imported to `1/√k`.

Positive `D-CH` rules out a convergent subsequence with a physical fleet
response, a supply response, and zero balance residual at a common attained
dual optimum. Such a joint limit would be a balanced physical primal/dual
pair and force `D=CH`. It does **not** imply every price algorithm oscillates,
that prices converge, or that physical schedule iterates can never settle.
The manuscript's exact two-cycle concerns only its specified undamped update.

The pasted two-service trace mixes quantities. At `p=(5.50,4.50)` in the
nominal model, direct evaluation gives `V(p)=149`, `F*(p)=56.25`, and current
`Q(p)=92.75`, rather than `94.887`. The latter is the exact optimum of the
hull dual and may have been a best-so-far value in the trace; without the
iteration log it should not be labeled the dual value at that displayed price.
The claimed `0.5/√k` run and 20,000-solve count are exploratory and should not
enter the paper as verified algorithm evidence.

## Aggregation scope

Shapley–Folkman reasoning applies to sums of separately bounded participant
sets with fixed coupling dimension. It bounds aggregate convexification
effects in terms of the dimension and individual nonconvexity; normalized
effects can shrink as many suitably small participants are added. It does
not universally make the absolute gap vanish or make the regret of a single
composite operator vanish. The manuscript's `Δ_n<=5/n` and its positive
`O(1)` whole-operator regret along `n=40k+1` are exact properties of its
specific scaled quadratic cost, fleet set, and deviation right. The
`O(1/n)` reserved-pair incentive uses separate connector rights and is a
different institution. Hreinsson et al. (2021) is relevant aggregation
context, not a proof of these constants or rates.

## Subsequent implementation

The critique above concerns the supplied, unlogged trace. A separately specified
EGG replay was subsequently implemented under `SUBGRADIENT_PROTOCOL.md`, with
its complete trace retained under `results/`. `INDEPENDENT_REVIEW.md` verifies
that new run. Draft 0.9 uses this reproducible run, not the supplied table.
