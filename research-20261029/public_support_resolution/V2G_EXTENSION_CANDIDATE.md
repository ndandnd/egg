# Prospective bidirectional shared-connector extension

29 October, 07:52 UTC. New analytical hypothesis, not a numerical result or
novelty clearance. Independent adversarial proof review requested. No public
case assumption or old experiment is changed. No V2G native experiment,
cohort, command or manifest is authorized by this note.

Retain the heterogeneous two-batch model with a fixed allowed successor graph,
zero travel, ideal identical batteries B, full initial and terminal SOC, fee
f>0 per assigned bus, and every singleton duty. Allow every assigned bus to
use the early connector in either direction. In particular a standalone B
bus is initially full and present before its service. There are no additional
idle storage buses. The one early connector has symmetric power K, accepts
one bus at a time, and hence at most K gross kWh in its unit window. Terminal
charging has shared power H. Losses, degradation and switching time remain
absent. Signed net electricity is valued at the same posted price in each
direction; supply cost is defined on the resulting signed-load domain.

For matching M, m=|M|, N=2n-m and total service energy S, signed early q has
the following exact per-bus boxes:

- paired A_i,B_j: a_i+b_j-B <= q <= a_i;
- singleton A_i: a_i-B <= q <= a_i;
- singleton B_j: b_j-B <= q <= 0.

These follow directly from SOC before and after the second batch. Terminal
refill of each bus is its total service energy minus q, lies in [0,B], and
sums to S-E. Serial early actions must satisfy sum|q|<=K, not merely |E|<=K.

Put R(M)=sum_(i,j in M)[a_i+b_j-B]_+. The sum of all lower box endpoints is
S-NB, and the sum of all upper endpoints is A=sum_i a_i. At prescribed E,
the least gross energy is max(E,2R(M)-E): for E>=R, use only charging; for
E<R, keep mandatory positive charges at R and use available discharging
capacity R-(S-NB). Thus the proposed exact fixed-matching projection is

  max(S-H, S-NB, 2R(M)-K) <= E <= min(A,K).

Both inequalities include the gross early-connector and terminal limits.
They do not omit a separate |E|<=K condition: R>=0 makes E>=2R-K imply
E>=-K. Zero-power cases use no division. All buses have common availability
and accept connector power, so sequential monotone actions realize the
boxes and all terminal demands. This argument would fail with different
early release times, asymmetric acceptance, losses or switching overhead.

For r_m=min_(allowed |M|=m)R(M), define

  t_m=max(S-H, S-(2n-m)B, 2r_m-K), U=min(A,K), c_m=f(2n-m).

The proposed complete joint projection is the union of
(E,S-E,c_m) for t_m<=E<=U over feasible m. The minimum matching R gives
the widest interval, so no new multi-objective selection is hidden here.
Since r_m is nondecreasing and discretely convex, t_m has the same
properties as a pointwise maximum of three such sequences. Collapse only
equal-coordinate thresholds to their cheapest cardinality; retain physical
intermediate thresholds on collinear hull edges. The same piecewise-affine
cost frontier and physical-attainment support criterion should follow.
Feasibility itself is unchanged from charge-only: t_0<=U iff S-H<=U.
The energy interval can now extend below zero when H>S; a cost function
defined only for nonnegative grid load requires a declared background load
or an additional net-load restriction, not an implicit extrapolation.

Two proposed implications need independent verification:

1. A=(5,15), B-services=(14,15), battery20, K15, H49 retains t=(0,0,9).
   The previously proved positive gap would therefore survive all of these
   bidirectional charging alternatives with the same assigned-bus limit.
2. A=(1,1,19), B-services=(2,10,19), battery20 has S52 and r_3=1 under
   complete matching. With K>=2 and H52, t_3=0. V2G can offset a mandatory
   local early purchase using spare energy on another assigned bus, removing
   that final cardinality threshold. No value/support result is inferred
   without specifying and checking the full cost function.

This is an extension of the physical mechanism, not a claim that V2G,
bidirectional aggregation, matching convexity or EVSP-grid coupling is new.
It remains a narrow two-window ideal model and does not alter the public
37-service charge-only certification question.
