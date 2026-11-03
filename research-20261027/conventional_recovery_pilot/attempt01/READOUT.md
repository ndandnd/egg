# Conventional recovery pilot

Minimal conventional recovery study; broader candidate-rich, stabilized and random controls absent. Not the full NEXT_EXPERIMENT gate, a novelty claim, V2G result or nonlinear result.

All 40 planned states are retained, including unattempted and missing outcomes. Strict methods and operational fallback coverage remain separate.

| Group | Phase | Strict / 2 | Operational / 2 | Native optimal / 2 | Qualified banks / 2 |
|---|---|---:|---:|---:|---:|
| 62001 | F | 1 | 1 | 1 | 1 |
| 62001 | N | 1 | 1 | 1 | 1 |
| 62001 | D | 1 | 1 | 1 | 1 |
| 62001 | UN | 0 | 1 | 0 | 0 |
| 62001 | UD | 0 | 1 | 0 | 0 |
| 62002 | F | 0 | 0 | 0 | 0 |
| 62002 | N | 0 | 0 | 0 | 0 |
| 62002 | D | 0 | 0 | 0 | 0 |
| 62002 | UN | 0 | 0 | 0 | 0 |
| 62002 | UD | 0 | 0 | 0 | 0 |
| 62003 | F | 0 | 0 | 0 | 0 |
| 62003 | N | 0 | 0 | 0 | 0 |
| 62003 | D | 0 | 0 | 0 | 0 |
| 62003 | UN | 0 | 0 | 0 | 0 |
| 62003 | UD | 0 | 0 | 0 | 0 |
| 62004 | F | 0 | 0 | 0 | 0 |
| 62004 | N | 0 | 0 | 0 | 0 |
| 62004 | D | 0 | 0 | 0 | 0 |
| 62004 | UN | 0 | 0 | 0 | 0 |
| 62004 | UD | 0 | 0 | 0 | 0 |

| Comparison | Strict pairs / 8 | Full eight mean | Operational full eight mean |
|---|---:|---:|---:|
| UN_vs_F | 0 | None | None |
| UN_vs_F, group 62001 12/24 mean | — | None | None |
| UN_vs_F, group 62002 12/24 mean | — | None | None |
| UN_vs_F, group 62003 12/24 mean | — | None | None |
| UN_vs_F, group 62004 12/24 mean | — | None | None |
| UD_vs_F | 0 | None | None |
| UD_vs_F, group 62001 12/24 mean | — | None | None |
| UD_vs_F, group 62002 12/24 mean | — | None | None |
| UD_vs_F, group 62003 12/24 mean | — | None | None |
| UD_vs_F, group 62004 12/24 mean | — | None | None |
| UD_vs_UN | 0 | None | None |
| UD_vs_UN, group 62001 12/24 mean | — | None | None |
| UD_vs_UN, group 62002 12/24 mean | — | None | None |
| UD_vs_UN, group 62003 12/24 mean | — | None | None |
| UD_vs_UN, group 62004 12/24 mean | — | None | None |

Ratios use each cell’s own positive finite F grid electricity. A full-eight mean is null if any planned pair is missing.

| Task | Attempted | Strict | Operational source | Finite-bank optimum reached | Status / failures / missing reason |
|---|---|---|---|---|---|
| B62001-N12-F | True | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N12-N | True | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N12-D | True | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N12-UN | True | False | own_F_fallback | False | {"status": null, "failures": [{"stage": "union_native", "type": "KeyError", "message": "'gurobipy'"}], "unattempted_reason": null} |
| B62001-N12-UD | False | False | own_F_fallback | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62001-N24-F | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62001-N24-N | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62001-N24-D | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62001-N24-UN | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62001-N24-UD | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N24-F | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N24-N | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N24-D | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N24-UN | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N24-UD | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N12-F | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N12-N | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N12-D | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N12-UN | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62002-N12-UD | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N12-F | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N12-N | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N12-D | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N12-UN | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N12-UD | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N24-F | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N24-N | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N24-D | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N24-UN | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62003-N24-UD | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N24-F | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N24-N | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N24-D | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N24-UN | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N24-UD | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N12-F | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N12-N | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N12-D | False | False | missing | None | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N12-UN | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |
| B62004-N12-UD | False | False | missing | False | {"status": null, "failures": [], "unattempted_reason": "Fatal stage or unresolved owned child"} |

| Pipeline | Complete | CPU seconds | Elapsed stage sum seconds |
|---|---|---:|---:|
| F+N+UN | False | None | None |
| F+D+UD | False | None | None |

Each pipeline pays F and its acquisition once; common preparation/preflight is added once. Physical campaign totals charge all executed work once.

Physical campaign resources: {"self_cpu_s": 0.07855999999999999, "waited_children_cpu_s": 16.853438, "preparation_charge_s": 0.38, "package_cpu_prepublication_s": 17.312, "conservative_cpu_with_unresolved_reserve_s": 17.312001, "package_elapsed_sum_prepublication_s": 19.13929620716721, "cumulative_retained_research_cpu_prepublication_s": 20285.712002, "cumulative_research_wall_elapsed_sum_prepublication_s": 20908.37929716643, "legacy_excluded_cpu_s": 2546.091499549272, "source_review_cpu_s": "UNKNOWN", "observed_self_peak_rss_bytes": 24576000, "python_threads": 1, "task_deltas_not_added_twice": true, "external_total_acceptance_pending": true}

Owner failures: []
