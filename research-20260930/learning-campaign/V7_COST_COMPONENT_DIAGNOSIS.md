# V7 saved cost-component diagnosis

The graph’s common15 mean bill gap of+4.599760 cost units versus the predeclared source policy is entirely charging/supply cost. All three learned arms have exactly the same fleet count and operations cost as their selected source policy on every common15 timetable. This audits the already-reviewed saved plans; no inference, replay, optimization or new solve is run.

| Same common15 | Mean Δoperations | Mean Δlinear tariff | Mean Δquadratic supply | Mean Δbill | Same winning-source topology | Novel vs any admitted source |
|---|---:|---:|---:|---:|---:|---:|
| tabular_v3 | +0.000000 | +0.183704 | +0.296668 | +0.480372 | 2/15 | 12/15 |
| families_v5 | +0.000000 | +2.209926 | +0.621957 | +2.831883 | 1/15 | 13/15 |
| graph_v6 | +0.000000 | +3.919111 | +0.680649 | +4.599760 | 2/15 | 11/15 |

Every common15 vehicle delta is zero; observed operations costs are100units per vehicle. Graph’s supply loss splits into+3.919111 linear tariff and+0.680649 curvature. Different movement covers, rather than an extra vehicle on these15cases, accompany the loss: graph differs from the winning-source movement set on13/15cases and is novel against the entire two-source bank on11/15. Topology novelty alone is not a cost improvement.

For the fixed `day` tariff (cheap periods10–13 at0.10, other periods0.30), linear cost can be rebased exactly as0.30·total grid load minus0.20·cheap-period load. The paired arithmetic separates energy quantity from where charging occurs; it does not estimate a causal effect of changing routes or tariff.

| Same common15 | Mean Δgrid kWh | Mean Δcheap-period kWh | Δquantity at high tariff | Δcheap-period discount | Δcurvature |
|---|---:|---:|---:|---:|---:|
| tabular_v3 | +3.829630 | +4.825926 | +1.148889 | -0.965185 | +0.296668 |
| families_v5 | +5.717037 | -2.474074 | +1.715111 | +0.494815 | +0.621957 |
| graph_v6 | +1.663704 | -17.100000 | +0.499111 | +3.420000 | +0.680649 |

Graph uses only1.663704more grid kWh on average, but17.100000fewer kWh in cheap periods. Thus its linear gap is+0.499111 from quantity at the high-tariff reference plus+3.420000 from a smaller cheap-period discount. The remaining+0.680649 is the quadratic load term. The bulk of the graph bill gap is therefore observed tariff allocation, not fleet count or simply more total energy. These are identities of the saved loads, not causal counterfactuals.

On10071 graph’s−0.041949bill delta combines−1.973333linear cost with+1.931385curvature: cheaper linear charging is almost cancelled by the curved term. Conversely, on10075 graph is+9.465424worse despite−0.141243curvature, because linear tariff cost is+9.606667. This motivates charging-opportunity and full supply-cost awareness within same-fleet route construction; it does not select an architecture from these outcomes.

The common15 cohort is unchanged from the reviewed replay and contains every timetable where all primary arms replayed.10069 remains missing for family and graph because of their existing5-second cover caps. The successful tabular plan there uses6vehicles against source5: its+113.915027bill gap is+100operations and+13.915027supply. Across all16 tabular outcomes, mean gap remains+7.570038 (=+6.250000operations,+1.320038supply); it is not replaced by the common15 result. No missing cost is imputed.

All component and paired-mean identities hold exactly using rational arithmetic on the known market coefficients and saved replay loads. Near-zero bill signs and the prior report’s post-hoc0.01descriptive tolerance are unchanged. The two-source source policy, INNER promotions, failures and all spent time remain fixed. These TRAIN observations do not separate causal route opportunity, load scheduling and solver effects, and provide no optimality/speedup or DEV/TEST claim. All32hull failures remain outside usable scientific scope.
