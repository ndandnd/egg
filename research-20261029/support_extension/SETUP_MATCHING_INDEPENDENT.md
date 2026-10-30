# Positive setup breaks exact minimum-requirement matching reduction

**COUNTEREXAMPLE.** Minimum summed early requirement is not an exact same-cardinality statistic with positive per-action connector setup. This holds on a complete2-by-2 graph, at unit efficiencies, with both perfect matchings feasible under the positive setup law. The failure concerns an actual missing load/cost point, not just a different schedule count. Independent symbolic reasoning only; no data, computation, imports, tests, hashes or other agent's withheld candidate were used.

## Instance

There are two simultaneous A services in[0,1] and two simultaneous B services in[2,3]. Their energies are

`a=(8,4)`, `b=(8,4)`, `B=10`.

All four successor edges are allowed and have zero time, energy and monetary cost. Every bus starts/ends full, reserve0, unit charging/export efficiency, common early access[1,2], terminal charge-only access[3,4], zero auxiliary draw, no taper or session fees. The shared early connector has charge/export power8, with each NONZERO early action requiring an additional setup1/4 of a time unit, occupying the same connector with no energy. Terminal power is20, accepted by each bus; terminal actions have no added setup. Fee is any f>0 and the total fleet cap is4.

Restrict attention to matching cardinality2, which uses exactly two buses and has operating cost2f. The complete graph has exactly two perfect matchings:

| Matching | Per-bus lower early requirements | Sum R |
|---|---|---:|
|Identity:8→8 and4→4|6,0|6|
|Cross:8→4 and4→8|2,2|4|

The cross matching is the UNIQUE minimum-R matching. Both have total consumption24, so all their full-refill loads satisfy E+L=24, even when neutral cycles are permitted.

## A physical point lost by the minimum-R choice

The identity matching physically attains

`(E,L,c)=(6,18,2f)`.

After A, its inventories are2 and6. On the8→8 bus, set up for1/4 of the early window and charge6 at power8 for the remaining3/4. Its inventory reaches8; the other bus does nothing early. After B, inventories are0 and2. Terminal refills are10 and8, totaling18, which serialize at power20 in less than one terminal window and restore both buses full. This is one nonzero early action, with all intermediate SOC bounds respected.

No cross-matching schedule can attain this SAME aggregate point. Each of its buses has positive required net early battery exchange at least2. Hence each bus must receive a positive charging action, even if it also exports or cycles. There are at least TWO nonzero early actions and therefore at least1/2 total setup time. Unit efficiency and E=6 imply C−X=6, so C+X=6+2X>=6. Total connector time is consequently at least

`(C+X)/8 + 2(1/4) >= 6/8+1/2=5/4>1`.

This rules out every cyclic or fragmented alternative, not just a one-direction construction or a guessed action order.

The cross matching is nevertheless feasible under setup time: charge2 on EACH bus, each using1/4 transfer time plus1/4 setup. The two actions exactly fill the window. Both buses then finish B empty and terminal purchases10+10=20 restore full. Its joint point is(4,20,2f). Thus the example does not rely on an infeasible minimum-R matching or an empty competing branch.

## A same-cardinality monotone value error

Every cross schedule has at least two charging setups, so its gross early energy is at most4. Thus E<=4. Its required net increments sum to at least4, so E>=4. At unit efficiency E=C−X and gross C+X<=4 therefore force E=C=4,X=0. The complete cross-matching projected load is exactly(4,20).

For the strictly increasing linear supply functional F(E,L)=E+2L, its score plus fee is44+2f. The identity witness gives42+2f. In fact any identity schedule with only one early action can transfer at most6 early units, while additional actions leave at most4 gross units and cannot meet its mandatory6-unit purchase; its complete projected load is(6,18). Hence the full cardinality2 optimum is42+2f, whereas keeping only minimum R gives44+2f.

This is a same-cardinality linear response/planning comparison, not a claimed global physical-hull gap. At fee2f, other cardinalities cannot reproduce the missing point when f>0; the two-bus layer and its convex hull genuinely lose it under the proposed reduction. For a linear objective the full cardinality hull minimum equals its physical minimum.

## Consequence for the approximation theorem

With zero setup, the minimum-R polygon contains the other matching's aggregate point because requirement4<=6 and total consumption/headroom/fleet agree. Positive setup makes the distribution of required exchange across buses matter: two small mandatory charging recipients can consume more connector setup time than one larger recipient. Summed R alone cannot encode that distribution.

The reviewed setup-free OUTER bound and finite-action INNER approximation remain valid; neither asserted exact minimum-R sufficiency for the true positive-setup set. Exact setup-constrained projection may require per-bus requirement/headroom information, action-pattern information or another richer statistic. This counterexample does not establish hardness, a minimal statistic, empirical switching behavior or any public-certificate conclusion.
