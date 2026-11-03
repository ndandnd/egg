# Fixed-route charging control: two-file static triage

**Recommendation: resolve the fixed-topology convex-charging control before launching the 384-decision replication.** A small direct convex-QP diagnostic on these same two fixed topologies is justified. Keep the completed study unchanged and label any strengthened control prospectively; do not silently reinterpret its frozen fixed_route arm as a converged charging optimum.

Read only the seed17 specification metadata and the compact `planner-result.json` files for base50600:

| Case / attempt folder | Last primary native lower bound | Best independently admitted true bill | Last primary native wall time |
| --- | ---: | ---: | ---: |
| 40 / `015-replanning-scale-50600-40-fixed_route` | 714.8454240912208 | 714.9894582963846 | 0.0358242495s |
| 80 / `033-replanning-scale-50600-80-fixed_route` | 1190.5773588570246 | 1193.3528986623726 | 0.2155456254s |

Both files report four rounds, 12 dispatched native calls, selected source round3, fixed topology, fleet4, and no failures. The last primary is marked OPTIMAL, with essentially matching native incumbent and native bound, **for that round's finite supporting-tangent model**. Its value remains below the best replay-evaluated quadratic bill. The primary solve itself is therefore not the visible bottleneck; finite-envelope convergence is unresolved.

Neither stopped near its native cutoff. The 40-case planner returned at6106485.166225416, against native deadline6106534.110390791 and final deadline6106542.110390791. The 80-case returned at6107100.436045875, against6107128.072146375 and6107136.072146375. The round/call policy ended while substantial clock remained. This is evidence that four rounds can leave charging underresolved even when all individual linearized solves report OPTIMAL.

**Inference and limits:** some apparent GNN advantage over fixed_route could reflect this charging approximation rather than route adaptation alone. These two records do not establish how much, do not explain away the cohort's 12.0116748%-of-E0 difference, and say nothing directly about GNN versus CoverCA1. Native bounds are raw conditional reports, not independently established certificates; their proximity to the replay bill must not be presented as a rigorous error bound or extrapolated to other groups. The files explicitly retain `global_lower_bound:null` and `certificate_claim:false`.

The narrow next check is an independently budgeted convex quadratic solve with **all original routing binaries fixed to the same common prior**, original physical constraints, and the original integrated quadratic objective. Confirm that the reduction preserves the charging physics; retain a replay-valid prior if solving fails. Record numerical primal/dual diagnostics and replay the returned plan independently. If this materially improves the fixed-route witness, freeze the stronger charging baseline for replication; if it does not, report that diagnostic with its numerical limits. No extra ranking/model training or timing framework is needed to answer this concern.

Static assessment only: two compact planner summaries, no raw captures, selection arrays, scripts, recomputation, imports, hashes, inference or native execution. No replication source was changed.
