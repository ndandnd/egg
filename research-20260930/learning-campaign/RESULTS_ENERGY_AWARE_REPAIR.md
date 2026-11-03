# Energy-aware route repair: stage results

Job 688750 completed successfully in 35 seconds (exit 0; one allocated CPU;
maximum RSS 116,972 KiB). All four child cells returned before their hard
limits. Each energy-relaxed cover was reported native optimal for the declared cover model:
three buses for the 20-service case and four for the 28-service case. These
are minima only for the declared relaxation with optimistic depot resets;
they do not certify physical fleet minima.

| Case | Cover policy | Cover buses / pullouts | Cover status / gap | Fixed-route charging | Repair time (s) | Child time (s) |
|---|---|---:|---|---|---:|---:|
| 2016, 20 services | cost-only | 3 / 3 | optimal / 0 | infeasible | 0.82 | 4.04 |
| 2016, 20 services | cost-learned | 3 / 3 | optimal / 0 | infeasible | 0.60 | 3.83 |
| 2017, 28 services | cost-learned | 4 / 4 | optimal / 0 | infeasible | 3.34 | 6.75 |
| 2017, 28 services | cost-only | 4 / 4 | optimal / 0 | infeasible | 1.24 | 4.80 |

All four fixed-route charging LPs returned `INFEASIBLE` with no incumbent, so
none produced a new repaired fleet or a direct repaired cost. The learned
policy selected different cover routes and ran inference (0.037 seconds in
2016; 0.076 seconds in 2017), but it did not change relaxed bus counts,
charging feasibility, or the replayed physical outcome relative to cost-only.
Cover time was 0.58/0.32 seconds for cost-only/learned in 2016 and
0.66/2.68 seconds in 2017; fixed-route charging took about 0.24 seconds in
2016 and 0.58 seconds in 2017 before infeasibility was returned.

Each failure then selected and replayed the same archived stage-2 source
candidate for its case. The saved replay flags are true: the 2016 fallback is
the four-bus source fleet at target cost 553.47 cost units (rounded); the 2017
fallback is the five-bus source fleet at 724.66 cost units. Root independently
replayed all four source fallbacks and confirmed plan hashes and exact
objectives against [INDEPENDENT_REPLAY_ENERGY_AWARE.json](INDEPENDENT_REPLAY_ENERGY_AWARE.json).
These are source-fallback costs, not outcomes from the proposed three- or
four-bus repairs. The result CSV keeps
the direct repaired cost empty and records the fallback cost separately.

Because each fallback is the already-verified archived candidate, all four
cells correctly skipped a redundant fresh hull check: assessment is empty
and hull time is zero. The historical stage-2 bounds are references only;
this pilot produced no fresh lower bound, mixture upper bound, or physical
optimality claim. The result is that the energy filter admits covers that
still fail the fixed-route charging model on both development cases. Four
unreplicated cells provide no evidence of a learning advantage.

Machine-readable per-cell timings, statuses, replay flags, fallback costs,
and hull fields are in [ENERGY_AWARE_REPAIR_CELLS.csv](ENERGY_AWARE_REPAIR_CELLS.csv).

An independent [charging-window diagnosis](CHARGING_WINDOW_DIAGNOSIS.md) rejects all four selected fleets even if each bus has exclusive charger access: 12 of 14 routes cannot maintain reserve with the energy their depot stops can deliver. Representative failing routes reach at most 5.29–18.25 kWh after a service, below the 20 kWh reserve. This identifies insufficient charging opportunities within the chosen routes; shared congestion is not needed to explain these failures. The next controlled change is a cumulative per-visit charging-energy cap in route selection, with the same frozen model, cases and physical verification.
