# Strict curvature and a relative open robustness neighborhood

Analytical candidate only; no instance, numerical execution, data, import, hash or experiment. The proposed strengthening is sound under the same abstract common-window compulsory-task model. Its robustness conclusion is local for each fixed finite family member, not a uniform or public-instance perturbation theorem.

## Strengthened construction

Retain the complete-graph family: k>=1, w_i=2^i, w_min=1, B>=20w_max, high/low services (B/2+3w_i,w_i) in both batches, exactly2k buses forced by simultaneous services and fleet cap, K=kB/2+4W, and M=S_max=kB+20W. Physics is charge-only/unit efficiency with full initial/final batteries and the common early/task/terminal windows. Keep within-block task energies0/6w_i. For interblock edges set

    eta=1/4,  d_ij=B−b_j−eta,

and set terminal budget/power H=2kB+1, with adequate acceptance. Here eta denotes an ENERGY margin, not charging efficiency. Every added task energy is positive because B−b_j>=B/2−3w_max>=7w_max. Post-early energy is b_j+d_ij=B−eta, strictly below capacity. Its early requirement r_ij=(a_i+b_j+d_ij−B)_+=a_i−eta>0, since a_i>=1.

Every matching has the complete early interval [R,K], with R=sum r_ij, and terminal load S−E. Each edge still satisfies 0<=r_ij<a_i: on a high/high within-block edge a_i−r_ij=B/2−3w_i>0; on its other within-block edges r=0 and a_i>0; on added edges the margin is eta. Thus R<K for EVERY matching. Also S−R=sum min(e_ij,B)<=2kB<H. The increased H admits all intervals with strict total terminal-budget slack. In particular full early refill is feasible for every matching and leaves strictly positive eta inventory after its added-edge post-early task/B portion. For robustness one can instead choose EVERY x_ij strictly between r_ij and a_i, giving early-budget slack, strict preterminal lower/upper SOC margins, and terminal-budget slack simultaneously. Full terminal SOC remains an equality satisfied by adjusting refill, not by assuming unused initial inventory.

## Exact strongly convex support gap

Use

    F(E,L)=3E+L+(E−3)^2/(2K)+(L−(M−9))^2/(4M).

Its Hessian is diag(1/K,1/(2M)), positive definite. On the full nonnegative orthant its derivatives are at least3−3/K>0 and1/2+9/(2M)>0, so F is coordinatewise strictly increasing as well as strongly convex.

Keep the earlier potentials p_high=B/2+9w_i,p_low=w_i. Within-block edges remain tight for c_ij=e_ij+2r_ij. An added edge's c_ij drops by exactly3eta relative to the previous complete-graph construction. Its slack is therefore at least

    gamma−3eta >=3−3/4=9/4,

where gamma=w_max+2w_min. Hence EVERY physical point has3E+L>=M, and a matching containing any added edge has3E+L>=M+9/4. The affine inequality also holds on the full convex hull. The equal mixture of within-block corners0 and6 gives (E,L)=(3,M−9), where both square terms vanish. Therefore CH=M+2kf for all f>=0, uniquely in projected coordinates by strict convexity.

For a within-block branch L=M−2R−E, differentiation along E gives

    2+(E−3)/K−(L−(M−9))/(2M)
      >=2−3/K−9/(2M)>0,

because E,R>=0 and hence L−(M−9)=9−2R−E<=9. Each such branch minimizes at its corner E=R. Its excess there is

    (R−3)^2 * (1/(2K)+9/(4M)).

Exactly R=0 and6 are nearest3. Thus their excess is g=9/(2K)+81/(4M). Since K>=14 and M>=40, g<=9/28+81/160<1<9/4. All added-edge schedules have at least9/4 affine excess and nonnegative square penalties, so none improves those physical minima. Consequently the ENTIRE complete-graph instance has

    D=CH+9/(2K)+81/(4M)>CH.

Both physical minimizing corners are retained. The strict-support consequence is the same classical one as before. This does not assert practical magnitude, a uniform gap, or a new generic robustness theorem.

## A genuine relative open neighborhood

For EACH fixed k and chosen finite B, positive gap and feasibility of ALL perfect matchings persist in a sufficiently small relative open parameter neighborhood. Fix service counts/order, full-fleet cap, complete graph, common positive-duration windows, charge-only/unit-efficiency law, zero other draw, and the compulsory-task interpretation. Allow finite numerical parameters (service/task energies, capacity, resource budgets and separable quadratic economic coefficients) to vary continuously, within their nonnegative/positive admissible domain. Zero within-block task energies sit on that domain's boundary: the neighborhood is relative, not a ball allowing negative task energy. Any acceptance parameters must still permit the common-window serialization, or be varied only where the strictly feasible allocations remain valid. No new physics or additional tasks/routes are being added.

All service energies are strictly between0 and B, every post-early demand b_j+d_ij is strictly below B, and every edge r_ij<a_i. These strict margins persist locally. Because there are finitely many edges/matchings, their common margins can be chosen positive. At the base H>S_M−R_M for every matching, so all matching intervals have positive length and remain feasible locally. More generally their endpoints are

    lower_M=max(R_M,S_M−H),  upper=min(sum a_i,K),

continuous functions of the parameters; R_M=sum(e_ij−B)_+ is continuous even where a positive part changes regime. Their strict separation persists simultaneously for the finite matching family. Choosing interior per-bus allocations above explains why this is a real feasibility argument rather than mere continuity of an objective on a fixed feasible set.

Parameterize each branch by t in[0,1] between its continuous endpoints. Its load/cost/objective is continuous on that common compact domain. Uniform continuity implies continuity of its minimum; taking the minimum over finitely many matchings proves continuity of D. The full charge-only physical projection is a finite union of these affine segments. Its complete-plan hull is generated by their finitely many continuous endpoints and is parameterized by one fixed finite-dimensional simplex. The same compact-domain argument proves continuity of CH, including degeneracies and duplicate generators. Hence D−CH stays strictly positive in some neighborhood of the base positive value. Positive separable curvature and positive derivatives at the origin also persist locally, retaining strong convexity and monotonicity on the nonnegative orthant.

This supplies NO numerical radius, common radius over k, preservation of which matching/corner is optimal, unchanged full frontier, metric-road realization or calibration claim. The argument is not applicable to the public rounded-energy model merely because its gap is positive: here explicit feasibility margins and a fixed finite branch representation were proved; those prerequisites were unavailable in that public perturbation question. Any implementation or metered qualification would be separate, and none is proposed by this analytical note.
