# Scoring-price mechanism: estimand and exposure contract

Prospective, nonnumerical design critique, 24 October 2026. This note interprets
`RECOVERY_LEARNED_VALUE_STUDY_ADDENDUM.md` with
`RECOVERY_CLASSICAL_BASELINE_SPEC.md` and the current `CONTINUATION.md`. It adds no
arm, case, repeat, budget, authorization or launch clearance. No assets, cases,
inference, tests, solver calls or cluster work were used. The narrow source read
was limited to the feature/scorer interface, online call path and common selector.

## What the 48 decisions compare

Preserve the six-arm, eight-base, three-seed day comparison: 144 decisions. The
mechanism subset remains four bases, two per size, selected by the frozen salted
identity rule before inference. Each base has graph-v8 and CatBoost, each with
fresh shifted-target and original-day scoring inputs, at each of three seeds:
4 × 2 × 2 × 3 = 48 decisions, or 24 within-learner pairs. There are 12 pairs per
learner, supported by four base groups, not 12 independent timetables. Total
planned count remains 192. The original-day scoring condition is a new timed
execution against the shifted target; a historical day execution cannot replace
it. No additional negative-control arm is proposed.

For base i, learner l and seed s, treatment z changes only the scorer's supplied
linear-price vector: z=1 supplies shifted `a`; z=0 supplies original-day `a`.
Both planners, charging completions, replay billing and final outcome evaluation
use the same shifted target `(a,b)`. Both conditions recompute features and scores
inside their own startup-inclusive 60-second clock. Physics, movements, frozen
model/preprocessing, backbone, K, tie rule, recovery policy, solver seed, endpoint
and evidence rules must otherwise match. The supplied scoring prices must not
leak into the target planner, bill calculator or recovery rules.

The identified intervention is therefore the finite-budget effect of changing
the supplied ranking-price inputs for this frozen learner and policy on these
selected development bases. It includes any consequent feature/scoring/selection
latency and the search time left after preprocessing. It is not a tariff effect:
the target tariff is held fixed within every pair. It is not the effect of
learning versus no learning, a topology-only effect, a restoration effect, or
tariff generalization to an external population.

## Outcome and execution-context qualification

Write a potential outcome as `Y(i,l,s,z; e)`, where e includes execution slot,
worker, concurrent workload, thermal state, native timing and other machine
conditions. Y includes the timely replay-valid deployed fallback or final plan,
its exact target bill, and the frozen endpoint/failure classification. The ideal
same-context contrast compares z=1 and z=0 at the same e; two sequential runs do
not observe both potential outcomes in that context.

A paired solver seed is a variance-control/blocking device. It does not force
the same native search trajectory after a different topology, start, remaining
time or model construction order. A wall-clock limit makes healthy machine
speed and thermal variation relevant to which candidate is available by the
deadline. Even with one thread per worker, two simultaneous workers may share
resources. Thus pairing alone does not eliminate execution-context confounding
or interference.

Freeze treatment-to-slot assignment and condition order before inference. The
rotation must explicitly cover fresh versus original-day conditions within each
learner, size and seed, with paired conditions close in the schedule. A salted
assignment can serve as a reproducible randomization only if its salt and rule
are fixed independently of outcomes and machine forecasts; a fixed hash order
is not by itself evidence of exchangeable contexts. Record realized slot,
worker, overlap and available resource/thermal context. Do not correct a slow
condition by giving it extra time or rerunning it. Do not add repeats to the
192-decision design.

Under an outcome-independent, balanced assignment and the declared interference
assumption, the comparison targets the scoring-input method effect averaged over
the study's execution-context distribution and frozen seeds. If assignment or
context balance is inadequate, report the observed paired contrast with this
limitation; it is not an exact same-context causal measurement. Context logs can
diagnose imbalance, not recover the unobserved counterfactual. Any adjustment or
sensitivity analysis must be specified before outcomes and cannot justify
discarding slow runs.

Apply the addendum's endpoint ordering to fresh versus original-day within each
learner. A timely replay-valid plan beats a genuine healthy algorithmic no-plan
or late result; two such algorithmic failures tie. With both valid, fresh wins
only if its lower target bill is outside the existing symmetric band
`0.005 * max(abs(B_fresh), abs(B_original), 1 currency unit)`; reverse for a loss.
Call this paired score W in {-1,0,1}. First average the three seed contributions
within a base, then equally weight bases within each size and the two sizes.
Infrastructure-unknown and undispatched contributions remain missing with the
existing [-1,1] bounds. Preserve all assignments and the incomplete suffix if
the budget stops the study. Use the existing separate multiplicity family for
the two learner mechanism contrasts; freeze any inferential rule before cases.

This practical net-win contrast is a method endpoint, not an average causal
currency saving. Both-valid bill differences and their decomposition are
secondary, with denominators visible. Selecting both-valid pairs or equal-vehicle
pairs conditions on post-intervention outcomes; those subsets are descriptive.
Four bases, including only two per size, sharply limit population inference.

## Required exposure chain

For each assigned pair, archive the following linked evidence, with original
movement IDs as the common alignment. Hashes establish exact identity; numerical
summaries explain differences and must not substitute for the underlying ledger.

| Link | Required evidence and interpretation |
| --- | --- |
| Supplied `a` to features | Original and shifted price identity/permutation, fixed target `(a,b)` identity, feature schema and preprocessing identity; per-row/per-feature exact finite-value changes and maximum absolute deltas. Distinguish changed window features from numerical changes to theoretically invariant summaries. |
| Features to scores | Aligned finite raw logits and hashes, changed-score counts and magnitudes. Input availability is not proof that the fitted scorer uses those inputs. |
| Scores to order | Exact deterministic order and ties by movement ID, both for flexible movements and the eligible set `F minus B`. Show rank displacement and the score gap at the fill cutoff. A score change can leave every relevant comparison unchanged. |
| Order to retained mask | Identical common price-blind backbone B; M, `abs(B)`, K, fill count `K-abs(B)`, exact retained IDs, mask hash and symmetric difference. Only cutoff crossings among eligible movements change the mask. Reordering mandatory backbone/boundary movements alone does not. |
| Mask to solver input/start | Actual restricted movement inventory/model ordering, preparation duration, native entry time and remaining allowance; acquisition/restoration times, candidate/fallback identities, replay admission, submitted full-model binary-start identity and native acceptance/processing receipts. A retained mask is not itself a validated full-model start. |
| Search/start to endpoint | Timely replay-valid deployed outcome, exact target bill and components, vehicle count, healthy failure/unknown classification, restoration/full-search usage and complete deadline/finalization receipts. Never substitute an unexecuted warm path or a restricted bound. |

The common backbone and exact K remove variation in retained edge count, not in
topology, search difficulty or preprocessing cost. The exposure question concerns
choices outside the backbone. Features and scores may change on mandatory
movements without changing that choice. Once restoration returns the full
feasible set, a prior restriction can still affect incumbents, starts and time
spent; a final full graph does not erase earlier exposure.

Source support: `src/egglab/learned_proposals.py:65–113` computes window mean/min
and global mean/spread from `prices`; `src/experiments/codex_local_campaign.py`
passes `market.a` to `v8_scores` and CatBoost `score_case`. The former builds a
graph sample with the shared features; `src/egglab/physical_route_graph_v6.py:157–175`
aggregates neighboring edge/node messages. `src/experiments/codex_train_classical.py:51–68`
applies fixed preprocessing and rowwise CatBoost raw-logit prediction. These are
interface facts, not observations about a saved model's responses.
`src/egglab/classical_controls.py:45–93` already implements the common selector
and restriction under policy `common-priceblind-top3-exact30-v1`, including
original-order masks, exact K, `exposure_slots`, `zero_exposure` and score/mask
hashes. Preserve and bind that implementation in the future source freeze; do
not route the comparison through the campaign's older rank-dependent `prune`.
The actual scorer/target-tariff wiring and paid-clock integration must also be
bound by the launch implementation; the helper alone establishes neither.

## Invariances and negative controls within assigned pairs

The cyclic permutation preserves the linear-price multiset. The current global
mean is the unweighted `np.mean(prices)` and spread is max minus min, whereas
window means use interval-overlap weights. In exact arithmetic the permutation
preserves global mean/spread and every nonwindow row's price features, even if
market periods have different durations. For the frozen rowwise CatBoost
interface, an exactly unchanged feature row with the
same preprocessing/model should have an unchanged score, although its rank may
move because other rows' scores change. Tiny floating-point changes near a tree
split can matter; feature closeness is not a guarantee of score equality. GNN
scores on unchanged rows may change through neighboring messages. This supplies
an architectural exposure diagnostic, not evidence that propagation improves
planning. Pullin-window features can also change and feed the graph even though
boundary movements are always retained.

Neither frozen learner receives `b`. Since the proposed intervention holds `b`
fixed, it cannot identify learned response to curvature. A hypothetical `b`-only
change would have no direct frozen-scorer input channel; do not add it as a new
arm here. The target optimizer's own response to `(a,b)` cannot be attributed to
learned ranking. The graph-versus-CA1 comparison also remains a complete-method
comparison with unequal information: CA1 receives both `a,b`.

Prespecify nested exposure labels instead of one binary success flag:

- **Structural zero choice:** the backbone consumes all K slots, or the selector
  retains every eligible movement. Ranking inputs cannot alter the retained
  topology. Report feature/score/latency responses anyway.
- **No transmitted feature/score change:** supplied prices change but relevant
  features or scores do not under the exact finite-value audit below.
  Label the first unchanged link; do not call an unchanged score useful tariff
  sensitivity.
- **Changed scores/order, identical mask:** the intervention does not cross the
  actual retention cutoff. This is zero realized mask exposure despite upstream
  response. Rank displacement alone does not establish changed search guidance.
- **Changed mask:** topology exposure occurred; trace its downstream use. A
  changed mask does not ensure different acquisition, native processing or bill.

Structural zero-choice and identical-mask pairs are negative controls for a
claim that the observed effect is transmitted by a changed retained topology.
Keep every such pair in the assigned mechanism estimand, at its original base
weight; do not replace bases, drop zero-exposure cases or recalculate a favorable
denominator. Exposure-conditioned summaries may be shown only as descriptive
post-intervention diagnostics.

An identical mask does **not** imply identical runtime or outcome. Recomputing
the two scoring inputs can consume different time; startup, thermal/shared-load
variation and wall-clock native search can differ; equal sets need not have
equal serialized ordering. Before interpreting this negative control, freeze a
canonical original-movement ordering so identical masks produce the same
restricted inventory/order. Even with identical serialized solver inputs and
seed, time left, native timing, acquisition/fallback and start processing can
differ. A valid outcome difference in an identical-mask pair belongs to the
timed method contrast or residual context variation. It is not proof of a
topology-mediated benefit, and it is not automatically an engineering failure.
Classify engineering failures only under the addendum's frozen receipt rules.

## Numerical comparisons to freeze before launch

No numerical tolerance is estimated from new data here. Use exact equality for
IDs, masks, orders, cardinalities, tariff permutation membership, input/model/source hashes
and target-parameter identities; raw hashes detect any byte difference. The
selector must retain its specified ordinary descending score order and exact
movement-ID tie rule, with **no epsilon tie modification**. Diagnostic tolerance
must never silently alter ranking, K, model inputs or replay admission.

The addendum already fixes the practical bill band above. CA1's `1e-6 kWh`
stress-screen tolerance has different units and purpose; it is not a feature,
logit, price or bill tolerance. Keep native replay's existing admission rules.

Proposed prespecified audit policy: compare aligned finite features and scores
by exact represented numeric value (`atol=0`, `rtol=0`); archive dtype, the full
values/hashes, change counts and maximum absolute deltas per feature and score
vector. Hash differences can distinguish serialization or signed-zero details
that numeric equality does not; do not equate a hash difference alone with a
value change. Reject nonfinite scorer inputs/outputs under the existing validity
contract. This policy detects any transmitted numerical change without inventing
an empirical sensitivity threshold. It does not declare every detected change
practically meaningful. Actual orders, cutoff crossings and masks remain exact.

The unweighted mean may change in finite precision when the reduction order
changes under a permutation. Report this separately as a numerical change in a
theoretically invariant summary, with its magnitude; do not automatically call
it learned tariff sensitivity or an engineering failure. If a tree split or a
rank cutoff transmits such a change, show that chain and label its numerical
origin. Avoid post hoc promoting roundoff to a meaningful learned response.

The future manifest must adopt this exact audit policy or choose and justify
alternative absolute/relative tolerances before generation/inference, explicitly
covering both binary64 feature arithmetic and the scorer's dtype. No practical
feature/logit equivalence threshold is supplied by the current plans; selecting
one remains necessary before launch only if such a claim is intended. Timing
differences should be reported as measured continuous diagnostics with clock
resolution, without inventing a favorable equivalence band. No new-data
calibration, threshold tuning, deletion or automatic rerun is authorized here.

## Claims the completed mechanism comparison can support

A complete, healthy contrast favoring fresh inputs supports a local,
startup-inclusive method benefit of supplying the shifted ranking prices under
this fixed target and policy, subject to assignment/context limitations. A
feature-to-mask response supports price-dependent topology selection. Observing
both, with the downstream receipt chain and zero-exposure controls disclosed,
is evidence consistent with a useful topology channel. It still does not
identify a pure topology-mediated causal effect: latency and adaptive search
also change, and no independent mask-only intervention is included.

Do not claim that learned price-dependent topology improves bills merely because
features/logits/ranks respond, the shifted target produces different charging,
or fresh wins on a selected both-valid/changed-mask subset. Report null,
identical-mask, failure and heterogeneous results, including worst regressions.
The full assigned 192-decision design and its missingness/accounting contract
remain intact; this note adds interpretation and freeze prerequisites only.
