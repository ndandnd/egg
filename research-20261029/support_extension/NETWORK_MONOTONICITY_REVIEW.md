# Network dispatch need not be load-monotone

PASS. The proposed three-bus example is feasible and globally optimal throughout0<=x<=1, and its incremental dispatch cost is strictly decreasing and convex. This is analytical verification only: no numerical execution, data, imports, hashes or tests. Negative marginal nodal prices and congestion-induced nonmonotonicity are established phenomena; no novelty, empirical or ML claim follows.

Use unit line susceptances, flow f_ij=theta_i−theta_j, and nodal balance generation minus demand equals outgoing flow. Let bus3 have demand1+x, bus1 demand4 and bus2 demand0. Fix theta3=0. Bus3 balance gives theta1+theta2=1+x, while bus1 balance gives

`g1−4=2theta1−theta2=3theta1−1−x`.

Thus `theta1=(g1−3+x)/3`. The symmetric line13 bound |theta1|<=1/2 implies the global feasible lower bound `g1>=3/2−x`. Total balance independently gives `g2=5+x−g1`.

The proposed dispatch attains that lower bound:

`g1=3/2−x`, `g2=7/2+2x`, `theta1=−1/2`, `theta2=3/2+x`.

Its oriented flows are exactly `f12=−2−x`, `f13=−1/2`, `f23=3/2+x`. For0<=x<=1, their magnitudes are at most3,1/2,5/2, respectively, within the declared5,1/2,5 limits. Generation lies in [1/2,3/2] and [7/2,11/2], within [0,10]. All nodal balances hold. In particular the negative13 flow is power from bus3 to bus1; a load bus can carry transit power without local generation. There is no physical-sign inconsistency.

## Global optimality

At fixed x eliminate g2 using total balance. The derivative of total cost with respect to g1 is

`3+g1/50 − (1+(5+x−g1)/50) = 2+(2g1−5−x)/50`.

On the entire feasible generator domain g1>=0 and0<=x<=1, this is at least `2−6/50>0`. Therefore total cost strictly increases with g1 throughout that domain. Every feasible dispatch obeys the line13-derived lower bound, and the displayed feasible dispatch attains it. This proves unique global optimal generation, rather than merely stationarity on a guessed active set. The connected network and fixed reference angle also determine the corresponding unique angles.

Expanding its objective yields

`F(x)−F(0)=−89x/100+x^2/20`.

Its first derivative is `−89/100+x/10<0` over the entire stated interval, and its second derivative is1/10>0. Both generator cost functions themselves have strictly positive first derivatives and strictly positive second derivatives on [0,10]. The falling optimized cost is therefore not caused by a decreasing generator bid. Increased demand at bus3 relaxes the congestion-imposed minimum of expensive generation at bus1 while increasing cheaper generation at bus2; the net redispatch saving exceeds the added supply cost.

## Correct practical scope

F is a single-period optimized dispatch cost along one specified nonnegative load increment, with background demand and network fixed. Loads, flows and generation can be expressed in consistent power units; cost is per dispatch period (or per time unit), and a fixed period converts this consistently to energy. Equal susceptance is normalized; the example is an ideal lossless DC network, not an AC-feasibility or empirical network claim. Incremental F may be negative even though absolute generation costs are nonnegative.

The common-loss frontier's monotone-objective premise is consequently substantive for a network-derived supply objective. Convexity and increasing generator costs alone do not establish coordinatewise monotonicity of the optimized nodal-load value. A model using the dominance reduction must check the relevant load-domain monotonicity or retain the alternatives that domination would discard. This example does not show that such a reduction fails on the manuscript's stated monotone synthetic objective, nor does it establish a new public-case result or a prevalence estimate.
