# Complete assignment graph with all perfect matchings feasible

Prospective analytical result: the proposed strengthening works. No data, code, calculations by execution, source audit or numerical qualification was used. The argument retains abstract compulsory transition tasks, not metric roads or optional detours.

## Construction and feasibility of EVERY matching

For k>=1 let w_i=2^i, w_min=1, w_max=2^(k−1), W=sum_i w_i, and B>=20w_max. In block i, each batch has a high service of energy B/2+3w_i and a low service of energy w_i. There are2k simultaneous services in each of two successive batches, at most2k buses, full initial/final inventory, zero reserve, unit efficiency, charge-only operation and fee f>=0 per bus. Keep the common A/early/task/B/terminal windows and nonnegative consumption assumptions of the reviewed block construction. Shared early power/budget is K=sum_i a_i=kB/2+4W. Increase shared terminal power/budget to H=2kB, with adequate per-bus acceptance. All other access and nonservice consumption remain zero.

The assignment graph is now COMPLETE. Within a block keep identity transition energy0 and cross transition energy6w_i. Between distinct blocks define d_ij=B−b_j. Each edge performs its prescribed nonnegative task over the same positive-duration noncharging interval; no alternative task/path can replace it. These are input energies, not claims about geographical travel or power-limited propulsion.

For an edge define e_ij=a_i+b_j+d_ij and r_ij=(e_ij−B)_+. Every edge satisfies b_j+d_ij<=B: equality on interblock edges, and the earlier B>=20w_max bound suffices for within-block cross edges. Thus 0<=r_ij<=a_i. On any perfect matching M, independent per-bus early purchase intervals [r_ij,a_i] sum to [R_M,K], where R_M=sum_M r_ij. For any E in that interval, terminal purchase is S_M−E, with S_M=sum_M e_ij.

The terminal budget does NOT prune these intervals: for each matched bus, e_ij−r_ij=min(e_ij,B)<=B, so S_M−R_M<=2kB=H. Also S_M−K=sum_M(b_j+d_ij)>=0. Therefore the ENTIRE branch R_M<=E<=K is feasible and realized by serial early charging and serial terminal refill. Endpoint SOC constraints imply intermediate feasibility because task/service consumption is nonnegative. In particular, full early refill x_i=a_i makes every perfect matching feasible. There is no favorable-matching exclusion hidden in this assertion. The simultaneous batches and cap force exactly2k buses and a perfect matching, excluding singleton/idle/extra-bus escapes.

## A global affine certificate

Use row and column potentials with the same block values

    p_high(i)=B/2+9w_i,   p_low(i)=w_i.

Their combined sum over all rows and columns is M0=kB+20W. Every within-block edge satisfies e_ij+2r_ij=p_i+p_j: the identity high edge has e=B+6w_i,r=6w_i, the identity low edge has e=2w_i,r=0, and either cross edge has e=B/2+10w_i,r=0.

For an interblock edge, e_ij=a_i+B and r_ij=a_i, so e_ij+2r_ij=B+3a_i. Its surplus over p_i+p_j is uniformly at least

    gamma = w_max+2w_min >= 3.

Indeed a high row leaves surplus2B−p_j, at least3B/2−9w_max>=21w_max. A low row i to a high column j gives B/2+2w_i−9w_j>=w_max+2w_min; a low-to-low edge gives B+2w_i−w_j>=19w_max+2w_min. These estimates cover every added edge, regardless of which other edges a permutation uses. They also work when k=1, where there simply are no interblock edges.

Since every matching uses each potential once,

    S_M+2R_M >= M0,

with surplus at least gamma when any interblock edge occurs. Every physical point on its branch consequently satisfies

    3E+L=S_M+2E >= S_M+2R_M >= M0.

All within-block perfect matchings remain present. Their corners are z_R=(R,M0−3R), with R=6t,0<=t<=W. The same affine lower bound holds throughout the FULL complete-plan convex hull; it was not derived by ignoring the added assignments.

## The support-gap corollary and corner survival

Take F(E,L)=3E+L+(E−3)^2/(2K). Its monotonicity/convexity are unchanged and K>=14. The equal mixture of the retained R=0 and R=6 corners attains (3,M0−9). The affine bound proves CH=M0+2kf for the full complete graph. Within-block schedules have physical minimum M0+2kf+9/(2K), exactly at corners0 and6. Every interblock schedule costs at least M0+2kf+gamma, which is strictly greater because gamma>=3>9/(2K). Thus

    D=M0+2kf+9/(2K),  D−CH=9/(2K)>0

still holds for EVERY k>=1,f>=0, now with every perfect matching physically feasible. No newly feasible assignment can invalidate the sign. As before, this excludes own-marginal-price support under the classical assumptions, not every pricing mechanism.

For EACH retained corner R*, the earlier objective F_R*=3E+L+(E−R*)²/(2K) makes that corner uniquely optimal in projected coordinates: every within-block objective is >=M0, with equality only E=R=R*, while any interblock schedule has objective >=M0+gamma. The derivative in E is at least2 on the nonnegative domain because R*<=K, so these are coordinatewise strictly increasing convex objectives. Hence all2^k distinct convex-optimal corner loads survive on the COMPLETE graph. Allocation/schedule uniqueness is not asserted.

## Exact scope

Do NOT claim that the old entire efficient pieces or complete physical projection are unchanged: added matchings introduce new branches and might alter efficient portions away from the retained corners. The global affine certificate and corner-specific objectives prove precisely the survival claims above, not an exhaustive new frontier classification.

The retained corners remain collinear and share price(3,1); no exponential hull-vertex/price-region count or optimization hardness follows. Magnitudes grow exponentially in k, but an explicit dense binary input still has polynomial size; symbolic compression is not excluded. The construction is intentionally structured and uncalibrated, with adequate instance-dependent connector powers. It shows that neither graph sparsity nor outright infeasibility of added perfect matchings is necessary for the obstruction. Arbitrary roads, access changes, bounded propulsion rates, prevalence and novel generic multiobjective theory remain outside its claim. Independent proof review is required before manuscript integration.
