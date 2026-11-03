# What bound, and why most joint assignments did not qualify

All three strictly qualified joint assignments reached the **0.965 p.u. lower voltage limit at the far depot itself**. They share the January 17 primary windows and the 80% far-site design. Two used the high backup offer (mean-energy and heterogeneous fleet), and one used the low offer (heterogeneous fleet). Those 36 arm-quarter observations span 12 delivery timestamps.

The compact rows identify only solver bus 99 as voltage-active throughout. The native mapping identifies it as the 20 kV busbar `MV1.101 Bus 68` with two closed-switch aliases, native bounds [0.965, 1.055] and no imposed voltage setpoint. A native load and a fixed-injection generator are connected there. Its child 100 is a passive open-cable end. The independently fixed slack is bus 0, `HV1 Bus 17`, at 1.025 p.u. The global minimum voltage in the independent AC checks ranges from 0.964999999999827 to 0.965000000000166 p.u. across the 36 rows. The largest voltage difference between the two network models was 2.86e-12 p.u. No transformer or line terminal was flagged as thermally active in these rows.

Local generation was interior to its [0, 1] MW capability in all 36 rows (0.635351–0.999321 MW). Each reported window-mean depot price consequently matched that market's marginal local offer, €414.7235 or €510.5304/MWh. These constructed winter award scenarios show actual lower-voltage activity and paid redispatch. They supply no separate voltage shadow price and do not establish how often this limit binds on an operating system or in unresolved assignments.

## Joint qualification

| Mutually exclusive recorded outcome | Primary / 72 | Secondary / 72 |
|---|---:|---:|
| Qualified joint grid, AC, whole-fleet witness and count selection | 3 | 0 |
| Selected point and AC qualified, candidate comparison unresolved | 1 | 3 |
| Selected conic point optimal_inaccurate, independent AC passed | 64 | 27 |
| Hull-interval conic solver reported infeasible, no joint point | 4 | 6 |
| Fleet structurally infeasible before OPF | 0 | 36 |

The four qualified selected points that did not qualify joint selection each had one optimal_inaccurate competing integer-layer solve. For one secondary assignment (far/10%, January, hard supply), the hull solve was also optimal_inaccurate. The retained points therefore establish deliverability under the tested model while leaving that count comparison unresolved.

All 816 primary and 240 secondary **selected-point** quarter checks with an available joint point passed the frozen independent AC comparison and native limit screen. An accurate AC reconstruction cannot establish optimality. Of the 91 optimal_inaccurate selected points, 90 nevertheless met the saved mixed cone criterion in every quarter. For the remaining primary July near/40% mean-energy hard-supply assignment, four midday quarters exceeded the criterion with a worst discrepancy-to-tolerance ratio of 1.78334. The compact rows do not retain every conic residual separately, so a unique numerical cause for all inaccurate statuses cannot be reconstructed. The ten solver-infeasible hull results lack AC operating points. No missing assignment enters an estimate as a nonbinding observation.

Source-only diagnosis from the frozen compact cells, the solver's binding/qualification rules, and the admitted static SimBench topology and node limits. No solver or physical replay was run.
