# Independent corollary review: positive gap with exponentially many alternatives

PASS. This is an analytical consequence of the already reviewed complete family projection, without computation, data, or a new physical construction.

Write `M=S_max` and `c=2kf`. Every physical point is on exactly one of the declared branches

`R=6t`, `0<=t<=W`, `R<=E<=K`, `L=M−2R−E`.

Here `W=2^k−1`, `K=kB/2+4W`, and `B>=20 max_i w_i`. In particular `K>=14`, and `6W<=K`, so both corners R=0 and R=6 and their midpoint exist for every k>=1. The fleet cap and simultaneous batches exclude singleton, partial-matching, extra-bus and idle alternatives; this is the whole physical projection under that cap, not a selected subset.

Take

`F(E,L)=3E+L+(E−3)^2/(2K)`.

Its Hessian is diagonal `(1/K,0)`, hence positive semidefinite. On the full nonnegative orthant its derivatives are `3+(E−3)/K >= 3−3/K>0` and1. It is smooth, convex and coordinatewise strictly increasing. Joint strict convexity is unnecessary.

For every physical point,

`3E+L=M+2(E−R)>=M`.

This affine inequality also holds throughout the complete-plan convex hull. Therefore every convexified point satisfies

`c+F(E,L)>=c+M+(E−3)^2/(2K)>=c+M`.

The equal mixture of corners `(0,M)` and `(6,M−18)` attains `(3,M−9)` and equality. Thus `CH=M+c`. Equality forces E=3 and `3E+L=M`, so the optimum is unique in projected load/cost coordinates. This argument covers the entire hull, including all later segments, without assuming an unproved hull diagram or ignoring further alternatives.

On a physical branch the objective is

`M+c+2(E−R)+(E−3)^2/(2K)`.

Its derivative in E is `2+(E−3)/K >= 2−3/K>0`; hence the branch minimum occurs at E=R. Among all R=6t, the nearest values to3 are exactly0 and6, both at distance3. Consequently

`D=M+c+9/(2K)`, and `D−CH=9/(2K)>0`.

Both physical optimal projected corners are retained; no third branch or interior point ties them. Fee f>=0 merely adds the same c to every physical and convexified point, so the conclusion includes f=0 and all k>=1. The hull gradient at its optimum is `(3,1)`; it supports the common corner line but does not eliminate the positive planner gap. At a physical optimum, the usual support criterion gives strictly positive own-marginal-price regret.

This strengthens the stated boundary example: even with all2^k efficient matching alternatives present, a positive support gap remains. It does not say that adding alternatives always preserves gaps, that the gap is uniform in family size, or that optimization/hull description is hard. Its exact size decreases as K grows. No operational prevalence, empirical routing, or generic hardness inference follows, and the common-transition-consumption theorem remains outside this edge-dependent construction.
