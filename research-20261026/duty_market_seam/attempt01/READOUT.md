# Duty/market seam — compact operational readout

One literal synthetic base, four economic contexts. Display decimals only; READOUT.json retains exact represented costs and components. No cross-institution pooled mean, physical-optimum or ML claim.

| Context | Institution | Unchanged | QP U | Fixed duty | Full | QP−duty | QP−full | Duty−full |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| b0_all | all_three_coincide | 241.6666667 | 233.0555556 | 227.5 | 227.5 | 5.555555556 | 5.555555556 | 0 |
| posted | exogenous_posted_payment | 252.0833333 | 243.75 | 237.5 | 237.5 | 6.25 | 6.25 | 0 |
| system | incremental_integrated_system_cost | 258.1114969 | 249.3135931 | 242.96875 | 242.96875 | 6.344843107 | 6.344843107 | 0 |
| strategic | atomic_uniform_price_payment | 264.1396605 | 254.8771862 | 248.0413291 | 248.0413291 | 6.835857124 | 6.835857124 | 0 |

The b0 context has three equivalent economic aliases from one set of solves. QP qualification and strict MIQP delivery are different flags; native status is separate. Failure counts are retained records, not deduplicated incidents.

| Context | Phase | Attempted | QP qualified | Strict MIQP | Native status | Duties changed | Used fallback | Failure records | Parent seconds |
|---|---|---|---|---|---|---|---|---:|---:|
| b0_all | target_qp | True | True | — | 2 | False | False | 0 | 0.8141904585 |
| b0_all | fixed_duty | True | — | True | 2 | False | False | 0 | 0.2580529163 |
| b0_all | full | True | — | True | 2 | False | False | 0 | 0.2029788336 |
| posted | target_qp | True | True | — | 2 | False | False | 0 | 0.2018591678 |
| posted | fixed_duty | True | — | True | 2 | False | False | 0 | 0.2128754584 |
| posted | full | True | — | True | 2 | False | False | 0 | 0.2060002498 |
| system | target_qp | True | True | — | 2 | False | False | 0 | 0.208777166 |
| system | fixed_duty | True | — | True | 2 | False | False | 0 | 0.2108990839 |
| system | full | True | — | True | 2 | True | False | 0 | 0.2614020836 |
| strategic | target_qp | True | True | — | 2 | False | False | 0 | 0.2550367909 |
| strategic | fixed_duty | True | — | True | 2 | False | False | 0 | 0.2151307911 |
| strategic | full | True | — | True | 2 | False | False | 0 | 0.2736892914 |

## Closure and resource observations

Administrative passed: True. External publication/exit-tail acceptance remains pending.

```json
{
  "summary": {
    "planned_base_units": 1,
    "planned_contexts": 4,
    "planned_workers": 12,
    "recorded_contexts": 4,
    "attempted": 12,
    "qualified_common": 4,
    "strict_dependent_deliveries": 8,
    "operational_dependent_endpoints": 8,
    "max_observed_worker_rss_bytes": 57180160,
    "defined_contrasts": {
      "qp_to_fixed_duty": 4,
      "qp_to_full": 4,
      "fixed_duty_to_full": 4
    },
    "complete_four_context_report": true,
    "pooled_cross_institution_cost_or_gain_mean": null,
    "b0_aliases": "Posted/strategic/system are economic aliases atb0; onecontext/onesetofsolves",
    "available_only_mean": null,
    "scope": "Operational delivered endpoint contrasts across4economic contexts ofONEliteralbase, not independentcases",
    "promotion_rule": null,
    "statistical_claim": false,
    "certificate_claim": false
  },
  "resources": {
    "self_cpu_s": 0.133788,
    "waited_children_cpu_s": 2.203982,
    "combined_cpu_s": 2.3377719999999997,
    "preparation_charge_s": 0.06,
    "package_cpu_before_publication_s": 2.397772,
    "package_elapsed_sum_before_publication_s": 3.505143041871488,
    "observed_self_peak_rss_bytes": 26181632,
    "python_threads": 1,
    "prepublication_only": true,
    "external_total_acceptance_pending": true
  },
  "failures": []
}
```

Self plus waited-child CPU is one cumulative owner observation; task deltas are not another charge. Source preparation is adopted once for package caps. These prepublication measurements are not final external acceptance or containment.
