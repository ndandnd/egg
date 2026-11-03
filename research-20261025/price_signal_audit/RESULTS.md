# Fixed-plan price-signal diagnostic — completed 25 October 2026

342 admitted plans / 20 development timetables. Original exact objective and historical input hashes all matched. No new routes, charging schedules, model fits, inference or physical replay were run.

Primary bank: minimum observed fleet count within each timetable, pooling all six methods and three seeds. It is a hindsight catalog; these are not deployable-selector or full-problem optima.

| Target | Groups with a materially better target plan / 20 | Median cost reduction from changing the original-day selection | Maximum reduction |
|---|---:|---:|---:|
| day | 0 | 0.0000% | 0.0000% |
| flat | 12 | 0.1531% | 2.3534% |
| late | 13 | 0.7165% | 4.2338% |
| shift+6 | 13 | 0.4894% | 3.8735% |
| shift-6 | 11 | 0.3114% | 2.4568% |

Material means more than 1e-6 cost units. All tariffs have the same mean linear coefficient and unchanged curvature. A reduction is relative to the original-day winner evaluated at the target tariff. Fixed stored charging limits the available alternatives; a small effect cannot rule out better unobserved charging or routes.

| Objective change, same minimum observed fleet | Positive system-cost loss / 20 | Median loss in cost units | Maximum loss |
|---|---:|---:|---:|
| System-cost optimum to marginal-payment optimum, day | 8 | 0.000000 | 6.077384 |
| System-cost optimum to marginal-payment optimum, late | 3 | 0.000000 | 7.914771 |

System cost is c+aL+bL²/2; all-units marginal-price payment is c+aL+bL². This comparison selects from the same stored bank. It does not solve a strategic fleet model or equilibrium.

| Paired equal-fleet comparison, 40 trips | Groups | Paired cells | Median group objective improvement | Positive / negative / zero group signs |
|---|---:|---:|---:|---|
| Graph vs nonlearned, day | 10 | 30 | 0.4702% | 9 / 1 / 0 |
| Graph vs nonlearned, flat | 10 | 30 | -0.4255% | 2 / 8 / 0 |
| Graph vs nonlearned, late | 10 | 30 | -0.5322% | 4 / 6 / 0 |
| Graph vs nonlearned, shift+6 | 10 | 30 | -0.5548% | 2 / 8 / 0 |
| Graph vs nonlearned, shift-6 | 10 | 30 | -0.7311% | 0 / 10 / 0 |
| Graph vs catboost_v5, day | 10 | 30 | -0.0021% | 1 / 8 / 1 |
| Graph vs catboost_v5, flat | 10 | 30 | -0.0038% | 0 / 9 / 1 |
| Graph vs catboost_v5, late | 10 | 30 | -0.0211% | 2 / 7 / 1 |
| Graph vs catboost_v5, shift+6 | 10 | 30 | -0.0111% | 2 / 7 / 1 |
| Graph vs catboost_v5, shift-6 | 10 | 30 | -0.0018% | 1 / 8 / 1 |

Positive means lower integrated system cost for graph. Signs here are exact signs, including numerically tiny differences; they are not tests of significance. Equal-fleet eligibility is conditional on the old endpoints, not a prospective fixed-fleet intervention. At 80 trips the important graph/classical comparisons mostly have unequal fleets, so this analysis cannot remove that confounding.

Exact cost differences split into fleet cost, common-mean-price energy quantity, tariff timing exposure and curvature; all additive identities passed. Results preserve every original unavailable endpoint and seed/group denominator.

Interpretation: a tariff-dependent bank winner establishes an available alternative, not that the learned scorer recognizes it. The next mechanism test must change the model price inputs and reoptimize charging/routes under the declared objective. Neither this audit nor its stability radii certify the original unrestricted EVSP.

Same-fleet bank sizes: {'min': 1, 'median': 10.0, 'max': 15}. Full exact quantities, source hashes and original admitted loads are in results.json.
