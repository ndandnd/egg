# Continuous-cardinality hull proposal: REFUTED in general

Analytical counterexample, not a numerical experiment. Read lossy.tex and the heterogeneous model definitions only; no data, imports, execution, hashes or implementation. Piecewise-linear interpolation of the discrete convex matching values is a valid ingredient of a convex OUTER relaxation, but substituting it into the physical frontier formulas does not generally produce the complete-plan convex hull or preserve monotone planning values.

## The proposed set

Let r(m) interpolate r_0,...,r_nu linearly. Set N(m)=2n−m, c=fN(m), and impose the displayed four threshold inequalities with r(m), together with U=min(P/alpha,K), L<=H and

    L >= S/alpha−E+kappa [r(m)/alpha−E]_+.

The threshold coefficients of r are nonnegative, so these are convex inequalities when r(m) is convex. They hold on each integer-cardinality efficient branch. Consequently the resulting convex set contains conv Z (or its appropriate terminal-load epigraph). This proves the relaxation direction, not exactness. Taking a maximum/kink AFTER interpolation can introduce points below the interpolation of feasible integer branches.

## Exact one-service-per-batch counterexample, with genuine losses

Use n=1, the single allowed successor edge, a=b=15, B=20, alpha=1, delta=1/2, early gross budget K=10, terminal budget H=30 and fee f=16. These satisfy the original common-window/full-inventory/zero-reserve assumptions. Each service has its standalone bus alternative; the total fleet cap is2. Thus S=30,P=15,kappa=1 and U=10. The matching sequence is r_0=0,r_1=10, so its convex piecewise-linear interpolation is simply r(m)=10m. No nonconvex or incorrectly interpolated matching sequence is involved.

The exact integer frontiers from the theorem are:

| Cardinality | Fleet cost | Threshold | Complete efficient branch |
|---|---:|---:|---|
| m=0 | 32 | t_0=0 | 0<=E<=10, L=30−E |
| m=1 | 16 | t_1=10 | E=10,L=20 |

For m=0, T=S−2B=−10 and the four lower bounds are −5,−10,0,0. For m=1, T=S−B=10 and they are10,10,0,5. These also have transparent physical realizations. With two buses terminal capacity prohibits net export; early positive purchases reduce terminal refill one-for-one. The paired bus must purchase10 before its B service, exhausting the early budget, and then refills20 terminal units. The theorem already accounts for any dominated cyclic alternatives, so planning over Z and conv Z is exact for monotone supply.

Now set m=1/2 in the proposed relaxation. Then N=3/2, r=5,T=0,c=24. The four threshold terms are respectively5/2,0,0,5/2. Hence

    (m,E,L,c)=(1/2,5/2,30,24)

is feasible: its terminal epigraph value is30−5/2+(5−5/2)=30, meeting H exactly; E<=U and the interpolated battery/gross constraints hold. Explicit auxiliary totals would not fix it: purchases C=5 and exports X=5/2 give net E=5/2 and gross15/2<=10, consistent with those same fractional aggregate equations.

This point is not a mixture of the integer branches: EVERY point of conv Z obeys E+L=30, whereas it has E+L=65/2. More importantly, it improves a MONOTONE economic objective, so dismissing it as an irrelevant upward epigraph point does not rescue value exactness. Choose the fixed increasing convex supply F(E,L)=3E+L. The integer two-bus branch has objective32+30+2E, minimized at62. The paired point has objective16+30+20=66. A linear objective has the same minimum62 on their full convex hull. The proposed fractional point instead has

    c+F(E,L)=24+15/2+30=123/2 < 62.

Therefore the relaxation strictly understates the true hull planning value. Its fractional point is not dominated by any true convexified point in the relevant (E,L,c) coordinates. The cost improvement is not caused by numerical tolerance, an omitted service, infeasibility at an integer cardinality or using a nonmonotone supply objective.

Even joint strict convexity can be imposed without removing the counterexample. Add epsilon(E²+L²) with epsilon=1/10000. On the nonnegative feasible domain this is strongly convex and coordinatewise increasing. Every true hull objective is still at least62, whereas the same relaxed point costs123/2+epsilon*(3625/4)<62. No exact optimization of the perturbed objective is needed for that strict separation.

## Interpretation and exact compact alternative

The fictitious fractional fleet combines mandatory recharge, export capacity and terminal clipping as if all were physically available together at that fractional cardinality. A convex mixture instead allocates weights to COMPLETE feasible integer plans before averaging their loads and cost. Convexity of r_m alone does not make those operations commute. The failure already occurs between consecutive cardinalities with a linear interpolation; adding more breakpoints of r cannot address it. A lossless special-case counterexample also exists, but is unnecessary because this example has nonunit discharge efficiency.

There remains an exact compact continuous formulation already provided by the main theorem: take the at most3(nu+1) endpoint/kink records and use simplex weights on those records. Their convex combinations give conv Z exactly; m can be recovered as the corresponding weighted cardinality, but cannot replace the weights in the proposed inequalities. This is a standard finite convex-hull extended formulation and supports the existing rational quadratic certificates, not a new generic algorithm. Its size is linear in the number of cardinalities AFTER the matching values are computed.

Decision: do not promote the proposed r(m)-substitution formulation to the paper as an exact hull. It may be described as an outer relaxation only if that serves a separate purpose; no such experiment or new manuscript extension is recommended here. Identifying additional special assumptions under which a scalar continuous-cardinality description is exact would be separate theory, not an implication of discrete matching convexity.
