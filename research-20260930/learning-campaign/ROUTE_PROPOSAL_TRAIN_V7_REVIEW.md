# Fixed TRAIN physical-proposal v7 review

**Verdict: no material issue found in the final summary or ledger.** The tables are now contiguous Markdown tables. I checked the added post-hoc ±0.01 cost-unit descriptive tie column against the exact rational paired deltas in the replay ledger; its counts match, while the separately reported exact-sign counts remain unchanged:

| Arm | Exact lower / tie / higher | Post-hoc lower / within ±0.01 / higher |
|---|---:|---:|
| tabular_v3 | 6 / 3 / 7 | 5 / 4 / 7 |
| families_v5 | 5 / 2 / 8 | 4 / 3 / 8 |
| graph_v6 | 3 / 3 / 9 | 1 / 6 / 8 |
| cost_only | 0 / 1 / 14 | 0 / 1 / 14 |

The replay code adds the tolerance only to reporting summaries; exact paired signs, source-policy selection, and model promotion remain separate. The report also calls out the floating-scale nonzero deltas that display as `0.000`, and does not treat them as evidence of savings.

The compact report and ledger agree on 16 groups, 48 successful saved-model scoring stages, 143 exact physical-plan bill replays, 35 failed and 98 skipped stages, and the incomplete hull scope. All 32 hull-control children failed before optimization on the `pool_tol` keyword mismatch; group 10069 lacks family, graph, and cost-only cover after the 5-second no-incumbent timeout. The three learned-arm mean bill deltas on the common 15 groups are positive (+0.480, +2.832, +4.600); no general route-benefit claim is supported. Failed-stage time remains included, and source-acquisition time is separated as sunk cost.

This was a bounded review of the released replay script, report, and ledger; I did not rerun physical-plan replay, score models, train, solve, or read raw traces. Root's independent saved-plan replay was still running at review time.
