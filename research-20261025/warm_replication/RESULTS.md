# Eight-group warm replanning replication — completed 25 October 2026

The fixed GNN and CatBoost policies **both failed the prospective practical
continuation rule**. The strong fixed-route charging control qualified in all
48 assignments, so the result is interpretable. Neither family earns expansion
under the frozen 1% of prior-electricity threshold. This is not a test proving
zero effect, equivalence, or the irrelevance of learning.

The source/protocol was frozen at `bc54492f` before attempt01. Managed owner
31384 closed exit0; frozen finalizer 88473 closed exit0 and ran once. The
subsequent once-only compact export passed. Exact rational outputs and unchanged
gates are in `summary.json` and `RESULTS_VIEW.json`; rounded display is in
`export-view-stdout.txt`. No cell was rerun or replaced.

## Complete denominators and physical endpoints

- 16/16 predetermined CoverCA1 prior acquisitions admitted.
- 384/384 assigned active decisions attempted and recorded, with operational
  cost defined for every assignment. These are eight base timetable groups,
  two nested sizes and three solver seeds, not 48 independent timetables.
- 382/384 method endpoints accepted; 371/384 strict method successes.
  Thirteen methods did not strictly succeed. Eleven still retained admitted
  intermediate plans; two used the common pre-existing valid fallback.
- No late outer endpoint, invalid admission, configuration failure, fatal stop,
  missing acquisition, undispatched assignment or unresolved child was reported.
- 48/48 direct Method0 fixed-route QP decisions had a timely NEW independently
  admitted physical candidate and native OPTIMAL/strict success. Raw solver
  objectives were not substituted for replay-valid bills.

The two fallback cells were GNN and GNN_day, both 50607/40/seed73. Their worker
return code was -6, with reaping recorded. Their inspected stderr logs are empty;
the cause is **unresolved**, not established as a model, solver, memory or data
failure. No automatic retry is allowed. Both paid failures remain in every
operational comparison. The other strict failures include later-round numerical
admission failures or exhaustion of the planner's search deadline after a valid
intermediate result; operational availability does not convert them to method
success. See the independent failure review for identities.

## Learned-policy contrasts

Each entry below is the mean across all 48 assigned pairs of
`100 * (control cost - learned cost) / prior late electricity cost E0`.
These are percentages of **common prior electricity E0**, not percentages of
the control's total bill or energy use. Positive values favor the learned arm.

| Control | GNN | CatBoost |
|---|---:|---:|
| CoverCA1 | 0.0386688% | 0.1997028% |
| CA1 | 0.2464893% | 0.4075233% |
| Deterministic random | 0.1706251% | 0.3316591% |
| Full movement model, conditional fixed fleet | 3.4760564% | 3.6370904% |
| Strong fixed-route QP on prior topology | 8.7352508% | 8.8962848% |
| Unchanged prior | 23.4267235% | 23.5877575% |

Both families had positive complete group medians against CoverCA1 in 7/8
groups and against QP in 8/8. They cleared the group-count condition but missed
the **mean >1%E0** condition against CoverCA1. Both comparisons were required.
CatBoost was prospectively secondary; its larger mean is not permission to
promote it or select a family after seeing these results. GNN versus CatBoost
has positive group medians in 5/8 but a negative full mean: group summaries and
paid failure tails must both be retained.

The initial four-group GNN contrast against Cover was 1.2318882%E0. Its separate
gate remains true in that development cohort; the new eight-group mean is
0.0386688%E0 and its gate remains false. Do not pool these cohorts to rescue a
threshold or describe the earlier point estimate as robustly replicated.

All policy comparisons include fresh loading/features/scoring, construction,
search, completion, replay and publication within the same 60-second outer
clock, with native cutoff52. This supports comparison of complete warm policies,
not a pure score-quality ablation or cold-start speedup. The specialized QP
uses a different appropriate backend from the tangent-based route methods.

## Price conditioning

GNN versus the same frozen model scored using day rather than target late
prices had mean gain 0.1206672%E0 and a median that rounds to zero across 48
operational pairs (the exact rational median is positive, below the declared
near-zero tolerance).
At the declared 1e-6 normalized near-zero tolerance: 23 GNN wins, 15 GNN_day
wins, 10 near-zero. Complete group medians were strictly positive in five groups,
but one was within that near-zero tolerance: the corresponding descriptive
group tally is four GNN wins, two GNN_day wins, two near-zero.

Pool records were available for 47/48 pairs, all changed and with rank-fill
room. The missing pair is the shared 50607/40/seed73 crash. This establishes
exposure to a ranking-pool intervention in the observed 47, not benefit in every
pair. The compact exporter does not provide numeric overlap averages. No
available-only replacement or new promotion rule is introduced.

This is weak, heterogeneous **fixed-model inference-conditioning evidence**.
Both optimizers still see late prices, and there is no comparably trained
tariff-blind model. It does not identify the information value learned from
tariffs, sensitivity to curvature b, or causality. The current models receive a
but not b. Input permutation or more model families would not supply the missing
identification.

## What survives and what is conceded

Replanning can improve substantially on a known prior, and the retained-fallback
policy delivered valid operational endpoints in every assigned cell. Strong
conventional restricted pools capture most of the observed learned improvement
over the unchanged plan. Learning's incremental practical advantage is small in
this new cohort. Generic learned pruning, recovery and convex-hull pricing are
prior art; these results do not establish a novel algorithm or an FT50-ready
contribution.

All cases remain synthetic development. TRAIN admission established declared
base-ID nonoverlap only, not global variant-alias closure or transfer to a new
population. Fleet is fixed to a feasible fleet-count prior, not a proven
day-economic optimum. Power scales180/270kW with size. Fleet cost is constant
within each comparison; route energy can change. No unrestricted optimum,
original-problem certificate, significance or price-learning claim follows.
The objective is integrated system cost `c+a'L+.5L'BL`, not atomic uniform-price
payment `c+a'L+L'BL`.

## Next scientific decision

Stop expanding the current policy, quotas, runtime or model families. Before
more fitting or a larger replication, inspect a narrowly whitelisted TRAIN-only
metadata/label-readiness package: which tariffs occur for the same physical
timetable, how price-derived features enter, what objective and incumbent policy
generated labels, whether labels actually vary with tariff, and whether group
aliases close across variants. Start with metadata; row/label access requires
its own explicit file allowlist and prospective measured command. Never open
the sealed banks.

If there is no defensible conditional supervision signal, concede that the
current training setup cannot substantiate price-responsive prediction. Any
new price-paired label design must have a scientific rationale and fixed
teacher/pool policy before dispatch, rather than search for a favorable tariff
contrast. If readiness passes, design a matched aware/blind experiment with
equal inner selection, trained assets frozen before independent evaluation,
competent classical controls and a declared useful-effect threshold. No new
fit, solver experiment or readiness command is authorized by this report alone.
