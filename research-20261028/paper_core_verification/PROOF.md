# Exact capacity and vehicle-cost characterization

Status before execution: analytical derivation reviewed; implementation qualification pending.
This extends the existing fee-7 threshold to all nonnegative vehicle fees in
the stated nominal family. It is not a new general convex-hull-pricing theorem,
and its originality beyond this project is not established by checking sources.

Assume precisely the two-service physical model in PROTOCOL.md. Let terminal
connector power be K in [0,30] kW and used-bus cost f >= 0. Since the terminal
window lasts one hour, K is also its energy capacity. All quantities below use
the fixed synthetic monetary and energy units of that model.

**Physical projection (all plans, not sampled plans).** One bus must recharge
at least 10 early kWh between services to avoid negative SOC; early capacity
is 10, so its load is (10,20). Two buses have early load x in
[max(0,30-K),10], and terminal load 30-x. These conditions are sufficient:
charge only A's bus early and refill A and B serially at power K after hour 3.
Both start/end full and all intermediate inventories stay in [0,20]. Before
B, its unused bus starts full, hence cannot charge early. No third partition
exists, up to bus labels. K<20 is infeasible. K=20 forces early load 10 in
both partitions, giving D=CH=f+90; both partitions tie only at f=0.

For K>20 put l=30-K, d=K-20, g(x)=90-2x+x^2/5,
t=max(5,l), and h=clamp(5+5f/(2d), l, 10). Then

    D  = min(f+90, 2f+g(t))
    CH = 2f - f(h-l)/d + g(h).

To prove the hull expression, first convexify the *physically feasible*
segments in (early load, operating cost). Its vertices are (l,2f), (10,2f),
and (10,f), with degenerate coincidences allowed. Because supply cost depends
only on early load after full energy balance, the cheapest hull operating
cost is 2f-f(x-l)/d. Differentiating its strictly convex quadratic objective
gives h. Both physical and hull minima are attained. The reference program
instead constructs vertices from raw SOC equalities/inequalities and minimizes
every hull edge; it imports none of these closed-form projection formulas.

**Necessary and sufficient gap condition.** For f>0 and K>20,

    D-CH > 0 iff max(0, (2/5)d(l-5)) < f < 2d.

Indeed positive gap occurs exactly when l<h<10. In that interior the hull
operating cost is strictly less than the two-bus cost at the same load, and
strict convexity excludes the one-bus endpoint from attaining CH. If h is
an endpoint, the corresponding physical plan attains CH. The stated strict
inequalities follow by substituting the unclamped h. At either equality
boundary gap is zero. For f=0, h=t and D=CH=g(t), so zero fee is separate.
This proof covers the continuous parameter domain; the finite tests below
only qualify its implementation, not the theorem by sampling.

**All planner ties and complete deviations.** One bus at x=10 and two buses
at x=t both minimize physical cost exactly when f=90-g(t). Otherwise retain
the cheaper partition. At every such optimizer use p=(4+x/5,(30-x)/5).
The posted tariff remains fixed over deviations. Its full best-response value is

    V(p)=min(f+10p1+20p2, 2f+l*p1+(30-l)*p2, 2f+10p1+20p2).

This checks the entire continuous opportunity set because each partition's
price objective is affine on its physical segment. A zero price difference
p1-p2 means the *whole* two-bus interval minimizes within that partition;
its full interval must be retained if it also minimizes across partitions.
Otherwise the appropriate endpoint suffices. Regret is c+p.e-V(p), for each
planner optimum separately. It is neither a strategic best response to a
tariff reset nor a payment or equilibrium result for shared independent owners.

**Existing fee-7 slice.** These expressions recover infeasibility below K=20,
zero gap on [20,47/2], and positive gap on (47/2,30]. In the positive regime,
D=97, gap=(1/5)(5-35/(2(K-20)))^2 and regret=2K-47. This slice was already
independently audited in the old study; its recovery here is a regression
anchor, not new evidence about operational prevalence.

Economic interpretation is conditional: extra terminal capacity expands the
fleet's choices and can *create* a support failure at some fixed fees. It does
not increase the planner's optimal cost. The geometry isolates that distinction;
it does not show that installing chargers worsens welfare or that typical
operators face this synthetic tariff.
