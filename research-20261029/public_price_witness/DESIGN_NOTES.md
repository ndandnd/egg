# New price witness: objective interface and scientific claims

This is source-only preparation, not execution or a repair of a historical
raw result. The saved PRICE_MIP routes are a new fixed-topology input; its
old charges, reported loads and failed strict screen remain immutable and
are not replayed. One new charge-only linear program uses all original
charging opportunities on those routes at the already certified incumbent's
fixed own-price vector.

The qualified recover_primal API compares its problem objective with the
original physical verifier's quadratic cost. Passing it an a=p,b=0 objective
would conflate two different costs. Instead, pass the original quadratic
problem and the new LP value proposal. The helper performs its one rational
quadratic tie-breaking construction on the proposed zero/active face and
screens that NEW rational point once using the original verifier. This gives
a physical upper whether or not it minimizes the fixed-price problem.

Only afterwards form a separate objective descriptor a=p,b=0, retaining
identical variables, rows and bounds. Signed exact phase I/check_certificate
may certify fixed-route price optimality at the admitted values. An unresolved
or infeasible normal cone for that primal cannot erase its physical admission.
No original physical objective is overwritten, and no original audit is
relabeled as a linear-cost audit. A finite-dimensional face failure is not
fixed-route infeasibility. There is no second native method/face attempt.

Let x be the source-bound incumbent and y the new strict physical response.
At the fixed p=gradient F(e(x)), evaluate both private scores c+p.e exactly.
A positive score difference gives a valid lower bound on r(x;p), showing
that THIS incumbent is unsupported. It does not show D>CH, because x is
known optimal only on its own fixed topology.

For their two-plan hull segment let d=e(y)-e(x),
A=c(y)-c(x)+gradient F(e(x)).d, B=sum_t b_t*d_t²/2. Exact cost is
C(x)+lambda*A+lambda²*B. Clamp the rational stationary lambda to[0,1],
handling B=0 separately. Direct evaluation and exact endpoint/interior KKT
checks validate the segment minimum. An improving private response has A<0
and therefore supplies a strictly smaller hull upper than C(x). The mean
load is a whole-plan convexification, not automatically a physical schedule.

The old LP global response lower and native MIP OPTIMAL status are not
recomputed or used as exact physical/global planning certificates here. The
new fixed-route linear lower is also not a global full-fleet response lower.
The new hull upper may later be compared with an independently valid physical
lower bound, but no global gap sign is asserted by this package alone.
