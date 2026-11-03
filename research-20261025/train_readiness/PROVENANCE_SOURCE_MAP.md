# TRAIN provenance source map for a minimal readiness read

25 October 2026. Source inspection only. No TRAIN manifest, preprocessing/model
JSON, rows, labels, outcome file, sealed metadata or checkpoint was opened; no
imports, tests, hashes, generation, replay, solver or fit ran. The paths below
are **prospective metadata candidates supplied by the parent**, not inspected
facts about their current contents. Current source describes an intended writer/
reader contract; it does not establish that historical executed bytes match it.

## Source chain and meanings

**Pool writer.** `pool_physical_route_training_v3.py` declares the exact128 output
and two exported tables at [lines12–17](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/pool_physical_route_training_v3.py:12).
It admits dataset receipts and pinned tables before pooling, preserves shard
order and records each dataset path, receipt/table/health digests and receipt
`shards` provenance ([lines33–51](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/pool_physical_route_training_v3.py:33)).
The original output is ROOT-relative `result/physical_learning/...`, whereas the
parent's selected copy is under `claude-local`. The filesystem move/copy chain
is not established by these APIs; actual manifest pins must supply that link.

**Canonical grouping.** The writer requires eight exact registry IDs per shard,
one `base_group=physical_v2_s{base_id}` per physical case, TRAIN split and generator;
source records must join on both group and base ID, with at most one source0 and
one source1 per base ([lines63–94](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/pool_physical_route_training_v3.py:63)).
`group_eligibility` carries availability, not a separate variant namespace.
The learning reader additionally checks case identity/profile against the
generator and market identity against `physical.market`, then groups both
source tariffs together ([model_v3 lines48–84](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v3.py:48)).
These sources contain **no general cross-generator alias map** to the warm
40/80-trip cohorts. Numeric base-ID nonoverlap alone cannot prove such closure.

**Physical variation is not an additional independent replicate.** The generator
maps each registered base to a deterministic profile: three SOC profiles,
20/28 services, three consumption levels and three depot-gap levels; geometry
draws use generator/base/duty/field ([assignment and draws](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:52)).
The case name encodes base, service count and profile, with one connector,
90kW resource, vehicle cost100 and deadhead cost0 in this version
([construction](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:139)).
No new cases or assignment values were materialized here. Repeated profile
settings are not proof of identical timetables; neither is a different ID proof
of independent generators or populations.

**Tariff assignment.** Source code defines source0 as flat a=.20, source1 as
a=.10 in zero-based periods18–21 and .30 otherwise. Both have30 periods and
b=1/900 throughout. The same function defines day cheap periods10–13 and late
22–25, but those are target markets, not the two source-label tariffs
([market API](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_cases.py:191)).
Thus source0/source1 are within-base market variants, and b has no training
variation in this API. The pool manifest itself has no explicit a/b arrays or
per-source `market_identity`; actual tariff lineage requires its source pins and
the fixed API, not an inferred meaning of arbitrary names.

**Teacher objective and label.** Source stages dispatch the compact hull coordinator
under their own source market ([campaign lines191–205](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/physical_learning_campaign.py:191)).
The declared source budget is GRB, one thread, pricing phase55/wall70,
four pricing/six master calls and numerical-QP master policy
([budget](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/learning_campaign_stage2.py:203),
[policy](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/learning_campaign_stage2.py:43)).
Catalog labeling chooses **one minimum replayed source column**, tie-broken by
column key, under `ops + supply(source_market, load)`
([selection](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/physical_learning_campaign.py:323));
supply is `Σ(aL+.5bL²)` ([definition](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:105)).
This is integrated system cost, not marginal-price payments, a pure-fleet teacher
or a certified global route optimum. The pooled learner forms x from case and
source-market a, and y from inclusion in that single source plan
([loader](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v3.py:69)).
`selected_vector` is binary movement membership after path recovery
([definition](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/learned_proposals.py:116));
it is not optimal-action probability, regret or pairwise tariff preference.

**Censoring and teacher quality.** Source input is exported only when a full plan
replays; a feasible label can survive child/native failure. The adapter explicitly
records `certified_for_reported_objective=False`, open curved optimality,
provisional/after-failure flags, statuses and bound-assessment fields in
`source_outcomes.jsonl` ([adapter lines185–255](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_learning_dataset.py:185)).
Those outcomes are not exported into the training pool; the pool carries
availability and digest lineage instead ([manifest lines85–117](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/pool_physical_route_training_v3.py:85)).
Its source registers a possible10037/source0 censor; actual presence/counts remain
unknown here. Do not convert a missing source into a zero/negative label.
Shard00 uses the composite parent/continuation admission, unlike shards01–15;
the composite receipt's parent/continuation commit fields are not automatically
embedded by `receipt.get('shards')` ([composite writer](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/physical_learning_composite.py:35)).

## Matched-training provenance, not merely checkpoint identity

The exact128 grouped split is80 fit/16 inner/32 outer for a fold, grouping all
observed source fleets by physical timetable. Timetable, then observed fleet,
then edge receive equal weight ([split/weight API](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v3.py:108)).
The classical trainer requires task00/fold0 group lists and fit-only feature
normalization matching the existing GNN split; it fits only fit groups, selects
by inner loss, freezes selection before outer exploratory evaluation
([trainer lines83–125](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_train_classical.py:83)).
CatBoost metadata writes seed, chosen configuration, qualification, model/source/
table hashes and feature names ([metadata writer](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_train_classical.py:113)).
Its source explicitly qualifies labels as single feasible incumbents, not optima
([qualification](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/experiments/codex_train_classical.py:22)).

GNN preprocessing writes features, fit-only mean/scale and three group lists, but
**not** the pool pin, training seed, selected epoch or full training budget in
that preprocessing object ([v8 lines252–268](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_graph_budget_v8.py:252)).
Those are elsewhere in task results, which are outside the proposed read set.
Task-to-seed mapping uses the inherited `(17,29,43)`, not current warm-evaluation
seeds17/41/73 ([base declaration](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/physical_route_model_v2.py:24)).
CatBoost's training seed is17. The generator's base ID/deterministic draw, model
training seed and native teacher random seed are three different concepts.
The teacher Budget has no random-seed field; the inspected wrapper does not
establish an explicitly controlled historical teacher seed. A pricing event's
`seed=True` means the initial a-price oracle call, not an RNG seed
([initial call](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_hull.py:927)).

## Minimal prospective metadata projection

Do not read these files now. Parent can freeze a single bounded metadata-only
readout of the following exact candidates and keys; absent keys must be reported
absent, not substituted by directory-name inference. No table follow-through.

| Candidate | Exact useful whitelist |
|---|---|
| `/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/pool_manifest.json` | `policy`, `train_only`, `base_ids`, `independent_groups_intended`, `groups_eligible_observed`, `groups_eligible_full_pair`, `source_fleets_intended`, `source_fleets_observed`, `feature_policy`, `target_outcomes_not_exported`; `group_eligibility[]`: `base_id`, `base_group`, `intended_source_count`, `observed_source_count`, `observed_sources`, `missing_source_labels`, `eligible_for_observed_source_supervision`, `eligible_for_full_pair_supervision`, optional `registered_censor`; digest-only `output_hashes`, `adapter_source_hashes` |
| Same manifest, shard lineage | `admitted_shards[]`: `shard`, `dataset`, `dataset_receipt_sha256`, `case_table_sha256`, `source_table_sha256`, `health_sha256_from_receipt`; optional `raw_attempt_provenance[]`: `shard`, `attempt`, `frozen_source_commit`, digest-only `frozen_source_hashes`, `input_hashes`. Do not descend to referenced files. |
| `/Users/nadan/Documents/ChatGPT/egg/claude-local/v8/task00/inner_progress/fit_only_preprocessing_and_groups.json` | `features`, `fit_groups`, `inner_groups`, `outer_groups`; report whether `pool_manifest_sha256`/`seed` exist, without assuming this writer supplies them. No need to export normalization vectors for this readiness question. |
| `research-20261017/classical-training/attempt1/catboost/preprocessing.json` | `features`, `fit_groups`, `inner_groups`, `outer_groups`, `pool_manifest_sha256` |
| `research-20261017/classical-training/attempt1/catboost/metadata.json` | `arm`, `seed`, `qualification`, `model_sha256`, `features`, `selection.candidate_index`, `selection.config`, digest-only `training_source_hashes`, `pool_table_hashes`; omit loss/accuracy values and predictions. |

Use explicit group→base mapping and check within-partition duplicates and
cross-partition group/base intersections. Count source tariffs within each
base; never treat two fleets or individual movement rows as independent groups.
Feature names identify tariff channels (`window_price_mean`, `window_price_min`,
`market_mean`, `market_spread`), while actual fit-only transform and topology
construction must remain matched in any later aware/blind design
([feature API](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/learned_proposals.py:19)).

## What this read can and cannot decide

It can establish declared pool linkage, split consistency, source availability,
selected-model provenance fields and the source-defined two-tariff supervision
contract. It cannot establish actual teacher optimality/gaps, per-tariff quality
balance, label disagreements, new tariff-label coverage, native teacher seeds,
all historical executed-source equality, arbitrary variant alias closure or
population independence. The exact proposed metadata set contains no per-source
quality summary; keep that unknown rather than opening outcome tables. GNN task
training/selection parity is likewise not fully established by its preprocessing
file alone. Missing source fields mean “not supplied in this bounded read,” not
“the evidence does not exist.”

A comparably trained blind model would require a separately specified matched
feature intervention, common grouped labels/splits/weights, architecture/fit/
selection resources, training seeds and independent evaluation. The current GNN
scored with day a is not that intervention. Existing source code offers a possible
supervision substrate, not readiness clearance to refit or regenerate anything.
