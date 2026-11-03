# Support under additional feasible complete plans

This is an exact analytical statement for the declared model, not evidence of
operational prevalence or a new general pricing theory. No computation is used
in this proof. Complete plans, not single vehicle duties, are the economic
alternatives.

## General expansion statements

Let X be the old plan set, Y the added set, and Z=X union Y. Their images in
(load, operating cost) space are nonempty compact sets (or omit empty Y).
Use the identical proper closed convex supply function F for every set, finite
on all physical loads. Assume the manuscript's strong-duality/attained-price
qualification for the expanded hull as well as the old hull. Define D_A, CH_A,
V_A(p), and r_A(x;p) as in the manuscript. Assume Delta_X=D_X-CH_X>0.

For every retained x and every unchanged price p in the subdifferential of F
at e(x), V_Z(p)=min(V_X(p),V_Y(p)) <= V_X(p). Hence

    r_Z(x;p) >= r_X(x;p) >= Delta_X > 0.

No old unsupported plan can become supported through expansion. This does
not imply global failure survives: a new plan can be supported. Under the
stated qualification, failure disappears exactly when D_Z=CH_Z, equivalently
when some new plan y minimizes c+p.e over all Z at some p in its own supply
subdifferential. For differentiable F, this is precisely the pair of tests

    c(y)+p.e(y) <= V_X(p),
    c(y)+p.e(y) <= V_Y(p),       p=gradient F(e(y)).

All minima above are attained by compactness and continuity of linear
objectives; physical objectives attain minima by lower semicontinuity. Since
CH_Z<=CH_X<D_X, erasure necessarily requires D_Y<=CH_X. It is not sufficient.
Conversely min(D_X,D_Y)>CH_X is sufficient for survival. In particular,
D_Y>=D_X implies Delta_Z>=Delta_X.

### A certificate preserving the old hull value

Fix any attained old hull-dual optimizer p*. Suppose every y in Y satisfies

    c(y)+p*.e(y) >= V_X(p*).                         (C)

Then V_Z(p*)=V_X(p*). Its dual certificate proves CH_Z>=CH_X, while inclusion
proves the reverse inequality. Thus CH_Z=CH_X. For any physical y, its cost
minus CH_X is the sum of two nonnegative terms:

    [c(y)+p*.e(y)-V_X(p*)]
    + [F(e(y))-p*.e(y)+F*(p*)].

Consequently erasure under (C) occurs exactly when an added y makes both
terms zero: fleet equality in (C) and p* in the supply subdifferential at e(y).
For strictly convex F the supply equality fixes the unique old hull-optimal
load, and fleet equality fixes its operating cost. Thus the new physical plan
must implement that old hull-optimal projected point. If (C) instead holds
with a uniform positive margin epsilon, the same identity yields

    Delta_Z >= min(Delta_X, epsilon) > 0.

This certificate does not assert that every expansion satisfies (C).

## Genuine movement-only expansion with unchanged nominal equipment

Keep the nominal two depot-to-depot services A=[0,1], B=[2,3], each consuming
15 kWh; at most two battery20 buses; fee7 per used bus; initial and final SOC20;
lossless charging only in [1,2] at shared/per-bus power10 and [3,4] at
shared/per-bus power30; no V2G. Retain every original schedule. Additional
allowed movements may consume nonnegative energy and incur nonnegative extra
operating cost, but introduce no service change, battery change, charging
window/location, energy recovery, or inventory transfer.

Full replenishment makes any added plan's total grid energy 30+w, w>=0.
Its early energy u lies in [0,10]. With two buses, the old two-bus plan having
load (u,30-u), cost14, is feasible and componentwise dominates the added plan
of load (u,30+w-u), cost at least14. With one bus, completion of both services
before terminal charging requires initial20 plus early energy at least30
plus any preterminal movement consumption. Hence u>=10; the early cap forces
u=10. The old one-bus plan (10,20), cost7, dominates it. Some added movements
are infeasible; this argument concerns every feasible added plan.

The nominal F(E,L)=4E+(E^2+L^2)/10 is coordinatewise nondecreasing on the
nonnegative orthant. Thus each added plan has an old physical dominator and
cannot decrease D. Replacing every added component in any finite hull mixture
by its old dominator also cannot increase operating cost or any load component,
and therefore cannot increase the supply objective. This proves

    D_Z=D_X=97, CH_Z=CH_X=7591/80, Delta_Z=169/80.

The proof is about permitted complete-plan expansions under these resources.
The original zero-movement model already exhausts its two service partitions;
an arbitrary extra projected point cannot be called an omitted feasible duty.

## Changed-equipment expansion: battery B and fee h

Now explicitly change available equipment: retain battery20 buses of fee7,
and add battery-B buses of fee h, with 20<=B<=30 and h>=7. Two buses of each
type are available but at most two buses total may be used. Preserve all
services and charging constraints above, with one terminal connector of power30.
Each selected bus starts and ends at its own full capacity. This is equipment
expansion, not additional duties of the unchanged homogeneous model.

Put a=30-B in [0,10]. An old one-bus plan has early energy10 and fee7. A new
one-bus plan has early energy x in [a,10] and fee h: after A its SOC is B-15,
after early charging B-15+x, after B B-30+x>=0. Capacity imposes x<=15,
so the shared early cap10 is tighter. Terminal purchase is30-x and fits the
connector. Every two-bus type assignment permits x in [0,10], total energy30,
and costs at least14; the old-old assignment of cost14 therefore dominates
all mixed and new-new assignments in projected economic comparisons. Those
assignments remain physical alternatives and must be retained in complete
argmin reporting when their fees tie.

Let g(x)=90-2x+x^2/5 and t=max(5,a). The physical value is

    D_Z=min(97, h+g(t)).

Since no old plan can be rescued, support exists precisely when the new
one-bus branch's own physical minimizer t is supported. At price
p=(4+t/5,(30-t)/5), compare its bill with every old one-bus plan, every old
two-bus plan, and its own whole interval. Its own branch minimizes at t
because either t=5 gives equal prices or t=a>=5 gives increasing early-price
cost. For a<=5, t=5 gives p=(5,5), so support holds iff h=7. For a>5 the
best old two-bus response charges zero early. The two comparisons give

    h <= A(a)=14+2a-(2/5)a^2,
    h <= C(a)=7+(10-a)((2/5)a-2).

Therefore the exact equipment-expansion support condition is

    a<=5 and h=7,
    OR a>5 and 7<=h<=min(A(a),C(a)).

Both inequalities are weak: boundary ties count as support. They automatically
imply physical optimality by convexity and the support inequality. Outside
this region no plan is supported and the expanded physical-hull gap is
strictly positive under the compactness and qualification assumptions. The
region for a>5 is nonempty only when a<=(5+sqrt(95))/2. Here A-C=27-4a,
so C is the smaller upper bound below a=27/4 and A above it. This criterion
is not a claim that every enlarged battery restores support.

For h=7 this reduces to B >= (55-sqrt(95))/2, approximately22.6266.
Below that threshold put t_h=5+35/(2a). The hull optimum has early load t_h,
operating cost14-7t_h/a, and positive gap (a-t_h)^2/5. At and above the
threshold the physical point (max(a,5),30-max(a,5),7) attains the hull.
This exact boundary, rather than the finite selected B values, is the proof
of the entire equal-fee battery regime.

### Complete battery25 fee threshold and instructive cases

For B=25, a=5. For all h>=7,

    D_Z=min(97,85+h),
    CH_Z=85+h-(h-7)^2/20       for 7<=h<=21/2,
         7591/80               for h>=21/2.

To obtain the hull formula, the old hull boundary is14-(7/10)x. The new
endpoint (5,h) lies below that boundary iff h<21/2. In that regime the new
lower boundary joins (0,14), (5,h), and (10,7). The objective decreases along
the first edge and has its minimum on the second at x=5+(h-7)/2. At h=21/2
the two formulas agree; above it the new segment is dominated by the old hull.

Thus the gap is (h-7)^2/20 for 7<=h<=21/2, is85+h-7591/80 for
21/2<=h<=12, and is169/80 for h>=12. Support is restored only at h=7.
At h=7 the new x=5 plan attains D_Z=CH_Z=92 and is supported at (5,5).

At h=8, the new physical optimum costs93, strictly below the old hull value
7591/80, but CH_Z=1859/20=92.95, giving gap1/20. Its own-price regret is1.
This is a counterexample to sufficiency of D_Y<=CH_X: the expanded hull also
improves. Its hull minimum has x=11/2 and operating cost79/10.

At h=12, old one-bus x=10 and new one-bus x=5 tie at physical cost97;
CH_Z remains7591/80. Their own-price regrets are13 and5 respectively.
For every h>=7 the old one-bus plan's regret remains13: at (6,4) the old
two-bus zero-early bill134 beats the new one-bus minimum h+130 and the
old one-bus bill147. For a new x=5 planner optimum (h<=12), its equal-price
bill exceeds the old one-bus bill by h-7. All planner ties must be reported.

Optional nonnegative-energy movements obey the preceding dominance argument
relative to their same-type no-movement plans, so they do not change these
equipment-expansion values when all original no-movement alternatives remain.
