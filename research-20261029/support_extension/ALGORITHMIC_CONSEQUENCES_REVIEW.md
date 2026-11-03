# Independent mathematical review of algorithmic consequences

Source-only review of ALGORITHMIC_CONSEQUENCES.md and LOSSY_PROJECTION_CANDIDATE.md. No execution, experiment, input access, imports, tests, hashes or literature search. No consumed physical-refinement source was changed.

**Verdict: the decision reductions, support equivalence and three-generator argument are valid within the stated monotone common-loss model. The rational-exactness paragraph needs an explicit rational-generator assumption and existential wording.** These are material statement qualifications, rather than a counterexample to the physical reduction or finite convex program.

## Physical and hull reductions

The reviewed theorem supplies a physically attainable finite union Z of affine segments, with every original physical point dominated in both load coordinates at unchanged vehicle cost. Coordinatewise monotonicity of F therefore gives the same physical value on Z. Replacing every component of a physical mixture by its dominating Z component establishes the same hull value on conv(Z). This reasoning needs monotonicity on the domain of the comparisons and their means, including signed early loads; convexity alone does not suffice.

Segment minimization is convex because the loads are affine on each segment. For the stated separable quadratic, the scalar curvature and linear coefficient are correctly h=b_E+b_L B² and d=a_E+a_L B+b_L AB when L=A+BE. Zero curvature requires endpoint selection or retention of the complete flat segment, as stated. Endpoints and strictly interior kinks generate conv(Z); clipped feasible endpoints cannot be omitted. Duplicate, collinear and singleton records cause no correctness problem. This computes values and reduced optimizers, not every original cyclic or dominated optimizer under flat economics.

## Support, ties and zero gradients

For p>=0, domination establishes V(p)=min_j(c_j+p·u_j) on the entire original opportunity set. A segment's minimum occurs at an endpoint unless its private objective is constant. Thus the finite comparison decides **weak** support even at zero prices. It does not enumerate all responses: complete segments, discarded cycles or other dominated plans can tie when relevant price coordinates vanish. The source correctly retains this distinction.

Under differentiable convex F and admissible p=grad F(u)>=0, an own-load-supported physical point x satisfies, for every physical or convexified point y,

    c_y+F(u_y) >= c_y+F(u_x)+p·(u_y-u_x)
                  >= c_x+F(u_x).

It is consequently both a physical and hull optimum. Conversely, when D=CH and a physical optimum is attained, that point also minimizes over the convex hull. First-order optimality along every feasible segment gives c_y+p·u_y>=c_x+p·u_x, hence weak support. This establishes the stated existence equivalence without strict convexity and includes p=0 and nonunique optimizers. It presumes that the gradient is a legitimate admissible price under the supply formulation. Restricted price sets or a chosen nonsmooth subgradient require the extra qualifications already present in the source. Negative prices cannot use the dominance-based finite response oracle.

## Why three generators suffice

At a hull optimum z*=(u*,c*), differentiability supplies the supporting functional (p,1). If the polytope is three-dimensional, this nonzero normal exposes a proper face of dimension at most two. Every generator with positive weight in a representation of z* lies on that face: otherwise its weighted private score would strictly exceed the supporting value. Carathéodory within the face gives at most three generators. If the entire polytope has affine dimension at most two, Carathéodory already gives the same bound even when the functional is constant on the whole polytope. This covers collinearity, duplicate records, zero gradient and flat objectives. The operating-cost coefficient 1 is essential to the nonzero-normal argument.

Enumerating singletons, pairs and triples consequently contains an optimum; it need not cover the full three-dimensional polytope. The source does not claim a new general matching algorithm or a favorable bit/runtime complexity, appropriately.

## Rationality: two explicit qualifications

1. **Require rational generating coordinates, not only a rational quadratic.** Rational B, service energies, K,H, efficiencies and fee suffice: finite matching minima, thresholds, endpoints and kinks then remain rational. The broad physical theorem permits real parameters, so a rational objective alone cannot imply a rational optimum. A direct model counterexample is n=1, a=b=sqrt(2), B=4, K=0, H=4, alpha=delta=1, fee=1 and rational linear F(E,L)=L. The one-bus optimum has E=0, L=2sqrt(2) and value 1+2sqrt(2). This is feasible and monotone, but irrational.

2. Write **“there exists an optimum with rational loads, operating cost and weights”**, rather than suggesting that all optimum points are rational. On a rational segment with constant cost and F=0, every point is optimal, including irrational load coordinates. The value and a rational representative can still be exact.

With rational generators, the singular-PSD argument is sound. Choose an optimum in the relative interior of its minimal simplex face. Stationarity on that face is a rational affine linear system in barycentric coordinates, intersected with rational simplex inequalities. A real feasible solution implies a rational feasible representative. The stationarity equations together with PSD convexity certify optimality, so this representative has rational value and gradient. One must solve feasibility of that stationary system rather than invert a singular Hessian; proper boundary faces cover optima absent from the relative interior. The same reasoning extends to a general rational PSD quadratic with cross terms, although the displayed h,d formulas are specifically separable.

## Short certificate and scope

Exact feasible weights plus the exact-gradient private-score inequalities against every generator are a sufficient global hull certificate by the convex first-order inequality. To promote that finite certificate to the original physical hull/response problem, retain the monotonicity/nonnegative-price dominance assumptions; the source already states this correctly. The certificate may include ties and needs no uniqueness assumption.

Recommended disposition: integrate as a corollary or explanatory algorithmic consequence after adding the two rationality qualifications. No new numerical campaign is mathematically necessary for these deductions. This review neither establishes computational efficiency in practice nor adds a novelty claim beyond the reviewed physical reduction.
