# Complete-graph strict-curvature robustness: independent review

PASS, with the relative-neighborhood scope specified below. This is an analytical verification, without execution, data, imports, hashes or numerical qualification.

Put M=Smax=kB+20W, eta=1/4, K=sum a=kB/2+4W, H=2kB+1. Retain both original intra-block edge energies and add every interblock edge with compulsory consumption d_ij=B−b_j−eta. All batches/windows, the fleet cap2k and common connector access remain fixed. Every matching is consequently perfect, and every plan has the same operating cost c=2kf. The new transition energies are positive: b_j<=13B/20, so d_ij>0.

## Every perfect matching is physically feasible

For one edge let t_ij=a_i+b_j+d_ij and r_ij=[t_ij−B]+. A paired bus has exactly the early interval [r_ij,a_i], provided b_j+d_ij<=B. Interblock edges satisfy b_j+d_ij=B−eta<B and r_ij=a_i−eta>0, hence have strictly positive early-interval width eta. Intra-block edges also have strictly positive widths under B>=20max w. Their post-early demands fit strictly below B. Thus every perfect matching has R=sum r_ij<K.

For any such matching, S−R=sum min(t_ij,B)<=2kB<H. Terminal capacity therefore never cuts off its minimum early point. Its complete projection is the nonempty interval

`R<=E<=K`, `L=S−E`, `c=2kf`.

All early and terminal amounts serialize on their respective common connectors; per-bus acceptance equals or exceeds connector power. Each terminal amount is at most B, and nonnegative consumption guarantees intermediate reserve bounds. Also S−K=sum(b_j+d_ij)>0. These are full physical branches, including every interblock matching; no assignment is discarded for convenience.

## A uniform separating margin for interblock matchings

Define row and column potentials in each block by p_big=B/2+9w and p_small=w. Their combined sum over all services is M. Every original intra-block edge satisfies

`t_ij+2r_ij = p_i+p_j`.

For an interblock edge,

`t_ij+2r_ij = B+3a_i−3eta`.

If its A endpoint is small, B+3a_i−p_i−p_j>=B+2w_i−19B/20>=3, since B>=20 and w_i>=1. If it is big, that difference is 2B−p_j>=21B/20>=21. Thus each interblock edge has potential slack at least3−3eta=9/4. Consequently every physical branch satisfies S+2R>=M, and a matching with h interblock edges satisfies

`3E+L=S+2E>=M+(9/4)h`.

This potential bound handles the complete graph, not only blockwise permutations.

## Exact physical and hull values

For the proposed objective

`F(E,L)=3E+L+(E−3)^2/(2K)+(L−(M−9))^2/(4M)`,

the Hessian is diag(1/K,1/(2M)), positive definite. On the entire nonnegative orthant, partial_E F>=3−3/K>0 and partial_L F>=1/2+9/(2M)>0. Thus F is smooth, jointly strictly convex and coordinatewise strictly increasing.

The affine bound3E+L>=M holds throughout the full hull; both square terms are nonnegative. The equal mixture of the retained R=0 and R=6 block corners attains (3,M−9), so CH=M+c, uniquely in projected coordinates.

On every block-only branch, L=M−2R−E<=M and the derivative along its segment is

`2+(E−3)/K−(L−(M−9))/(2M) >= 2−3/K−9/(2M)>0`,

using K>=14 and M>=40. The branch minimum is its corner. At a corner its excess above M+c is

`(R−3)^2 (1/(2K)+9/(4M))`.

Exactly R=0 and R=6 minimize this, giving delta=9/(2K)+81/(4M). Any interblock matching instead has objective at least M+c+9/4, even before its square penalties. Since delta<=9/28+81/160<9/4, none can tie or improve the two old corners. Hence the WHOLE problem has

`D=M+c+9/(2K)+81/(4M)`, `D−CH=9/(2K)+81/(4M)>0`.

## Open relative neighborhood: a rigorous continuity argument

Fix one finite k and its complete labeled topology, batch timing, connector policy, fleet cap and dimension. Allow sufficiently small perturbations of service/transition energies, B, connector budgets and quadratic coefficients/linear terms/centers. Restrict to the admissible parameter space: nonnegative consumption, identical start/end-full convention, fixed access, and nonnegative fee; if K=sum a or other defining identities are retained, take the relative topology of that parameter subspace. At f=0 this is a relative neighborhood in f>=0, not an ambient neighborhood allowing negative fees.

There are finitely many perfect matchings. At the displayed point every per-edge early interval has positive width, every post-early demand has positive capacity slack, every matching has R<K, and every minimum terminal demand is strictly below H. Finite minima of these positive margins remain positive in a sufficiently small neighborhood. If independent connector budgets vary, the projected interval endpoints are

`lo=max(0,R,S−H)`, `hi=min(sum a,K)`;

they are continuous and remain strictly ordered. Therefore each complete branch varies continuously in Hausdorff distance, as does their finite union and its convex hull. All nearby sets lie in a common bounded box. Continuous supply objectives varying continuously with their parameters then have continuous physical and hull minimum values (equivalently apply the minimum theorem to interval parameterizations and finite mixtures). Their strictly positive nominal difference remains positive on a sufficiently small relative neighborhood. Positive definite Hessian and strict global coordinatewise monotonicity persist by the displayed coefficient/derivative margins for separable quadratic perturbations; more general quadratic perturbations require explicitly retaining monotonicity on the relevant domain.

This proves an open relative robustness claim, not unchanged exact formulas, persistence of the same two physical minimizers, or the same hull mixture after perturbation. The neighborhood may shrink with k and the gap tends to zero as the scale grows. No uniform family-wide radius, operational prevalence, road realization, hardness inference or public-energy certificate transfer follows.
