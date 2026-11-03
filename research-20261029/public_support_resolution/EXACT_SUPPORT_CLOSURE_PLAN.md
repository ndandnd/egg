# Exact public support closure after the energy-flow phase

29 October 2026. Bounded mathematical/source-only design. No numerical execution, actual case-data read, imports, hashes or new implementation. The new certified upper is about 442.123; the independently justified three-or-more-bus physical floor is about 477.8235. Consequently a physical optimum uses exactly two buses. These facts do **not** restrict the complete-plan hull to two buses.

## A. The economical positive-gap target

Seek a rational physical lower `L_D` strictly above a rational feasible hull upper `U_H`. Exact values of D and CH are unnecessary. The energy-flow root certificate may already suffice; test that inequality first before commissioning a tree. If not, strengthen the **two-bus physical** lower bound by finite branching, while retaining the separate certified three-plus-bus physical floor.

### Construct U_H from admitted physical plans

Use only separately strictly admitted physical candidates. One component may be the protected terminal-construction witness; a raw native integer proposal that fails replay is not another component. Its explicit construction/admission would be a separate phase.

For two admitted projected plans `(e_0,c_0)` and `(e_1,c_1)`, put `d=e_1-e_0`, `dc=c_1-c_0`, and use the original exact binary-stored coefficients a_t,b_t. The complete-plan mixture at weight lambda has objective

`H(lambda)=c_0+lambda*dc+sum_t[a_t*(e_0t+lambda*d_t)+b_t*(e_0t+lambda*d_t)^2/2]`.

Define `A=sum_t b_t*d_t^2` and `B=dc+sum_t(a_t+b_t*e_0t)*d_t`. If A>0, the exact best segment mixture uses `lambda=clamp(-B/A,0,1)`; if A=0 choose the better endpoint (or record the whole segment when its linear slope is zero). All arithmetic and weights are rational. Independently recompute the two physical projections, simplex weight and mixture objective. Their mean is a hull witness, never an executable fleet.

Two plans are a cheap attempt, not a completeness theorem: positive gap can require a richer mixture. For a larger finitely admitted pool, rational simplex/KKT certification gives a valid U_H even without proving pool optimality. No pool lower bound certifies the complete hull. If the pool gives no useful strict separation, stop or prospectively authorize more globally priced physical columns; do not infer zero gap. Caratheodory gives a finite representation bound, not an economical way to find its components.

### Branch on movements while preserving the full graph

Use the exact per-leg energy-flow model, all original arcs and all original charging intervals. For the physical two-bus subproblem add the explicit equality `sum_pullouts y=2`. A node is only a list of selected movement decisions `(movement ID,0 or 1)`. The independent checker reconstructs these as exact equality rows `y_m=value` added to the unchanged base ledger; it must not accept arbitrary edited variable bounds, omitted arcs or author-supplied node matrices.

At a node choose any rational tangent load z, with `p_t=a_t+b_t*z_t` and `k=-sum_t b_t*z_t^2/2`. For the exact linear rows `A x sense b` and finite box `[l,u]`, project proposed multipliers to the correct signs: nonnegative for >= rows, nonpositive for <= rows, unrestricted for equalities. Let

`rho = objective_linear(p) - A^T*pi`.

Then the independently checked node lower bound is

`L_node = k + pi dot b + sum_j min(rho_j*l_j,rho_j*u_j)`.

This is precisely the exact box-residual argument already implemented in `exact_dual.py`, extended with independently reconstructed branch/cardinality rows and explicit **node/two-bus scope**. Native status, native bound, reduced-cost assertions and presumed primal feasibility are unnecessary proof inputs. A native QP solve is a multiplier/tangent proposal only. Missing proposals are unavailable, not automatic success or a hidden zero-vector replacement.

Prune a node when `L_node>U_H`. Otherwise branch on an unfixed original movement binary, producing both children y_m=0 and y_m=1. Preserve every child, including infeasible or interrupted ones. A complete integer assignment leaves the exact fixed-topology charging QP; do not replace that continuous problem by the raw candidate's schedule. An exact rational KKT reconstruction is an optional way to close a stubborn feasible leaf.

For an infeasible node, an independently checked rational Farkas/box certificate can close it. One convenient form sets objective zero and finds sign-valid pi such that

`pi dot b + sum_j min((-A^T*pi)_j*l_j,(-A^T*pi)_j*u_j)>0`.

Every feasible x would then satisfy `0>0`. A solver's INFEASIBLE status alone does not close a leaf.

### The tree certificate and final inequality

Publish a finite rooted proof tree. Each internal node names one previously unfixed movement; its two children append the complementary binary equalities. Every leaf has either a checked objective lower bound or a checked infeasibility certificate. Verify graph/row/price semantics once from cached admitted source, then independently verify each node's decisions, added rows, dual algebra and parent-child coverage. No search-node disappearance may be excused by undocumented presolve, a duty bank, or native pruning.

Let L_2 be the minimum checked objective bound among feasible/unresolved-feasibility leaves; infeasible leaves contribute +infinity. With complete tree coverage, `D_two>=L_2`. Reconstruct the elementary original-model three-plus-bus floor L_3 from nonnegative energy/cost and full inventory, or transfer its separately qualified exact certificate. The one-bus obstruction must also remain independently certified. Then

`D >= L_D = min(L_2,L_3)`.

If `L_D>U_H`, report the exact positive gap certificate `D-CH >= L_D-U_H>0`. This proves absence of own-load support. The strongest immediate stopping rule is to prune every remaining node as soon as its lower exceeds the fixed U_H; finding an exact optimal two-bus objective is unnecessary.

**Scope trap:** the two-bus node relaxation and its branch bounds are not unrestricted CH lower bounds. Physical three-plus plans can be individually too expensive to optimize D and still improve a hull mixture. The root unrestricted energy-flow certificate may bound CH; a cardinality-two tree only bounds physical D_two.

## B. A separate exact zero-gap/support closure

Given one admitted exact physical plan x, form its exact own-load gradient p and its exact private score `B_x=c(x)+p dot e(x)`. Certify `V(p)>=B_x` over the entire complete graph and all feasible fleet counts. The candidate itself supplies `V(p)<=B_x`. Equality then gives zero regret, and convexity proves x globally physical-optimal and `D=CH`.

This uses linear-price branch-and-bound with the same independently checked finite-box certificates. Three-plus plans may be omitted **only** after a valid linear-price exclusion, for example `3f+min_t(p_t)*E_service/eta >= B_x` for nonnegative prices and nonnegative movement costs. The earlier nonlinear physical floor is not sufficient for that omission. If such a pricing exclusion fails, retain those fleet counts or strengthen their valid linear-price bounds.

An arbitrary terminal-feasible construction is unlikely to be fixed-topology supply-optimal. A fixed-topology exact convex-QP KKT witness may first supply a suitable candidate x; it does not itself certify global support. Every other routing alternative must still be covered by pricing certification. A demonstrated positive regret at the current incumbent rejects support of that incumbent only, never all optimal fleets.

Zero-gap closure is intrinsically less tolerant than strict separation: a bound infinitesimally below B_x does not prove equality. Rational active-face reconstruction of an LP/QP dual can eliminate the residual. Merely converting approximate multipliers to their exact binary fractions may leave a small negative correction forever. An epsilon enclosure supports only an approximate-regret statement, not an exact sign conclusion.

## C. Prospective stops, cost and unavoidable combinatorics

Freeze the mixture components or admitted pool, branch rule, node/call/wall/CPU limits, source closure, certificate checker and publication policy before the new search. Keep the protected physical upper external to method success. Check trivial semantic contradictions and existing valid root bounds before a new native call. Cache immutable source semantics once; node certificates should reference a checked base rather than duplicate a large ledger at every node.

Stop with a positive-gap certificate only after exact strict separation and complete tree coverage; stop with support only after exact own-price equality over the full opportunity set. At budget exhaustion publish the admitted U_H, best valid global/root bounds, covered/open nodes and precise unresolved claim. Do not launch automatic extensions, silently repair new candidates, relabel a partial tree as a certificate, or reuse the two-bus physical exclusion inside an unrestricted hull assertion.

The worst case remains exponential in movement choices. Fixing fleet count two still leaves combinatorially many full path covers, and continuous charge feasibility remains coupled by one connector. A pricing decomposition into single-bus duties is not an exact complete-fleet oracle unless shared-resource coupling and exhaustive path pricing are proved. The full arc-flow tree avoids that additional equivalence obligation but does not remove the combinatorics. Rational KKT/Farkas certificates exist for the relevant rational polyhedral convex subproblems, yet locating them efficiently is not guaranteed by this design. A bounded unsuccessful search is a useful bound-improvement result, not public support resolution.
