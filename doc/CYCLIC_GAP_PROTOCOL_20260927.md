# Fully replenished continuous-charging witness: frozen protocol

Prospective seed-free analytical study, 27 September 2026. Freeze this protocol
and `src/experiments/cyclic_gap.py` in Git before execution. This is an explicit
four-period model, not an unverified claim about the production EVSP adapter.

Two mandatory depot-to-depot services each consume 15 kWh: service A in [0,1],
service B in [2,3]. Up to two identical used buses each start and finish at
20 kWh, which is also battery capacity; reserve is zero. Charging is continuous
and lossless. The early window [1,2] has shared limit 10 kWh and individual
limit 10 kW. The terminal window [3,4] has shared limit 30 kWh and individual
limit 30 kW. No charging occurs during either service. Unused buses do not
contribute initial energy, costs or load. All trips are mandatory; no other
operations, travel energy, idle draw, plug-count or taper constraints exist.

There are exactly two unlabeled service partitions. One used bus serves A,B;
its early charge is exactly 10, its terminal charge 20. Two used buses serve A
and B separately; early charge x belongs to A's bus and may range over [0,10],
with terminal charges 15-x and 15. Both structures buy exactly 30 kWh and end
with their starting energy, removing the previous depleted-terminal accounting.
The terminal window is a declared part of this model, not a dummy service.

With f>0 per used bus and early tariff intercept a (late intercept zero), define
G(x)=a*x + (x*x+(30-x)*(30-x))/10. Units are synthetic currency and kWh.
Physical cost is min(f+G(10), 2f+min_{0<=x<=10}G(x)). The complete convex hull
uses one-bus weight lambda and scaled two-bus early energy y, satisfying
x=10*lambda+y, 0<=y<=10*(1-lambda). As f>0, the cheapest mixture at x has
lambda=x/10 and y=0, hence convexified cost is
min_{0<=x<=10}(2f-f*x/10+G(x)). This is convexification of complete schedules,
including per-structure power limits before mixing.

The nominal illustrative case is f=7,a=4, chosen analytically before execution.
It is a construction, not a sampled prevalence claim. Run the full fixed
Cartesian grid f in {1,3,7,10,15,20}, a in {0,2,4,6} (24 cases). The exact
physical minimizer is clip(15-5a/2,0,10) for the two-bus branch; the hull
minimizer is clip(15-5a/2+f/4,0,10). Compare all costs with Fraction arithmetic,
retain zeros and all cases, and generate explicit boundary-energy witnesses.

Nominal additional checks: compute own-price best response over the three
complete-schedule vertices; distinguish fleet and supply LOC at the common hull
price. Demonstrate a convex combination as a lower-bound construction, not a
physically dispatchable fractional fleet or a randomization saving. Independent
review must inspect both physical partitions and reproduce results without
importing the author driver. No solver, protected outcome, training data or
cluster allocation is required. Preserve exclusive output directories, source,
protocol and Git identities. Expected runtime below one second; external
execution cap 30 seconds. No learned proposal or operational claim is tested.
