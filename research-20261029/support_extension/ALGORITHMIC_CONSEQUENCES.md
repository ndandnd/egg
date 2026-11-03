# Algorithmic consequences of the common-loss physical reduction

Source-only mathematical derivation from the reviewed common-loss frontier. No experiment, case selection, imports, tests, hashes, raw inputs or runtime claim. This is useful as a concise decision consequence of the theorem, not a new general matching/convex-optimization algorithm. Any manuscript addition should receive an independent mathematical review.

## What the physical result supplies

First obtain the classical minimum-cost cardinality matching values r_m, m=0,…,nu, on the declared allowed graph. This can use an ordinary integral bipartite min-cost flow/matching procedure; it is not necessary to enumerate complete fleet assignments. The specific physical theorem then produces t_m,U and the curve

    (E,L_m(E),c_m),  E in[t_m,U],
    L_m(E)=S/alpha−E+kappa*[r_m/alpha−E]+,
    c_m=f(2n−m).

Discard only empty intervals. If none remain, the physical model is infeasible; the optimization and support statements below assume a nonempty set. Retain each interval's left/right endpoints and the kink r_m/alpha when strictly interior. Each feasible cardinality contributes at most two segments and three generating points; a singleton contributes one point. Thus there are at most2(nu+1) segments and M<=3(nu+1) point records. Duplicate/collinear points may be retained safely. A lower threshold inside a segment must not be replaced by an unclipped matching endpoint.

These quantities give decisions for ALL objectives within the monotone class, rather than just the schedule selected by one fleet MILP objective. The actual application-specific content is that r_m alone suffices despite different assignments, inventory limits, conversion losses and gross shared throughput. Matching solvers, segment minimization and convex-hull pricing remain established tools.

## Physical planning: linearly many convex one-dimensional problems

For finite continuous convex F, coordinatewise nondecreasing on a domain containing all relevant dominance comparisons, minimize

    c_m+F(E,L_m(E))

separately on each affine segment. Each is a convex one-dimensional problem. The minimum over at most2(nu+1) such problems is the exact physical value D. An optimizing segment point has a physical realization by the theorem's constructive exchange allocation and an r_m-attaining matching. Retain ALL tied points/intervals if the task is to enumerate physical optima; selecting one representative computes the value but not the full optimizer set. Cyclic/dominated physical plans may also tie under flat economics, so this reduced enumeration is not automatically every original plan optimizer.

For separable rational quadratic economics

    F(E,L)=a_E*E+a_L*L+(b_E*E^2+b_L*L^2)/2,
    b_E,b_L>=0,

and a segment L=A+B*E, its scalar curvature is h=b_E+b_L*B^2 and linear coefficient d=a_E+a_L*B+b_L*A*B. If h>0 the minimizer is the exact rational clip of −d/h to the segment endpoints. If h=0, choose the appropriate endpoint when d has a sign, or retain the entire segment when d=0. Singleton intervals require no division. All original coefficients must be rational under the declared interpretation; substituting intended decimal rationals for stored binary coefficients changes the problem.

Monotonicity is an additional condition, not implied by b_E,b_L>=0. For this quadratic require a_E+b_E*E>=0 and a_L+b_L*L>=0 throughout a stated order-convex domain containing the relevant physical/hull loads and replacements. In particular negative early loads can violate an otherwise familiar nonnegative-price assumption. Without the theorem's economic monotonicity, reduced D need not equal original D.

## Convexified planning: finite convex program and exact quadratic treatment

Let v_j=(E_j,L_j,c_j), j1..M, be the generating records. Hull planning becomes the finite convex program

    minimize sum_j lambda_j*c_j + F(sum_j lambda_j*E_j, sum_j lambda_j*L_j)
    subject to lambda_j>=0, sum_j lambda_j=1.

This computes the original CH ONLY under the common-loss theorem's monotone reduction assumptions. It is a convexification of complete physical points; arbitrary interval allocations are not relabelled as physical mixtures. The mixing weights need not describe an executable single-day fleet.

Assume additionally that the generating coordinates are rational. Rational physical data (service energies, B,K,H, efficiencies and fee) suffice; a rational quadratic objective alone does not. Under this assumption, exact rational optimum certificates are justified. At an optimum z*=(E*,L*,c*) of this finite polytope, differentiability gives a supporting plane with normal(p_E,p_L,1), where p=gradF(E*,L*). The last component is1, so the supported face has affine dimension at most2, even if the polytope is full-dimensional in three dimensions. A point on that face is a convex combination of at most THREE generating points. The same bound holds if the whole polytope has dimension at most2. No four-component mixture is needed for an optimum of this particular objective.

Therefore one finite exact solution procedure is to consider every generating singleton, pair and triple and minimize the quadratic on its simplex. At most M+choose(M,2)+choose(M,3) constant-dimensional convex subproblems suffice. These triangles need not cover the entire three-dimensional polytope; the supporting-face argument shows that they contain an optimum. Each simplex subproblem is handled by its finite active faces and rational linear stationarity equations. On a singular face, do not invert a zero Hessian or discard the face: test the rational affine stationary system together with nonnegative barycentric coordinates, or use its boundary faces. A nonempty rational linear system/polyhedron has a rational feasible representative. Consequently there exists an optimum with rational loads, operating cost and barycentric representation, and with rational value and gradient. This is an existence statement: a flat optimum set can also contain irrational points. Multiple optimum representations/flat faces can remain.

This is a finite active-face method for THIS explicit small-dimensional frontier. It is not a claim that general electric-vehicle scheduling, arbitrary nonconvex aggregation or every convex oracle objective has an exact rational solution. Nor is it a demonstrated runtime/bit-complexity improvement over existing solvers. A generic strictly convex nonquadratic objective can have irrational optima; rational exactness should not be transferred to it.

## A short exact hull certificate

A proposed rational optimum can be checked without re-solving all simplices:

1. Its nonnegative rational weights sum to1 and reconstruct the proposed point from generating physical records.
2. Its objective is evaluated in the exact declared quadratic and p is its exact gradient.
3. For EVERY generating record, verify c_j+p_E*E_j+p_L*L_j >= c*+p_E*E*+p_L*L*.

Convexity of F makes these inequalities a global supporting-plane certificate on convZ. If the reduced-point price vector is nonnegative, physical dominance extends that linear lower to the entire original physical set as well. Otherwise the finite-polytope certificate alone does not establish an original full-response value through dominance. For the earlier monotone differentiable quadratic assumption, p>=0 follows on the stated domain. This distinction matters at signed-load boundaries.

## Own-marginal support: value decision, not all price responses

For an arbitrary feasible physical plan x and admissible own-load gradient p, if p_E,p_L>=0 then

    V(p)=min_j(c_j+p_E*E_j+p_L*L_j).

A linear functional attains its segment minimum at a generating endpoint or is constant over a whole segment. Thus comparing x's private bill to this finite minimum decides weak support exactly, including ties. Zero prices do not invalidate the VALUE or yes/no support decision, but can leave extra discarded cyclic/dominated plans tied; endpoint-only output must not be advertised as the full response set. Negative prices require the unreduced opportunity set, so this formula is not a valid general response oracle for them.

Alternatively, compute exact D and CH. Under the framework's supply/price-attainment qualification, D=CH iff some physical plan has admissible own-load support. For differentiable F with unrestricted nonnegative gradient convention as above, a positive gap excludes every such plan; at zero gap a physical optimum realizes the supporting hull point. If admissible economic prices are further restricted, existence of an admissible supporting price must still be checked, rather than inferred from strict convexity alone. With nonsmooth F a single chosen subgradient's failure does not decide existence across all admissible subgradients. None of these statements yields a tariff-reset equilibrium or convergence of a price iteration.

## Recommendation

The linear number of physical convex subproblems, explicit finite hull program, and short rational supporting certificate are useful consequences worth a small algorithmic corollary or explanatory paragraph. The at-most-three-point exact active-face construction is an optional appendix detail if useful for implementation/reproducibility; it should not become another disconnected lead theorem. Emphasize the physical reduction enabling these decisions, not a new optimization or generic polynomial-time claim. No new numerical campaign is needed to state these deductions correctly.
