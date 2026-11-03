# Conventional recovery continuation

Minimal conventional recovery study; broader candidate-rich, stabilized and random controls absent. Not the full NEXT_EXPERIMENT gate, a novelty claim, V2G result or nonlinear result.

All 40 planned states are retained, including unattempted and missing outcomes. Strict methods and operational fallback coverage remain separate.

| Group | Phase | Strict / 2 | Operational / 2 | Native optimal / 2 | Qualified banks / 2 |
|---|---|---:|---:|---:|---:|
| 62001 | F | 2 | 2 | 2 | 2 |
| 62001 | N | 1 | 2 | 1 | 2 |
| 62001 | D | 1 | 2 | 1 | 2 |
| 62001 | UN | 2 | 2 | 2 | 0 |
| 62001 | UD | 2 | 2 | 2 | 0 |
| 62002 | F | 2 | 2 | 2 | 2 |
| 62002 | N | 1 | 2 | 1 | 2 |
| 62002 | D | 1 | 2 | 1 | 2 |
| 62002 | UN | 2 | 2 | 2 | 0 |
| 62002 | UD | 2 | 2 | 2 | 0 |
| 62003 | F | 2 | 2 | 2 | 2 |
| 62003 | N | 1 | 2 | 1 | 2 |
| 62003 | D | 1 | 2 | 1 | 2 |
| 62003 | UN | 2 | 2 | 2 | 0 |
| 62003 | UD | 2 | 2 | 2 | 0 |
| 62004 | F | 2 | 2 | 2 | 2 |
| 62004 | N | 1 | 2 | 1 | 2 |
| 62004 | D | 1 | 2 | 1 | 2 |
| 62004 | UN | 2 | 2 | 2 | 0 |
| 62004 | UD | 2 | 2 | 2 | 0 |

| Comparison | Strict pairs / 8 | Full eight mean | Operational full eight mean |
|---|---:|---:|---:|
| UN_vs_F | 8 | 31/13776 | 31/13776 |
| UN_vs_F, group 62001 12/24 mean | — | 1/328 | 1/328 |
| UN_vs_F, group 62002 12/24 mean | — | 0 | 0 |
| UN_vs_F, group 62003 12/24 mean | — | 1/168 | 1/168 |
| UN_vs_F, group 62004 12/24 mean | — | 0 | 0 |
| UD_vs_F | 8 | 31/13776 | 31/13776 |
| UD_vs_F, group 62001 12/24 mean | — | 1/328 | 1/328 |
| UD_vs_F, group 62002 12/24 mean | — | 0 | 0 |
| UD_vs_F, group 62003 12/24 mean | — | 1/168 | 1/168 |
| UD_vs_F, group 62004 12/24 mean | — | 0 | 0 |
| UD_vs_UN | 8 | 0 | 0 |
| UD_vs_UN, group 62001 12/24 mean | — | 0 | 0 |
| UD_vs_UN, group 62002 12/24 mean | — | 0 | 0 |
| UD_vs_UN, group 62003 12/24 mean | — | 0 | 0 |
| UD_vs_UN, group 62004 12/24 mean | — | 0 | 0 |

Ratios use each cell’s own positive finite F grid electricity. A full-eight mean is null if any planned pair is missing.

| Task | Attempted this run | Reused prior | Strict | Operational source | Finite-bank optimum reached | Status / failures / missing reason |
|---|---|---|---|---|---|---|
| B62001-N12-F | False | True | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N12-N | False | True | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N12-D | False | True | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N12-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N12-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N24-F | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N24-N | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62001-N24-D | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62001-N24-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62001-N24-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N24-F | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N24-N | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62002-N24-D | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62002-N24-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N24-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N12-F | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N12-N | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N12-D | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N12-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62002-N12-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N12-F | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N12-N | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N12-D | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N12-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N12-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N24-F | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N24-N | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62003-N24-D | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62003-N24-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62003-N24-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N24-F | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N24-N | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62004-N24-D | True | False | False | worker_retained | None | {"status": null, "failures": [{"stage": "selection", "type": "NoSelection", "message": "No supported native selected fleet; common fallback is operational only"}], "unattempted_reason": null} |
| B62004-N24-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N24-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N12-F | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N12-N | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N12-D | True | False | True | worker_retained | None | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N12-UN | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |
| B62004-N12-UD | True | False | True | worker_retained | True | {"status": null, "failures": [], "unattempted_reason": null} |

| Pipeline | Complete | CPU seconds | Elapsed stage sum seconds |
|---|---|---:|---:|
| F+N+UN | True | 490.99192999999997 | 521.9916052090005 |
| F+D+UD | True | 596.231253 | 628.369820250012 |

Each pipeline pays F and its acquisition once; common preparation/preflight is added once. Physical campaign totals charge all executed work once.

Physical campaign resources: {"self_cpu_s": 0.665389, "waited_children_cpu_s": 985.724806, "preparation_charge_s": 0.35, "reuse_binding_charge_s": 0.05, "reused_stages_new_physical_charge_s": 0, "package_cpu_prepublication_s": 986.7901949999999, "package_elapsed_sum_prepublication_s": 1040.7502097079903, "conservative_cpu_with_unresolved_reserve_s": 986.7901949999999, "prior_closed_retained_study_cpu_s": 17.34, "prior_closed_study_elapsed_s": 19.17, "new_current_provisional_study_cpu_s": 986.7901949999999, "new_current_provisional_study_elapsed_s": 1040.7502097079903, "combined_actual_study_cpu_prepublication_s": 1004.130195, "combined_actual_study_elapsed_sum_prepublication_s": 1059.9202097079904, "combined_study_scope": "Prior closed retained package plus new provisional self/waited/preparation/binding; reused rows add no physical charge; final external parent receipt authoritative", "cumulative_retained_research_cpu_prepublication_s": 21272.530195000003, "cumulative_research_wall_elapsed_sum_prepublication_s": 21949.16020970799, "legacy_excluded_cpu_s": 2546.091499549272, "source_review_cpu_s": "UNKNOWN", "observed_self_peak_rss_bytes": 27541504, "python_threads": 1, "task_deltas_not_added_twice": true, "external_total_acceptance_pending": true}

Historical ledger (already paid in global prefix): {"source_revision": "234668a879f31c3a49254adf6e313f8fbdfaa1a6", "control_revision": "c7c69a75", "compact_master_sha256": "ce088ca15a50e31d3d32874ba035c12abea5a3d108fb6417852de9f5cf5a010e", "original_common_preflight": {"cpu_s": 0.438588, "elapsed_s": 0.4977212916687131}, "reused_task_ids": ["B62001-N12-F", "B62001-N12-N", "B62001-N12-D"], "reused_stage_costs_already_in_global_prefix": true, "failed_UN": {"task_id": "B62001-N12-UN", "cpu_s": 3.452561000000001, "stage_elapsed_s": 3.54326624982059, "method_success": false, "failures": [], "worker_failures": [{"stage": "union_native", "type": "KeyError", "message": "'gurobipy'"}], "fatal_contract": true, "config_failure": true}, "old_closeout_overhead": {"cpu_s": 0.0003379999999992833, "elapsed_s": 0.0003242483362555504, "scope": "Prior prepublication package minus common preflight and four stage costs; external closeout reconciliation remains separate"}, "prior_package_resources": {"self_cpu_s": 0.07855999999999999, "waited_children_cpu_s": 16.853438, "preparation_charge_s": 0.38, "package_cpu_prepublication_s": 17.312, "conservative_cpu_with_unresolved_reserve_s": 17.312001, "package_elapsed_sum_prepublication_s": 19.13929620716721, "cumulative_retained_research_cpu_prepublication_s": 20285.712002, "cumulative_research_wall_elapsed_sum_prepublication_s": 20908.37929716643, "legacy_excluded_cpu_s": 2546.091499549272, "source_review_cpu_s": "UNKNOWN", "observed_self_peak_rss_bytes": 24576000, "python_threads": 1, "task_deltas_not_added_twice": true, "external_total_acceptance_pending": true}}

Owner failures: []
