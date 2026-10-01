# Fixed TRAIN physical-proposal comparison v7

Array728823 retains usable physical results and an explicit incomplete hull-control scope. All48 saved-model scoring children passed; independent replay below reproduces143 saved plan bills exactly. No estimator inference, fitting, optimization, new solve or retry is performed by the replay script.

The frozen16 TRAIN timetables10064–10079 use seed17 outer-fold saved models, INNER-only family/graph promotion, and the `day` market. The primary proposals are repaired-only; source policy is the predeclared minimum of all direct and independently replayed recharged source plans, with every attempted source stage charged.

## Stage failures and scope

Both hull controls failed on all16groups (32typed TypeErrors): `nh.Budget` accepts `pool_tolerance`, while v7 passed `pool_tol`. They failed before hull optimization; no cold/retained hull bound or mixture result exists. Wrapper/Slurm0 is not full scientific success. Timetable10069 also hit the5-second HiGHS cover cap without an integral incumbent for family, graph and cost-only; tabular yielded a replayed fleet. These failures, dependent skips and spent time remain in the ledger.

All32 source recharges and16 cold physical incumbents independently replay. Raw argmax topology is invalid in46/48 diagnostics; only tabular and family on10074 reach replay, independently of the primary repaired arms.

## Paired physical bills

Bill deltas are proposal minus matched source policy: negative is cheaper. Values below round to three decimals; exact rational bills/deltas, fleets, topologies, hashes and all failures are retained in the machine ledger. A dash is a failed cover, not a high-cost surrogate.

| TRAIN group | Source policy bill | Δtabular | Δfamily | Δgraph | Δcost-only | Cold bill |
|---|---:|---:|---:|---:|---:|---:|
| 10064 | 664.867 | -0.117 | -0.117 | +15.159 | +71.760 | 659.127 |
| 10065 | 487.498 | +8.773 | +8.773 | +8.773 | +12.416 | 479.992 |
| 10066 | 719.263 | -0.754 | +1.455 | +7.770 | +13.993 | 713.004 |
| 10067 | 437.085 | 0.000 | 0.000 | 0.000 | +4.032 | 430.039 |
| 10068 | 579.835 | +0.070 | +0.070 | 0.000 | +13.078 | 572.871 |
| 10069 | 773.492 | +113.915 | — | — | — | 768.129 |
| 10070 | 599.482 | 0.000 | 0.000 | 0.000 | +14.261 | 564.079 |
| 10071 | 525.880 | -0.042 | -0.042 | -0.042 | +46.441 | 506.402 |
| 10072 | 540.755 | +3.876 | +3.876 | +2.471 | +8.867 | 531.570 |
| 10073 | 462.486 | +1.712 | +1.712 | 0.000 | +19.669 | 450.016 |
| 10074 | 499.348 | 0.000 | 0.000 | 0.000 | 0.000 | 495.570 |
| 10075 | 586.170 | -6.812 | -6.860 | +9.465 | +13.091 | 573.059 |
| 10076 | 632.096 | -1.139 | -1.139 | +12.447 | +38.618 | 622.821 |
| 10077 | 566.365 | +1.054 | +1.054 | +12.369 | +5.194 | 566.382 |
| 10078 | 580.162 | +0.583 | +13.005 | +0.583 | +24.086 | 579.600 |
| 10079 | 486.914 | 0.000 | +20.691 | 0.000 | +38.742 | 486.921 |
| Primary arm | Replayed / intended | Lower / exact tie / higher than source | Lower / within0.01 / higher (post-hoc) | Mean Δbill, available pairs | Mean Δbill, common15 | Novel topologies |
|---|---:|---:|---:|---:|---:|---:|
| tabular_v3 | 16/16 | 6/3/7 | 5/4/7 | +7.570 | +0.480 | 13 |
| families_v5 | 15/16 | 5/2/8 | 4/3/8 | +2.832 | +2.832 | 13 |
| graph_v6 | 15/16 | 3/3/9 | 1/6/8 | +4.600 | +4.600 | 11 |
| cost_only | 15/16 | 0/1/14 | 0/1/14 | +21.617 | +21.617 | 14 |


For reader interpretation only, the extra count column applies a transparently post-hoc absolute tolerance0.01cost units: differences within±0.01 are descriptive ties. This changes neither exact bills/signs nor the predeclared exact source policy or any model promotion; it is not an inferential threshold. Exact nonzero deltas displayed as0.000 are: all learned arms on10067,−2.896330089343893e-14; graph on10068,+2.994042873709717e-14; graph on10073,−5.909557616919132e-14. All other0.000 entries are exact ties. These floating-scale differences are also below the existing native objective tolerance1e-6 and do not evidence cheaper routes. Tabular/family/graph have5/4/1 cheaper groups beyond0.01, respectively.

Neither model promotion nor a combined best learned arm is inferred from these outcomes. The small TRAIN pilot can identify individual replayed cheaper proposals, but it does not establish a general held-out route benefit. The observed cold physical bills use a different multi-round curved planning budget; they are bounded incumbents, not certified physical optima or a matched-speedup comparison.

## Time and limitations

All attempted stage wall time is1392.314s, including62.358s spent in failed children. Supervisor totals1401.129s; wrapper totals1464s. Prior source acquisition totals779.447s and remains a separate sunk charge. Slurm allocated1484CPU-seconds (0.412CPUh), peak batch RSS232996KiB, observed concurrency3; requested ceiling was8CPUh. No stage time is discarded because it failed.

Disjoint per-arm work totals retain failed/capped stages and shared scoring costs in the ledger; source policy also retains all source admission/recharge/replay work. The ledger verifies complete stage hash chains, runtime pins, movement/market identities, outer-only partitions and recorded INNER choices. It verifies finite saved logits and completed scoring receipts; it does not rerun saved-model numerical prediction. All physical plans are replayed with the deterministic native replay/pricing-start APIs and exact curved cost recomputation. Source retrieval is within each timetable's admitted two-source bank. No DEV/TEST, training, optimality, matched speedup or outer-based promotion claim is made.
