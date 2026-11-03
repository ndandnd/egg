# A source-defined sufficient condition and a falsifiable mechanism

25 October 2026. STATIC mathematical analysis only. No case/plan values, tables,
new outcomes, project imports, hashes, replay or solver were read/run. This is
classical optimization reasoning, not a proposed new theorem, numerical bound
certificate or an assertion about the previously inspected stored cases.

## What is being valued

Fix a physically valid ordered route collection r. Let c_r be vehicle/deadhead
operating cost, D_r the sum of mandatory service energy and selected movement-leg
energy, and eta the common charging efficiency. In the ideal physical model,
initial and terminal battery states are both full, so required grid energy is
E_r=D_r/eta. This does not depend on charging time. Different route collections
can change D_r through deadhead and auxiliary waiting even at equal fleet count.

Let P_r(p) be the set of aggregate period grid-energy vectors achievable by some
physically feasible charging schedule on those fixed routes under resource
parameter p, with all pathwise reserve/headroom and shared-resource constraints.
Value at tariff(a,b) is

    V_r(a,b;p) = c_r + min_{L in P_r(p)} sum_t[a_t L_t + b_t L_t^2/2].

The source fixes b>=0 and this is the integrated system-cost objective, not an
atomic uniform-price bill. P_r refers here to exact ideal physical feasibility.
It is not automatically identical to the finite-precision copied matrix or the
set of replay-admitted floating witnesses; this note creates no code certificate.
No global routing optimality follows from optimizing one r.

## Terminal-only common opportunity

Suppose all vehicles on r have physically returned to the depot by a common
opening h and have no further service before common deadline H. Assume their
selected movement/service energies are nonnegative, every vehicle's total draw
D_{rv} is at most battery minus reserve, all start full, and the only remaining
requirement is full replenishment. Thus each vehicle can execute its whole route
without intermediate charging and can receive its deficit at the final visit.

For one serial connector with common bus/grid rate P(t), any aggregate terminal
load profile supported on[h,H], bounded by P(t), and with total grid energy E_r,
can be allocated sequentially among the vehicles' deficits. Preemption/splitting
is allowed, as in the source's charging-segment representation. Each vehicle
receives exactly its deficit and never exceeds its battery. All final visits
cover the common interval. In ideal period-energy notation this supplies a
common subset T(E_r;p) contained in P_r(p). For the value bounds below require
T to be nonempty, including enough total terminal capacity to deliver E_r.
It is a sufficient condition, not
necessary: failing a no-intermediate-charge check does not prove infeasibility.

Let A(E_r;p) retain only total energy and horizon/shared-power bounds, dropping
route windows and SOC timing. It is a relaxation, so

    T(E_r;p) subset P_r(p) subset A(E_r;p).

For two routes with equal operating cost and equal E, if an optimizer of the
coarse relaxation A lies in the common terminal set T, both route values equal
that common relaxed value at this tariff. Proof: minimization over a superset
is a lower bound; the same attaining terminal schedule is feasible in both
routes and supplies the matching upper bound. No equality of the full projected
sets is needed. Conversely, agreement at two tariffs does not establish set
identity, dominance or this sufficient condition.

Even without attainment, the same construction gives a classical diagnostic
bound: each route value lies between c+min_A f and c+min_T f. For equal c,E,
their absolute ideal-value difference is at most min_T f−min_A f. This is useful
only when both set-inclusion/physical-attainability assumptions are established;
it is not a bound supplied by the old native receipt. A tighter common outer
relaxation may exclude intervals unavailable to BOTH routes rather than include
the whole horizon. If neither route has a selected daytime charging opportunity,
the union of available charging intervals may itself be terminal-only.

Important caveat: not needing intermediate charging does NOT alone make routes
economically interchangeable. Optional daytime depot charging may reduce the
quadratic supply cost or exploit a cheaper period. A common terminal subset
must attain the relevant relaxed price objective before the sandwich closes.
Even if total energy is equal, route-specific windows/SOC can matter outside it.

## What the current SOURCE implies, and what it does not

physical_learning_cases.make_case defines at most14 two-trip duties. Its latest
start is360+30*13+8=758 minutes, with maximum first/wait/second duration31+25+31,
so the final service ends by845 and pullin travel ends by851. The declared common
terminal opening is1080, deadline1800, grid/bus rate90, one connector. Therefore
THIS SOURCE generator supplies a long common post-service refill interval.
This is a source statement, not a new verification of old stored rows or of
any original route's battery sufficiency. Stored-case truth must be admitted
prospectively in any future numerical experiment; no cases were generated here.

Source0 has flat a=.20; source1 has a=.10 in hourly periods18–21 and .30 elsewhere,
with b=1/900. Those four cheap hours lie in the common terminal interval. The
quadratic term and required E determine whether noncheap/earlier opportunities
can improve value. No actual group energy, battery utilization or bindingness
is inferred here. The pilot's near-equal points cannot supply those facts.

For the source1 tariff there is a simple sufficient price condition. With a
constant effective rate p<=90 kW, the four cheap hours can hold4p kWh. If a
route's required E<=4p and the common terminal allocation above is physically
available, equal allocation E/4 across those four hours minimizes the coarse
relaxation: cheap marginal cost .10+(E/4)/900 is at most .20, below every
noncheap initial marginal cost .30. Hence equal-c/equal-E routes satisfying the
terminal condition have the same ideal source1 value in this range, regardless
of different daytime opportunities. At90/45kW the sufficient energy ceilings
are360/180kWh. These are symbolic consequences of the SOURCE parameters, not
claims that any inspected group's energy lies below a ceiling. The flat source0
tariff has no analogous preference for those four hours; optional daytime
spreading can still lower its quadratic cost. This supplies a specific competing
prediction to be tested rather than assuming every tariff reversal is routing.

## Mechanism and competing explanations to test

Mechanism: reducing effective shared charging power can make route-dependent
opportunities important by making common terminal recourse insufficient or
expensive. The relevant object is feasible load/energy recourse, not arc-label
Hamming distance. Predict a resource interaction only where an ex-ante physical
opportunity measure changes, not simply for the previously favorable10018 group.

Competing explanations: (i) route energy/operating-cost differences account for
the contrasts, without timing value; (ii) routes retain essentially the same
relevant load opportunities as resources tighten; (iii) conventional routing
plus charging captures the value, leaving no useful learning increment; (iv)
solver/admission uncertainty, failed acquisition or fallback selection prevents
an informative comparison. Preserve each rather than promote available cells.

A credible falsification is that the fixed prospective resource restriction
creates no material operational interaction once energy/operations and competent
classical charging are accounted for, or that a simple classical policy matches
any retained benefit. Do not vary caps or select cases until the desired effect
appears. If that happens, concede/redirect; membership learning has no special
justification from this mechanism. A negative result is not a proof of universal
equivalence, and a positive classical mechanism is not ML information value.
