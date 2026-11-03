# A radius-dependent upper bound for quadratic supply

27 September 2026. Principal-researcher derivation; independent review pending.
This is an explanatory bound, not a novelty claim or new solver experiment.

Let the complete physical opportunity set have compact cost/load image
`K={(c(s),L(s)):s in S}`. Its convex hull is therefore compact. Let
`F(L)=a·L+(1/2)LᵀBL`, with symmetric positive semidefinite B, on a domain
containing all physical loads and their convex hull. Supply is the corresponding
quadratic restricted to nonnegative quantities if needed. Let `(c*,L*)` minimize
`c+F(L)` on `conv(K)`, and write `p*=a+BL*`. For any physical schedule s, put
`H=c(s)+F(L(s))−CH`, so H is nonnegative. At a physical optimum, H is the
planning gap Δ. Define the seminorm `||z||_B=sqrt(zᵀBz)` and the physical
load diameter `R_B=max_{s,t in S} ||L(s)−L(t)||_B`.

First-order optimality on the convex hull implies that `(c*,L*)` minimizes
`c+p*·L` on the same hull. A linear objective has the same minimum on K and
its convex hull. Consequently, with `V(p)=min_s[c(s)+p·L(s)]`,

`V(p*)=c*+p*·L*`.

The fleet's lost opportunity at the common hull price is therefore exactly

`LOC(s;p*)=c(s)+p*·L(s)−V(p*)=H−(1/2)||L(s)−L*||_B² >= 0`.

This step follows directly from the quadratic identity; no unconstrained
supply optimizer, strict positive curvature or interior load is required.
Set `d=||L(s)−L*||_B`, so `d<=sqrt(2H)`. Let t be a complete physical
price response at s's own price `p_s=a+BL(s)`. Then

`r(s)=c(s)+p_s·L(s)−c(t)−p_s·L(t)`

`<= LOC(s;p*) + [L(s)−L*]ᵀB[L(s)−L(t)]`

`<= H−d²/2+d R_B <= H+sqrt(2H) R_B`.

The first inequality uses `c(t)+p*·L(t)>=V(p*)`; the second is
Cauchy–Schwarz in the positive-semidefinite seminorm. The argument includes
singular B and B=0. If H=0, d=0 and LOC=0, hence regret is zero. Compactness
ensures all stated minima and the diameter are attained; extensions to
noncompact sets would need separate hypotheses. No division by an eigenvalue
or assumption about a strictly interior supply quantity occurs.

For the original cyclic replication, `B=(1/(5n))I` and complete loads have
`E in [0,10n]`, `L=30n−E`. Thus `R_B=sqrt(40n)`. With nearest integer
`m=27n/40+δ`, the physical optimum has `d²=40δ²/n=2Δ`, and its fleet LOC
at the hull price is zero. The sharper displayed inequality gives
`r<=40|δ|<=20`; on `n=40k+1`, it gives `r<=13`, consistently with the
exact regret approaching 8.775. The loose diameter grows as sqrt(n), so a
vanishing O(1/n) planning gap alone does not force this whole-fleet bound to
vanish.

Under the separately reviewed reserved-pair institution, every assigned pair
is a best response at the common hull price. A pair's load diameter in the
same aggregate B-seminorm is `sqrt(40/n)`. The shared price displacement d
therefore bounds each individual's regret by `40|δ|/n<=20/n`, recovering
the direct calculation. This uses the stated rights and common posted prices;
it is not an inference about unreserved shared-resource games.

The practical interpretation is quantitative: a small planning gap controls
own-price regret jointly with the range of feasible load changes and supply
curvature. It does not supply an empirical effect estimate or turn a numerical
gap interval into an exact physical certificate. For a feasible schedule and
a verified lower bound L_CH on CH, H can be conservatively replaced in the
looser monotone bound by `c(s)+F(L(s))−L_CH`, provided R_B itself is validly
bounded and all feasibility/numerical conditions are respected.

## Review resolution

Two non-author mathematical reviews passed the derivation above. The Astra
review checked nine adverse finite-set schedules and all88 archived replication
optima; the separate review also gives a valid piecewise sharpening. The proof
uses price-taking throughout: p_s stays fixed during the deviation. Each
reserved pair's zero LOC at p* is an additional, verified property of this
particular institution, not a claim for arbitrary bounded participants. The
review hashes identify the original derivation before this resolution note;
no mathematical formula has changed.
