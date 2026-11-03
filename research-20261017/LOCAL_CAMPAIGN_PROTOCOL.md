# Bounded local ranking-source development study, 17 October 2026

Design v2 (parent-directed pre-outcome amendments below control superseded v1 details). No experiments were executed to prepare this document. The companion
`LOCAL_CAMPAIGN_MANIFEST.json` freezes the full grouping and arm definitions before
case generation, scores, or outcomes. Execution remains blocked on the artifact and
interface lock below. This supersedes neither the historical recovery protocol nor
sealed final evaluation: it is a smaller, distinct ranking-source experiment first.

## Question and population

Does v8 ranking improve replay-valid cost under a common pruning rule over a cheap
nonlearned rule and random pruning, after inference and completion overhead? The newly trained 20261017 CatBoost
comparator joins if its frozen artifact and preprocessing are available before any
cohort scoring. It uses 80 fit / 16 inner / 32 historical outer TRAIN groups, seed17,
depth6/266trees selected on inner groups only. Artifacts are in
`research-20261017/classical-training/attempt1/catboost`. Availability is a file/interface
check, never a campaign performance screen; record any omission before scores and run
the remaining five arms unchanged. Do not select v8 folds or refit models from campaign outcomes.

Use claude-scale-v1, day tariff, sizes 40 and 80. Twenty distinct independently drawn
base IDs give ten timetables per size; the two qualification IDs are also disjoint.
The manifest gives every key and the outcome-independent SHA256 sampling rule over
50600–50999. This range is within the generator's authorized 50000–50999 development
namespace, outside sealed bank IDs. Each base appears at exactly one size: no prefix
pair is counted as an independent timetable. Shared synthetic construction and
borrowed TRAIN physical profiles remain a population limitation, not independent
physical systems. Profile overlap with model training must be disclosed.

Before generation, check only existing *development* manifests/log indexes for prior
use of these IDs; do not open sealed indexes. If prior use is found, retain the IDs
and label them previously exposed development groups; no outcome-based replacement.
The study remains development evidence even if IDs are new. No public cases or
sealed DEV/TEST/A6/B3/GIRO/confirmation data are opened. A promoted policy requires a
separate, prospectively frozen authorized final-test cohort; this study cannot supply
that claim. All tariffs, sizes, and solver seeds are paired, not independent samples.

## Arms and common policy

1. v8: graph-attention task00, fold 0 / training seed 17; fixed preprocessing.
2. CatBoost 20261017: newly trained fixed seed17 depth6/266trees model, exact
   training-time feature transform, conditional on the artifact/interface rule above.
   Legacy machine arm ID `catboost_v5` does not mean a historical-v5 replication.
3. Nonlearned: import the exact frozen `experiments.codex_offline_rank.heuristic`.
   Score = -travel_minutes -0.1*intertrip_gap +0.1*depot_dwell, larger is better.
   Travel minutes sum arrive_min-depart_min over legs with different endpoints;
   intertrip gap is after-trip start minus before-trip end; depot dwell is the gap
   between the depot-split legs. No labels, predictions or solver outcomes are used.
4. Random: ascending SHA256("egg-ranking-local-20261017-v1|case_key|solver_seed|movement_id").
   No Python process hash or RNG-version dependence; one frozen permutation per cell.
5. full4: unpruned, four tangent rounds, matched primary solver shape.
6. cold: unpruned historical one-full-budget/eight-round-cap policy, secondary control.

All restricted arms use global top ceil(0.30 * flexible_count), plus top-three
incoming and top-three outgoing flexible movements per trip, plus all pullouts and
pullins. Flexible means direct or depot. Apply the union once; never trim mandatory
per-trip coverage. Ties use movement ID, not current generation index. Rank ordinals
can be passed as decreasing numeric scores to a shared prune adapter. Record the
actual unique retained count and degree distribution for every arm: the same union
rule can yield different cardinalities. This estimates ranking-source performance
under a common policy, not a pure constant-cardinality causal effect. A separate
matched-count diagnostic would require its own prospective rule; do not add it after
seeing results. No recovery, widening, ensemble, warm start, LP ranking or fallback
acquisition is added in this stage. Failure is retained as a failure.

All arms use the same promoted replay completion and retention implementation, model
settings, hardware/backend and exact bill evaluator. For restricted and full4 arms,
each of four rounds receives at most one quarter of the remaining planner allowance,
subject to the shared cumulative deadline. Cold receives the remaining allowance
with at most eight rounds. Completion/replay time is inside the deadline. Always
replay on the original full case; keep the best *accepted replay-valid* incumbent
when a later extraction/completion fails. Never credit an unvalidated solver bill or
a restricted-model lower bound as a full-problem certificate.

## Budget and run order

Initial qualification: two frozen cases × all available arms × solver seed 17,
30 s end-to-end per run (12 maximum = 0.10 nominal CPUh). Hard total 0.5 CPUh includes
scoring, setup and failed runs. Qualification is an engineering gate only: no ranking
comparison, tuning or case exclusion from its outcomes. Proceed only when every
scheduled run emits a complete accounting/failure record, mappings agree, no accepted
plan fails independent full-case replay, retention regression tests pass, no deadline
overrun exceeds 2 s, and resource limits below are met. Infeasible/no-incumbent solves
are acceptable if correctly recorded; any admitted invalid plan blocks the study.
If qualification fails, repair infrastructure and version its lock; keep all attempts
inside the qualification ledger. If its 0.5 CPUh is exhausted, stop and report.

First substantive screen: 20 cases × 3 paired solver seeds (17, 41, 73) × at most
6 arms = 360 runs. Each has 60 s end-to-end, giving 6 nominal CPUh, leaving 2 CPUh of
the hard 8 CPUh screen envelope for scorer startup, monitoring, analysis and failures.
Five-arm branch is 300 runs / 5 nominal CPUh; do not spend saved capacity extending
timelimits or adding cases. The qualification allowance is separate and <=0.5 CPUh.

Interleave pairs: sort (case,seed) blocks by SHA256(salt|case|seed|block); rotate the
arm list by block index modulo arm count, alternating forward/reverse by block parity.
Two workers execute adjacent arms; finish a block before advancing. This reduces
thermal/time confounding. Never stop early for favorable effect sizes. At 7.5 charged
screen CPUh, stop dispatch; reserve 0.5 CPUh for shutdown/accounting. Interrupted or
undispatched cells remain explicit, never replaced. An incomplete cohort cannot pass
the promotion gate and is reported descriptively with the missingness table.

Two local workers initially, one thread each, including BLAS/torch/solver libraries.
No cluster. User handoff permits at most six single-thread workers, but this campaign
stays at two; raising concurrency requires a prospective resource-only amendment.
18 GB physical laptop memory is a whole-machine constraint. Cap worker RSS at 5 GiB
and summed worker RSS at 10 GiB, leaving roughly 7 GB decimal for OS/user activity.
Sample each process tree at <=1 s intervals, log system memory pressure/swap delta;
on worker/aggregate breach or sustained warning/critical pressure for 5 s terminate
both safely and stop dispatch. No automatic smaller-case replacement or retry under
new settings. If one worker alone exceeds 5 GiB, stop and revise prospectively.

## Timing and artifacts

Start the cold-start decision clock before model/scorer import/load, case/market
construction, preprocessing and inference. Stop after independent replay, exact bill,
and result materialization. Charge every solver build, repair, tangent round and
retry. Cache results may be reused operationally, but each algorithm pays its own
measured cold-start load and inference cost once per decision; report actual campaign
CPU spend separately so reused scoring is not double-counted in the spend ledger.
No inference timing from an unrelated old score file is admissible for the primary
endpoint. If offline scores are used, their fresh case-matched component timings and
startup cost must be locked, then subtracted from the 60 s deadline. Report warm
amortized timing only as a labeled secondary view. Set aside measured completion time
within the allowance; no post-cap successful repair can count toward the endpoint.

Each attempted cell emits manifest/version hashes, case identity and movement order,
arm/model/preprocessing hashes, solver seed and random permutation hash, retained
counts, machine/OS/Python/package/backend identity, start/finish UTC, monotonic wall,
process-tree user+system CPU, peak RSS and pressure samples, model load/feature/
inference/pruning/build/optimization/repair/replay timings, every candidate acceptance
or rejection and reason, best-valid-incumbent trajectory, round statuses, final exact
bill/vehicles, completion status, timeout/exception/termination details and charged
budget. Keep failed cells, partial records, stdout/stderr and unsuccessful candidates.
The parent common replay worker supplies retention/admission tests; no separate
ranking-specific numerical fix is permitted.

## Frozen analysis and numerical decision gates

Independent unit is base timetable. First compare seed-paired cells within group,
then take group medians; give each of the ten groups equal weight within size and
each size equal weight overall. Report both sizes separately. For valid paired bills
B_v8,B_control, gain = (B_control-B_v8)/B_control; bills must be positive or the
relative-bill gate is inapplicable. Both invalid is a tie; exactly one valid favors
that arm for failure-aware wins only. Never assign a fabricated finite bill penalty.
Report attempted, accepted-valid, no-plan, extraction/replay-rejected, infrastructure-
failed and missing counts separately; report conditional bill denominators explicitly.
An internal rejected candidate followed by a retained valid incumbent is a successful
cell but its rejection remains counted in diagnostics.

Primary economic comparator is the frozen nonlearned arm. Promotion to a separately
budgeted recovery study requires ALL of the following, on a complete screen:
- zero invalid accepted plans, no mapping violations or unaccounted budget overruns;
- v8 valid-plan count at least the nonlearned count in each size, and no more than
  one v8 validity loss among the 30 seed-paired cells of either size;
- at least eight of ten groups per size have all three both-valid seed pairs;
- median group bill gain >=1% overall, median >=0% in each size, and positive group
  gain in >=7/10 groups in each size (groups lacking three valid pairs count nonwins);
- no both-valid paired bill regression >5% versus nonlearned;
- versus random, v8 validity is no worse per size and median group gain >=0% overall.

All thresholds include scoring/repair overhead through the shared end-to-end cap.
Also report v8 vs CatBoost, full4 and cold with identical summaries; do not choose a
new primary comparator by results. CatBoost superiority is not required to enter a
recovery study, but if it matches/exceeds v8, explicitly state that graph complexity
has not earned its cost. Report group-level bootstrap intervals (resample groups
within sizes; 10,000 draws, analysis seed 20261017); these describe uncertainty, not a
post-hoc significance gate. Solver seeds are not resampled as independent timetables.
No time-to-quality promotion gate is used: there is no independently frozen quality
reference for fresh cases. Trajectories and time to paired terminal quality are
exploratory only. If any gate fails, label no-go/inconclusive and stop automatic expansion under this
protocol. Diagnose the failure and, when warranted, freeze a new prospective revision;
this does not end the user's research. Retain useful pruning engineering without claiming
learned superiority or fresh full-model generalization.

Recovery is next and separate: after ranking conclusions, prospectively freeze a
new cohort/budget and compare static pruning with widening/full restoration under a
common total clock. Do not combine its improvement with ranking-source effects.

## Known gaps and smallest next executable steps

Existing claude_e3_prune.py checks score case identity, movement order, logits and
score_seconds. claude_score_v8.py provides task00 and preprocessing loading, but its
cache timing is not cold-start timing. Existing prune uses movement index ties; the
driver starts its timer after case creation and lacks whole-process CPU/RSS, a hard
outer deadline, nonlearned/CatBoost interfaces and uniform four-round random shape.
The historical cold/random branch is not an adequate direct launcher for this study.
The scale generator deterministically shares timetable prefixes *only when the same
base ID is reused across sizes*; this manifest avoids that reuse.

1. Reconcile the offline scorer's output schema read-only with the E3 score contract.
   Add model/feature hashes and timings; verify the 20261017 CatBoost artifact and its feature
   transform are reproducible, or lock the five-arm branch before any cohort scoring.
2. Integrate the parent's common completion/retention changes and their focused tests.
   Add only a ranking adapter/shared ordering and accounting/deadline wrapper; no
   model or heuristic tuning. Hash generator, driver, completion code and artifacts.
3. Validate the manifest mechanically (22 unique base IDs, 10 per screen size,
   no cross-size reuse, legal namespace, three seeds), freeze case identities and
   movement maps for every listed key before inference, then freeze the artifact lock.
4. User execution authorization is already present. After those locks and parent review, run bounded
   qualification, evaluate its engineering gate, then the fixed screen. The parent launches the authorized campaign; this
   implementation worker performed no numerical runs while preparing the runner.

Source basis: research-20261016/HANDOFF_TO_GPT_20261016.md;
STATE_MAP_20261016.json protocol_specs/ml_quality sections;
src/experiments/claude_e3_prune.py; src/experiments/claude_score_v8.py;
src/egglab/claude_scale_cases.py and native_recharge.Leg/Movement definitions.


## Executable v2 amendments and commands

The executable driver is `src/experiments/codex_local_campaign.py`. Before any campaign
outcomes, the parent requested the exact offline audit heuristic and a newly fitted
classical comparator. These replace the v1 tuple heuristic and historical-v5-only
availability rule above. The function is `experiments.codex_offline_rank.heuristic`:
score = -travel_minutes -0.1*intertrip_gap +0.1*depot_dwell (larger is better), with
movement-ID tie breaking in pruning. CatBoost is the newly trained, frozen fit80/inner16
selected comparator in `classical-training/attempt1`; legacy arm ID `catboost_v5`
remains for compatibility and must not be described as a historical v5 replication.
It is optional solely by artifact availability at freeze. Logistic is outside these
six arms. All restricted arms and full4 share four-round caps.

Search phases are explicitly capped to leave `max(2 s, .10*T)` inside the shared
planner deadline for completion, including cold8. The planner deadline itself leaves
1 s for independent final replay and materialization. Thus search phases total no
more than T - preparation - 1 s - completion reserve. The native common completion
can use its remaining cumulative planner allowance; unused reserve is not free extra
time. Supervisor kills at T+2 s (then SIGTERM, 0.5 s, SIGKILL), but any result finalized
after T is invalid for the primary endpoint. Process startup is included in this outer
clock; worker's own monotonic clock starts at entry, so parent receipt is authoritative
for end-to-end overruns. Output and native events preceding termination survive.
A replay-valid worker result whose parent wall exceeds T must be reported censored,
even if it finishes inside the 2 s termination grace.

Mac resource supervision samples worker process-tree RSS/CPU every 0.25 s and system
memory-pressure/free percentage plus swap state every 1 s. Free percentage below 10
for >=5 s stops all workers. These platform commands must be permitted; monitoring
failure fails closed, stops workers and records a supervisor failure. Mock mode does
not invoke platform monitors. A prior attempt missing its final receipt blocks resume;
never remove that attempt to retry it. Fully completed successes and failures are both
skipped. Each output directory is bound to one stage, lock, and real/mock mode.

Freeze only once all source edits and classical model production have settled. The
freeze command generates all case identities/movement mappings without inference or
solving and hashes all egglab/experiment Python sources plus selected model files.
Changing any locked file blocks launch; use a prospective new lock/output directory
if a code correction is necessary. No command below was executed for numerical work
while preparing the runner.

From `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src`:

```sh
PYTHONPATH=. ../.venv-local/bin/python -m experiments.codex_local_campaign freeze --manifest ../research-20261017/LOCAL_CAMPAIGN_MANIFEST.json --lock ../research-20261017/local-assets-v2.json --v8-root /Users/nadan/Documents/ChatGPT/egg/claude-local/v8 --classical-root ../research-20261017/classical-training/attempt1
PYTHONPATH=. ../.venv-local/bin/python -m experiments.codex_local_campaign run --lock ../research-20261017/local-assets-v2.json --stage qualification --output ../research-20261017/local-qualification-v2
PYTHONPATH=. ../.venv-local/bin/python -m experiments.codex_local_campaign run --lock ../research-20261017/local-assets-v2.json --stage screen --qualification-output ../research-20261017/local-qualification-v2 --output ../research-20261017/local-screen-v2
```

The screen is the substantive pilot; no additional outcome-selected intermediate
pilot exists. Its runner checks complete qualification receipts, matching asset lock,
resource limits and absence of worker/infrastructure failures before launch. The
parent must additionally inspect native admission/retention test evidence. Execute
`PYTHONPATH=src python3 -m experiments.codex_local_campaign self-test` for a solver-free
mock that injects a failure, resumes, and proves both attempted tasks are skipped and
native failure events remain. This and Python compile checking passed locally.


Common admission policy amendment before qualification: in each round, preserve any
raw incumbent that independently passes the unchanged full replay and objective
checks if completion fails. Compare admissible raw and completed candidates by exact
true curved bill, and retain the best across rounds. A tangent objective alone cannot
select the incumbent or admit a mismatched bound. This policy applies to every arm.
Parent review of that shared native fix remains a launch prerequisite. The harness
also caps cumulative optimizer wall consumption across all rounds, so cold8 cannot
consume the reserved completion allowance merely by starting another round. Supervisor
receipts expose `endpoint_valid` and `endpoint_censored`; analysis must use the parent
receipt together with the worker result, never worker acceptance alone.

## Prospective v3 engineering amendment (after terminal v2 qualification)

V2 qualification is terminal: twelve supervisor receipts, no automatic retries.
Its lock, results and source commit 728ae96a remain preserved, and its recorded
supervisor censoring is not reinterpreted. Qualification supplies no model-selection
signal. The following v3 timing corrections supersede v2 timing only for a new,
explicitly frozen qualification revision; all cases, arms, models, keep rules,
seeds, economic gates, and screen budgets remain unchanged. The separate manifest is
`LOCAL_CAMPAIGN_MANIFEST_V3.json`; v2's manifest is preserved.

The parent records `parent_monotonic` in the immutable attempt receipt immediately
before subprocess launch. Worker deadlines use that same machine-wide monotonic
anchor, including interpreter startup/imports. Every arm reserves `max(3 s, .10*T)`
for final full-case replay and artifact/result materialization. This replaces the
v2 1 s finalization reserve. The existing `max(2 s, .10*T)` common completion reserve
inside the planner allowance remains unchanged, including cold8.

After `result.json` is completely written, flushed and fsynced, the worker captures
`finished_monotonic` and writes immutable `completion.json` with task, lock and result
hashes plus the shared anchor. Marker creation is accounting only; the decision
endpoint is finished result materialization. The supervisor validates all marker
identities/hash/timestamps and uses finished minus anchor for endpoint validity.
Missing/malformed markers are conservatively censored. Endpoint `wall_s` is this
materialization duration; `supervisor_elapsed_s` and `cleanup_wall_s` record monitoring
and owned process-group teardown separately. Cleanup/detection delays cannot change
a timely materialized endpoint. A worker result accepted before serialization can
still be censored when its finished result materialization exceeds T.

Additional diagnostics include planner-return elapsed time, planner JSON write time,
independent final replay time, final plan/replay artifact writes, and final result
materialization time. No deadline reserve is chosen from bill outcomes; this uniform
engineering revision addresses observed timing/admission bookkeeping failures only.

The 0.5 CPUh qualification ceiling is cumulative across revisions. Freeze v3 requires
`--prior-qualification-output` for the terminal v2 output. It validates the terminal
summary/receipt structure, derives prior cumulative charged CPU from the last complete
summary plus its final supervisor CPU, and locks hashes of prior campaign binding,
ledger and every attempt/supervisor receipt. Verification rejects later changes to
these evidence files. The prior charged amount is carried into the v3 asset lock,
initial ledger and supervisor spend before dispatch, together with v3 freeze cost;
there is no reset or manual floating-point override. Unused qualification capacity
is not used for model tuning. Any further engineering revision would need another
prospective amendment and cumulative carry-forward.

From the worktree's `src` directory, after parent review (commands not run here):

```sh
PYTHONPATH=. ../.venv-local/bin/python -m experiments.codex_local_campaign freeze --manifest ../research-20261017/LOCAL_CAMPAIGN_MANIFEST_V3.json --lock ../research-20261017/local-assets-v3.json --v8-root /Users/nadan/Documents/ChatGPT/egg/claude-local/v8 --classical-root ../research-20261017/classical-training/attempt1 --prior-qualification-output ../research-20261017/local-qualification-v2
PYTHONPATH=. ../.venv-local/bin/python -m experiments.codex_local_campaign run --lock ../research-20261017/local-assets-v3.json --stage qualification --output ../research-20261017/local-qualification-v3
PYTHONPATH=. ../.venv-local/bin/python -m experiments.codex_local_campaign run --lock ../research-20261017/local-assets-v3.json --stage screen --qualification-output ../research-20261017/local-qualification-v3 --output ../research-20261017/local-screen-v3
```

Solver-free fixtures now additionally verify timely versus late result materialization,
missing/malformed completion markers, cleanup-independent endpoints, and prior receipt
CPU/hash carry-forward, while retaining shutdown/descendant and no-retry coverage.


V3 carry-forward additionally charges a frozen conservative 10 CPU-seconds for v2
analysis, archiving and readback, because analysis CPU was not separately timed. This
10-second allowance includes (does not add again) the measured archive CPU recorded
in `qualification-v2-archive-manifest.json` (about 0.471 s). The v3 manifest freezes
that evidence path and allowance; freeze includes its hash and measured archive CPU
in the prior accounting lock. Thus prior qualification charge is the terminal v2
summary-derived amount plus 10 s (about 174.984 s total), before new v3 freeze/attempts.
