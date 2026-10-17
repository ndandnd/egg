# Independent numerical check of screen v3

Receipt-only closeout review. Independently recomputed from immutable attempt, worker result, and supervisor receipts using exact Fraction bills; did not import the campaign analyzer. No solver, model, training, sealed-data, native-event-log or replay execution. The frozen protocol and locked manifest supply grouping and paired seeds.

## Coverage and endpoint handling

There are **360 distinct attempted cells**, matching 20 timetables × three paired seeds × six arms: ten distinct groups at each of 40 and 80 services. Every arm has 60 terminal receipts.

| Arm | Valid economic endpoints | Other terminal outcomes |
|---|---:|---|
| v8 | 60 | 0 |
| CatBoost (legacy ID catboost_v5) | 60 | 0 |
| Nonlearned | 60 | 0 |
| Random | 59 | 1 extraction_failed |
| full4 | 44 | 16 unresolved |
| Cold | 59 | 1 censored TimeoutError |

The cold cell scale:50903:80, seed 17 materialized at 61.486538916 s against a 60 s endpoint. It is excluded; supervisor cleanup duration is not added to its economic clock. All other endpoints are uncensored. No worker/receipt supervisor resource-stop reason was found. Validity here requires worker acceptance **and** supervisor endpoint acceptance, no censoring, zero worker return code and no supervisor failure/missing worker receipt. This is a check of recorded admission evidence, not a new physical-feasibility proof.

## Independently recomputed economic comparisons

Each gain is (control bill − v8 bill)/control bill. Reduce paired seeds to one median per timetable, then take equal-weight group medians inside each size and an equal-size/group weighted median overall. Here both sizes have ten observed group medians, so the overall statistic is the ordinary median of those 20 group medians. Fractions are preserved until display.

| Control | Both-valid seed pairs | Median gain, 40 services | Median gain, 80 services | Overall group median |
|---|---:|---:|---:|---:|
| Nonlearned | 60 | 0.4702003% | 68.3622196% | 33.0283617% |
| Random | 59 | 29.7558417% | 19.3736676% | 24.2770241% |
| CatBoost | 60 | -0.0020827% | 44.3742442% | 1.5775545% |

Against nonlearned, v8 and control each have 30/30 valid cells in both sizes; v8 has zero validity losses. All ten groups per size have all three valid pairs. Positive group medians occur in **9/10** groups at size 40 and **10/10** at size 80. The largest individual regression is **0.3155364%**: scale:50805:40, solver seed 41 (gain −0.003155363791537282), comfortably within the frozen 5% regression limit. The primary economic, validity and complete-pair gates therefore pass on these receipt aggregates.

Against random, v8 has 30/30 valid endpoints per size; random has 30/30 at size 40 and 29/30 at size 80. There are ten fully paired groups at size 40 and nine at size 80. The scale:50877:80 group has only two valid pairs: its conditional median is retained descriptively and it is not a fully paired positive group. V8 wins all 59 both-valid seed comparisons and the single one-valid comparison; no invented bill is assigned to random's missing endpoint.

Against CatBoost, v8 has 37 lower-bill, 21 higher-bill and 2 equal-bill paired cells out of 60. The worst v8 paired gain is -3.1933371%. This secondary comparison does not replace nonlearned as the frozen primary comparator.

## Material interpretation limits

The primary pooled **33.03%** is between two sharply different size regimes: **0.47%** at 40 services versus **68.36%** at 80. It is not the typical gain at either size and must always be shown with those size-specific figures. These are bounded-search, ranking-plus-pruning-policy endpoints; this check does not establish an unrestricted optimum, a pure ranking-only causal effect, or recovery-study performance. The 20 synthetic development timetables and paired seeds are not 60 independent physical systems. The 16 unresolved full4 cells must remain visible when discussing conditional costs.

## Final analyzer comparison

Compared against `screen-analysis-v3-final/summary.json` after its successful terminal completion. **No numerical disagreement found.** All six endpoint counts match. Nonlearned/random both-valid denominators, every group median and group paired denominator, both size medians, overall medians, and worst paired gains agree with the independent exact-Fraction recomputation within 1e-14 gain units. CatBoost size/overall medians also agree; tiny last-digit differences come from the analyzer's float arithmetic, not a gate reversal.

All 15 reported gates are true, including completeness, admission/resource integrity, positive-bill applicability, paired validity, eight fully paired groups per size, primary median thresholds, seven positive fully paired groups per size, worst regression, random comparison and accounting. The independently reconstructed economic/validity gate results agree. Receipt sums independently confirm 13,283.902094 charged worker CPU seconds and peak worker RSS 786,006,016 bytes (about 0.732 GiB); no receipt resource-stop failure or endpoint overrun beyond the allowed 2-second grace was found. The analyzer adds 125.067812 supervisor CPU seconds for 13,408.969906 total charged screen CPU seconds (3.724714 hours), below the 8-hour screen envelope. That supervisor ledger-derived component, completion-marker hashes, physical replay evidence and artifact hashes were not independently re-executed in this receipt-only check.

The analyzer's computed protocol decision is **“GO to separately frozen recovery study.”** This is eligibility under the completed development-screen gates, not approval to launch another study, an optimality certificate, or proof of generalization. No new work was launched by this review. The analyzer reports a primary stratified group-bootstrap 95% percentile interval of 32.5121%–34.1934% (10,000 finite draws); this check did not independently rerun bootstrap. The sharp size-regime limitation above remains material despite that narrow pooled interval.

Closed-cohort numerical review complete. Immutable analysis outputs and raw receipts were not edited.
