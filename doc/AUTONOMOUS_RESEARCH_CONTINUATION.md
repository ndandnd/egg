# EGG journal research continuation

Updated 30 September 2026 UTC. Root manages; GPT-6 Sol implements/analyzes and
Luna Max reviews. The user's latest instruction is to keep experiments and model
training moving without routine approval, even while exact solving remains slow.
The existing hourly `advance-egg-journal-research` heartbeat is ACTIVE. This
supersedes the earlier idle-monitor pause condition and blanket deferral of ML.
Notify only substantive findings, major decisions, important failures or review
artifacts. Continue useful local work between jobs; do not pause on an empty queue.

## Latest checkpoint — XGBoost, CatBoost and ExtraTrees submitted

- New explicit user direction: try different ML families now; explain current models
  and promising alternatives. This authorizes the next declared family comparison.
  Manuscript deferred; hourly automation ACTIVE; all prior data protections remain.
- Existing classifiers: regularized logistic, custom one-hidden-layer32-unit MLP,
  scikit-learn HistGradientBoosting, plus constant/kind-frequency controls. They score
  observed incumbent movements; fleet construction/charging/replay remain separate.
- **Array720831 submitted22:19:24Z.** Execution75dd4cf19f1f735cc3dea559567da3b2bd32013e;
  remote `/home/nc437/egg-route-families-20260930-v5`; output
  `result/physical_learning/20260930-route-model128-families-v5`. LAUNCH_720831.json
  and ROUTE_MODEL_FAMILIES_V5_PROTOCOL/CHECKS/REVIEW govern. Same exact128pool SHA
  d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d;255/256sources.
  No postsubmission queue or partial outcome read. Guard found no active EGG job;
  no dependency needed. No other project's job or held job changed.
- New menu: XGBoost depths3/6 and CatBoost depths4/6, at most800rounds,lr.05,
  weighted inner early-stop patience50; ExtraTrees300trees,leaf5/20. Same17features,
  four80/16/32 grouped folds and3seeds. Six candidates/task saved before outer scoring;
  config selection AND separately reported promoted-family policy use only inner
  weighted log loss. All3families are reported; no outer winner-selection. Dev/test
  sealed. CPU/runtime/imports and model roundtrips verified on tiny syntheticdata.
- Resource cap:12tasks%4,1CPU/8GB/30min/native1,1700s child cap,6requestedCPUh total,
  no retry/requeue,exclude scaglione-compute-01. All candidates, models, progress,
  failures and time retained. Global ceiling12requestedCPUs/96GB unchanged.
- New isolated runtime `/home/nc437/egg-route-family-env-20260930/bin/python` pins
  xgboost-cpu3.0.5,CatBoost1.2.8,sklearn1.7.2,numpy1.26.4,scipy1.13.1,joblib1.5.2.
  ROUTE_FAMILY_ENVIRONMENT.json and route-family-requirements-frozen.txt. Local tiny
  tests use tmp/route-family-v5-env plus DYLD_LIBRARY_PATH to sklearn/.dylibs;
  no system install/old environment mutation. Five focused fixtures passed, including
  native weighted stopping loss and best-iteration portable prediction checks.
- Prior array719750 all12 COMPLETED0:0, complete artifacts collected and raw backup
 491c2e9db7569e87f35c65457d699cdbba6f4114 pushed. ACCOUNTING_719750.json:
  task elapsed sum4340s,allocatedCPU5761s; task receipts sum4146.30s. These are not
  online inference time. RESULT_MANIFEST_ROUTE_MODEL128_BUDGET_V4.json pins2544files.
  All12tasks passed strict saved-model replay; MLP300 and tree200 anchors match v3.
  MLP full128 logloss .091523→.084204,AP .730048→.747740,top-k .659818→.673704;
  common32 also improves. Selected epochs730–1200;9/12stopped early. Tree extension
  is mixed: full128logloss .069894→.070373 worsens,AP/top-k slightly improve;
  common32all3worsen. Tree selections200/400/800=3/3/6. Logistic coefficients vary
  across repeats but maxprobability drift9.75e-5/logloss1.42e-6; retained as control
  drift, not a training-budget gain. See ROUTE_MODEL128_BUDGET_V4_RESULTS/REPLAY and
  RESULT_REVIEW. No refit or reserved outcomes. Sol/Luna finished; no pending edits.
- MODEL_FAMILY_COMPARISON_METHODS.md gives official APIs and graph/attention direction.
  Next neural package should encode timetable compatibility structure with a small
  graph network under its own frozen protocol; larger model size alone is no benefit.
  Retain cost-only/source charging controls and diagnose the failed route cover.
- Google Doc appended with current/new families, fixed selection rule, scope and
  graph direction;2links/all7nativefigures verified (DOC_MODEL_FAMILIES_V5_RECEIPT).
  Verified longer-training neural gain/mixed tree result appended with1report link
  and7images preserved (DOC_MODEL128_BUDGET_V4_RESULTS_RECEIPT). Report backup2b45560.
- Next: one scoped720831 check next wake, collect complete outputs when terminal
  and independently
  replay portable models with pinned versions, including best-round inference,
  inner selections and promoted policy. Never retry failed/partial tasks automatically.
  Then compare full128/common32 to existing baselines with timetable-level aggregation;
  no route-benefit claim from classification. Keep useful graph/data/decoder work moving.

## Previous checkpoint — matched charging resolves route attribution; longer training submitted

- User direction unchanged: sustained parallel ML/data research, manuscript deferred,
  automation ACTIVE, no routine approval. Sol implementation/analysis and Luna review
  are complete; no active local worker or pending edit. Report substantive results only.
- Arrays718744 (model128) and718861 (decoder) finished COMPLETED0:0; complete artifacts,
  logs and scoped accounting collected and backed up in c77b950. Task elapsed sums are
  1,404.35s and443.34s; actual allocated CPU totals2,344s and783s, distinct from requested
  CPUs and online runtime. No repeat solves/fits were used for result analysis.
- All12 model128 tasks passed strict saved-model replay under matching sklearn1.7.2.
  On the same original32 timetables, boosted-tree log loss improves
  .07378→.07157→.06928 and input-trip-count top-k recall .68792→.69867→.70066 for
  bank32/64/128. At128, 25/32 improve log loss over64, but recall changes are mixed.
  Neural gains remain small. Bank counts are not per-fold fit counts:20/40/80 fit,
  4/8/16 inner,8/16/32 outer. Labels are observed incumbent membership, not optimal
  routes. ROUTE_MODEL128_RESULTS/REPLAY and figures/route_model32_to128_common32
  provide the verified report and figure; source/report backup e947a0e.
- Decoder:12/16 learned arms replay as full fleets on TRAIN10036–10038; all4 arms on
  10039 fail to find an integral cover at the cap. Cost-only succeeds4/4. Five learned
  fleets use novel topology,7 reuse sources. Matched source charging eliminates every
  apparent learned route-cost gain: direct-or-recharged source policy matches/beats
  every learned fleet. Four predeclared timetables, not16 independent observations.
  The matched comparison used saved admitted TRAIN/day outcomes only after prospective
  protocol commit b33f028;7 available sources and1 censor preserved, no new solve.
  See ROUTE_DECODER_MATCHED_SOURCE_CHARGE_V1_RESULTS/REPLAY, its verifier and protocol.
- Cold solving found cheaper individual fleet columns on all3 learned-success cases.
  **All8 cold/retained hull mixtures are nonpure.** Their certificates apply to CH,
  not an optimal physical fleet D. Decoder V2 replay verifies every physical column
  and mixture distinction; retain historical V1 replay. Fixed-route charging OPTIMAL
  certifies only its linear subproblem; curved full-fleet bills are replayed exactly.
  No incremental learned cost benefit or matched-quality online speedup established.
- Coverage note:128 independent TRAIN groups,255/256 sources; main54 physical cells
  have2–3 groups, but stride is confounded (54/108 joint cells). Charger topology,
  power and terminal window are fixed. See TRAIN128_COVERAGE_NOTE. Dev/test remain sealed.
- **Longer-training array719750 submitted21:48:19Z**, after guard found no active EGG
  jobs. No postsubmission queue/partial outcome read. Execution e947a0e87f4977b74dab375fe4dabdbf55f98667;
  remote `/home/nc437/egg-route-model128-budget-20260930-v4`; attempt
  `result/physical_learning/20260930-route-model128-budget-v4`. LAUNCH_719750.json;
  ROUTE_MODEL128_BUDGET_V4_PROTOCOL/CHECKS/REVIEW. Same128 pool SHA
  d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d.
  Only MLP cap300→1200 and tree candidates100/200/400/800 change; existing features,
  architecture, regularization, folds/seeds and inner-only selection stay fixed.
  Motivation is all12 prior INNER curves improving through caps, not outer ranking.
  Pool loader materializes all rows; outer x/y are excluded from fitting/selection.
  Each checkpoint/progress survives partial failure;300/200 anchors retained.
  Twelve tasks%4,1CPU/8GB/30min/native1,1700s child cap,total6requestedCPUh,no retry,
  no requeue,exclude scaglione-compute-01. Global ceiling12requestedCPUs/96GB remains.
- Original Google Doc appended with verified model/decoder/matched-source findings,
  scope limits and longer-training protocol. Five links and all7 prior native figures
  verified; DOC_MODEL128_DECODER_RESULTS_RECEIPT.json. No manuscript revision.
- Next: one scoped719750 queue check; collect complete progress/models/logs/accounting
  when terminal, preserve failures, no retry. First compare actual-bank300/200 anchors
  against frozen v3 inputs/preprocessing/predictions, then replay only inner-selected
  models and report grouped full128/common32 comparisons without outer selection.
  Next bounded local package: saved-evidence diagnosis of10039 cover failure and why
  novel10037/10038 routes lose to matched source charging. Gate decoder changes on a
  specific mechanism. Version new data to deconfound stride and diversify charging/
  route structure; do not expand model size blindly, open dev/test, or stop at128.

## Previous checkpoint — 64-group gains verified; 128 training complete; route test submitted

- User direction unchanged: sustained parallel ML/data work, manuscript deferred,
  hourly automation ACTIVE. Root managed Sol implementation/analysis and Luna review;
  all workers finished, no pending agent edits. Report substantive results only.
- **64-group array717453 completed all12 tasks.** Saved models/predictions replayed
  without refit under matching sklearn1.7.2. Equal-timetable boosted-tree recall is
  69.6%; on the same original32 timetables, 68.8%→69.9%, log loss0.07378→0.07157
  (23/32 improved), AP0.8152→0.8265. MLP common32 results nearly flat, AP/recall slightly
  worse. These are modest, heterogeneous source-edge gains, not complete-route or
  online-speedup evidence. Inner validation selected100 trees in3 tasks,200 in9;
  MLP selected300-epoch cap throughout. See ROUTE_MODEL64_RESULTS.md, replay JSON,
  ROUTE_MODEL64_REVIEW.md and figures/route_model32_to64_common32.{png,pdf}.
  Replay pins both manifests and old32 replay plus common-shard input hashes.
- All final label shards10–15 admitted once:48 groups,96 source fleets,288 target
  plans, no new censors. Total **128 TRAIN timetables /1,019 replayed plans /five
  preserved censors**. Source labels remain provisional when native budgets ended;
  target OPTIMAL means fixed-route linear charging, not global curved-cost optimum.
  Exact128 pool retains255/256 source fleets, all128 groups; only10037/source0 is
  missing, with its known dependent target censors. See PHYSICAL_WAVE2_FINAL_ADMISSION.
  Raw backup0794ec8; admitted pool backupb0cc428; verified64 report/figure backup4e218ef.
- **128-group array718744 submitted20:37:04Z and all12 tasks subsequently confirmed
  COMPLETED0:0 by the decoder dispatch guard. Its artifacts remain UNCOLLECTED.**
  LAUNCH_718744.json; executionb0cc428; remote
  `/home/nc437/egg-route-model128-20260930-v3`; attempt
  `result/physical_learning/20260930-route-model128-v3`. PoolSHA
  `d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d`.
  Same frozen models/features/seeds;80fit/16inner/32outer per task. Next collect
  complete model/wrapper/log/accounting artifacts and replay saved models, no refit.
- **Route-decoder array718861 submitted20:48:25Z**, after confirming718744 finished.
  Execution35f00cf; remote `/home/nc437/egg-route-decoder-train-20260930-v1`;
  attempt `result/physical_learning/20260930-route-decoder-train-v1`.
  LAUNCH_718861.json and ROUTE_DECODER_TRAIN_PILOT_V1_PROTOCOL.md govern. Four tasks,
  at most4 concurrently,1CPU/8GB/30min/native1 each, total2requested CPUh, no retry or
  requeue, excluded scaglione-compute-01. No postsubmission decoder queue/outcome read.
  All prior label jobs are complete. Global ceiling remains12requested CPUs/96GB.
- Decoder evaluates fixed TRAIN groups10036–10039, day tariff, seed17 logistic and
  boosted models from32/64 banks. The four groups are out of bank for32 and outer
  held out for64. Compare learned covers to cost-only cover, first/nearest/cheapest
  exact-rescored source plans, cold native solving and retained-source solving.
  Charge repair, independent physical replay and global hull verification remain
  separate timed stages; source-topology matches count as reuse. Acquisition costs
  joined only after all choices. Failed arms receive no fallback-success credit.
  Five fixtures passed and bounded independent review found no launch blocker.
- Submission guard initially mistook child718830 for an unrecorded job. Scoped
  scontrol proved it belonged to718744; guard switched from child ID %A to parent %F.
  Initial guard stopped before checkout/sbatch, so no decoder compute was duplicated.
  DECODER_SUBMISSION_GUARD_RECEIPT.json preserves this infrastructure correction.
- Original Google Doc appended with verified64/common32 findings, stopping behavior,
  bank completeness and128 launch; two report/figure links verified, all7 prior native
  figures preserved (DOC_MODEL64_RESULTS_RECEIPT.json). No manuscript revisions.
- Next: collect128 first; one scoped decoder718861 check, collect if terminal and
  review complete arm/score/failure receipts. Assess replayed feasibility, novelty,
  exact target bill and matched stage timings before claiming benefit. Preserve all
  failures and spent time; no retries. Advance the next versioned dataset/model/decoder
  step from those findings. Keep dev/sealed tests and protected historical cases untouched.

## Prior checkpoint — verified learning gains; 64-group training submitted

- **32-group array716152 completed all 12 tasks.** Saved-model hashes, splits,
  preprocessing, predictions and metrics independently replayed without refitting.
  At the fixed input-trip-count candidate budget, held-timetable selected-edge recall
  is 14.2% for the kind-frequency control, 60.6% logistic, 66.2% Adam MLP and 68.8%
  histogram boosted trees. Boosted trees beat that control on all 32 timetables.
  See ROUTE_MODEL32_RESULTS.md, ROUTE_MODEL32_REPLAY.json and the paired-timetable
  figure. Equal timetable weighting follows seed and source averaging. These are
  observed feasible-incumbent edge labels, not optimal-route labels. No complete-route
  feasibility, cost improvement or online speedup is established. All MLP/tree runs
  selected their maximum allowed inner checkpoint; this is not proof against overfitting.
- Model32 allocation totals 784 CPU-seconds; model receipts total 351.79 seconds,
  summed over parallel tasks, not campaign wall time or online solve time. Raw outputs
  and accounting backed up at5c5916c; verified report/replay/figure atff40919b.
- Shard09/job715490 completed and was admitted once: 16 source fleets and48 target
  plans replayed; zero new censors. Cumulative admitted TRAIN bank is **80 independent
  timetables, 635 replayed plans, five preserved censors**. Six remaining label jobs
  **715491–715496** (shards10–15) were last observed RUNNING in the19:27 scoped check.
  Their remote checkout is `/home/nc437/egg-physical-parallel-labels-20260930-wave2`.
  No later label outcomes were checked in this run; individual receipts govern.
- **64-group array717453 submitted2026-09-30T19:41:59Z** under
  ROUTE_MODEL64_128_V3_PROTOCOL.md and LAUNCH_717453.json. Execution commit8da9d59e;
  remote `/home/nc437/egg-route-model64-20260930-v3`; attempt
  `result/physical_learning/20260930-route-model64-v3`. Twelve fold/seed tasks, at most
  four concurrent, each1requested CPU/8GB/30min/native1, no retry/requeue, exclude
  scaglione-compute-01. No postsubmission queue or partial-result check was made.
  Combined resource ceiling remains8label+4training workers/12requested CPUs/96GB;
  actual Slurm allocations must be recorded separately.
- Exact64 prefix pool has127 observed/128 intended source fleets. Source0 for10037
  remains missing; source1 retained, no imputation/retry. Pool hash is
  `64791ec33307612bd8ad7f3c2396c42e0ffdc44717d2c865fe268f61bdab5eb0`.
  Fresh v3 code preserves frozen32 model settings/features/seeds, fit-only transforms
  and inner-only checkpoint selection. Each64 task has40fit/8inner/16outer whole
  timetables. Equal timetable metrics handle unequal source counts; the original32
  evaluation timetables are a prespecified common-population comparison. Sol implemented
  and Luna independently reviewed; no pending worker edits. No64 model was fit locally.
- Original Google Doc updated with verified32 results, two source links and a native
  paired-timetable figure; all six prior figures preserved (seven total). Receipt:
  DOC_MODEL32_RESULTS_RECEIPT.json. Manuscript remains deferred; automation ACTIVE.
- Next: one scoped check of717453 and715491–715496, collect complete outputs with
  accounting, preserve all failures and admit each new shard once. Replay saved64
  models without refit, compare learning curves including common32 groups. After
  all shards0–15 are admitted, freeze exact128 pool and launch under already recorded
  budget. Continue structured route decoding, physical charging replay and separate
  global verification with cold/retained/retrieval/exact-rescore controls. Do not use
  reserved dev/test outcomes, tune on outer folds or retry unreceipted attempts.

## Prior checkpoint — stronger grouped training and remaining registry launched

- Latest human direction: continue sustained training with modern ML plus sound
  classical controls against overfitting. Manuscript deferred; hourly automation
  ACTIVE. Use Root to manage, Sol for bounded implementation and Luna for concise
  research/review. All workers completed their packages; no agent owns pending edits.
- **Array 716152 submitted 2026-09-30T19:22:15Z**, four tasks observed RUNNING and
  eight pending in the single startup check. Each requests 1 CPU / 8 GB / 30 min,
  native1, no retry/requeue, exclude scaglione-compute-01. One task was allocated
  two logical CPUs; retain requested/actual distinction. LAUNCH_716152.json governs.
  Remote `/home/nc437/egg-route-model32-20260930-v2`; sparse checkout of src, campaign
  docs and exact pooled inputs. Execution commit **8fc64fb**. No partial scientific
  outcomes were read. Attempt `result/physical_learning/20260930-route-model32-v2`.
- Frozen dataset: exact TRAIN prefix10000–10031, 32 timetables / 64 observed feasible
  source fleets / 32,148 candidate movements. Pool `20260930-route-pool32-v1`, manifest
  SHA `35251cbc8c81787263b51f6259820299e862fba97efa6b8d09c9b1f9c8211842`.
  Four outer folds × seeds17/29/43; each task has20fit/4inner/8outer whole timetables.
  Compare constant/kind controls, regularized LBFGS logistic, histogram boosted trees,
  and Adam MLP32. Inner groups alone select tree iterations/MLP checkpoint; fit-only
  preprocessing, no row-level validation, no outer tuning or refit. Predictions,
  convergence, curves, AP, probability metrics, fixed0.5 recalls/support and ranking
  recall at input-only k=tripcount are saved. These are edge scores, not route benefits.
  Seven focused fixture checks and bounded source review passed. Isolated environment
  pins sklearn1.7.2/joblib1.5.2/NumPy1.26.4/SciPy1.13.1; no global solver-env changes.
- **Wave2 label jobs715490–715496**, shards9–15 / IDs10072–10127, submitted
  2026-09-30T19:15:33Z and all seven observed RUNNING. Execution commit6b29c72;
  remote `/home/nc437/egg-physical-parallel-labels-20260930-wave2`;
  individual attempts `result/physical_learning/20260930-shardNN-attempt1`.
  Seven jobs ×1requested CPU/8GB/2h/native1, no retry/requeue; exclude
  scaglione-compute-01;14CPUh cap.
  NEXT_PARALLEL_LABEL_WAVE2_PROTOCOL.md and individual LAUNCH receipts govern.
  Combined ceiling remains8label+4training workers /12requested CPUs /96GB.
- Previous wave1 jobs712946–712952 all completed; every shard02–08 admitted once.
  448 intended outcomes:444replayed plans and4censors (one source failure and three
  dependent target labels for10037, outside current32prefix). Source charge projection
  exceeded roundoff budget; failure and all time preserved, no retry. Cumulative bank:
  **72 TRAIN timetables /571 replayed plans /5censors**, including original preemption.
  Wave1 child time4172.29s; allocated CPU time6036s across parallel jobs. Source incumbents
  remain provisional where native budgets ended; target OPTIMAL is only linear-LP.
  See RESULTS_PHYSICAL_PARALLEL_WAVE1.md / PHYSICAL_PARALLEL_WAVE1_DERIVED.json / accounting.
  Raw/admitted backup6b29c72; source/protocol/review/pool backup8fc64fb.
  Launch/handoff backup81c9ded. The original Google Doc now records the new grouped
  comparison, methods plan and failure counts; all text/three links and six existing
  figures verified (DOC_GROUPED32_LAUNCH_RECEIPT.json).
- MODERN_ML_METHODS_AND_VALIDATION.md links established tabular and recent RouteFinder/
  RRNCO graph-attention approaches, with explicit EV timetable transfer limits. No
  current-SOTA claim or route-quality claim. Preserve base-group splits, small fixed
  selection budgets, per-group seed averaging, learning curves and sealed dev/test.
- Next: one scoped check of716152and715490–715496. Collect complete outputs, companion
  model files, wrappers/logs/accounting and preserve all failures. Review saved32group
  predictions/models without refit, including optimizer convergence and fit/inner curves;
  report seed-averaged per-timetable metrics, not edge-row pseudo-replication. Continue
  censor-aware exact64/128prefix pooling, then structured route decoding/charging replay
  and matched cold/retained/retrieval/exact-rescore baselines. Do not promote classifiers
  from accuracy alone or train extra epochs solely to use compute. Keep all reserved
  outcomes sealed. Do not stop the campaign when this array or wave finishes.

## Prior checkpoint — parallel labels and completed route-model pilot

- The human requested parallel use of the cluster. The previous one-job bootstrap
  rule is superseded by PARALLEL_LEARNING_RESOURCE_PROTOCOL.md: up to eight label
  workers plus four training workers, each one requested CPU / 8 GB / one native
  thread. Label jobs have two-hour caps; training tasks 30-minute caps; no requeue
  or retries, exclude scaglione-compute-01. The hourly automation was updated and
  remains ACTIVE. Manuscript work stays deferred.
- Seven additional label shards, indices 2–8, were submitted as jobs **712946–712952**
  and all seven were observed RUNNING in the scoped startup check. They cover TRAIN
  groups 10016–10071. Execution commit 25aee9b; remote checkout
  `/home/nc437/egg-physical-parallel-labels-20260930-wave1`; independent attempts
  `result/physical_learning/20260930-shardNN-attempt1`. Individual LAUNCH receipts
  and LAUNCH_PARALLEL_LABEL_WAVE1.json govern. Do not duplicate their submissions.
- **Training array 713295 completed all 12 tasks**, exit zero. This is four grouped
  folds by three declared seeds on the immutable first eight groups, comparing
  constant, movement-kind, linear-logistic and 16-unit MLP scorers. Each learned
  model ran 240 fixed epochs. Saved probabilities and metrics replayed with maximum
  discrepancies 1.67e-16 / 7.42e-14. MLP held-group log loss 0.2083 does not beat
  movement-kind frequency 0.2079; Brier improves 0.0550 to 0.0527. Linear is worse.
  All methods have zero selected-edge recall at threshold 0.5, so 93.88% accuracy
  is an all-negative result. See RESULTS_ROUTE_MODEL_PILOT.md and its replay JSON. The
  pilot is movement classification from observed feasible source-fleet labels;
  it is not a route feasibility, global optimality or online speedup claim.
  All raw model outputs, preprocessing, curves, predictions, receipts and logs
  were collected. Total allocation CPU time was 100 seconds; model task receipts
  total 26.05 seconds. ACCOUNTING_713295.json and RESULT_MANIFEST_ROUTE_MODEL_PILOT.json
  preserve denominators and timing. Execution commit 656405c; raw backup 9c275ae.
- **Physical shard 1 / job 711779 completed and was admitted once**: eight new TRAIN
  groups, 16 source fleets and 48 fixed-route charging plans all replayed. All 24
  tariff comparisons are paired: nine ties, 15 non-ties across five groups, with
  two groups switching the winning source under different tariffs. Fourteen source
  topologies occur across 16 fleets. Eleven source solves ended budget_exhausted;
  the target LP optima are linear-tariff results, not global curved-cost optima.
  Slurm time 881 seconds; child time 791.66 seconds. See RESULTS_PHYSICAL_SHARD01.md,
  PHYSICAL_SHARD01_DERIVED.json and ACCOUNTING_711779.json. Raw/admitted backup 9c275ae.
- The admitted bank now has **16 independent TRAIN groups and 127 replayed plans**,
  with the original one preemption censor preserved. The completed pilot uses only
  the original eight groups. No dev, sealed-test or historical protected outcomes
  were read. The Google Doc already records the parallel budget and model design,
  with all six figures preserved (DOC_PARALLEL_LEARNING_RECEIPT.json). The verified
  pilot results and new shard findings are also appended, with two report links
  and all six figures preserved (DOC_ROUTE_MODEL_PILOT_RESULTS_RECEIPT.json).
  Reports, replay review and handoff are backed up at febc815.
- Next: on the next follow-up use one scoped check of jobs 712946–712952, collect completed attempts and admit each once.
  Implement a versioned pooled-dataset interface for predetermined prefix learning
  curves at 32 / 64 / 128 groups, not whichever shards finish first. Preserve source
  bounds/status and all censors. Diagnose optimizer convergence and class imbalance
  using training groups only; define ranking and structured decoding prospectively.
  Develop route decoding and charging repair, then
  compare with cold solving, retained plans, retrieval and cheap exact rescoring;
  keep global verification separate. Small model fits take seconds, so independent
  solver-label generation currently deserves most parallel compute. Do not keep
  refitting a tiny dataset just to use allocation time.

## Prior checkpoint — next eight-group training shard submitted

- **Recorded EGG job 711779**, submitted 2026-09-30T18:14:02Z. The guard found
  no active EGG job; no post-submission polling. Execution commit
  `b5647e78928a3b6bcdcc5448a8c5d5e8bad2f71d`; remote checkout
  `/home/nc437/egg-physical-shard01-20260930`; exclusive attempt
  `result/physical_learning/20260930-shard01-attempt1`. LAUNCH_711779.json governs.
- Job 709011 COMPLETED: 155 Slurm seconds, 149 wrapper seconds, 107.67 receipted
  child seconds. All 23 new charging cells replayed. Requested 1 CPU; Slurm
  allocated 2 logical CPUs; native/library threads requested 1; peak RSS 184868 KiB.
  Raw continuation, wrapper, logs and accounting are collected and preserved.
- Composite v2 admitted once in 6.74 seconds: 8 independent TRAIN groups,
  16 source plans, 47 target charging plans and 1 explicit preemption censor.
  Seven groups have all three tariff pairs; 23/24 comparisons are eligible.
  Parent allocation (713 seconds) and child time (667.82 seconds) remain separate.
  No incomplete cell was retried.
- At the preset 1e-6 tolerance, 20/23 pairs tie; all three non-ties are in base10003.
  Five of eight source pairs share topology; none share full plans; there are
  11 source topologies across 16 fleets. Source status: 13 budget_exhausted,
  3 certified. The 47 OPTIMAL linear LPs do not certify curved/global optimality.
  No new model fit. See RESULTS_PHYSICAL_SHARD00.md and PHYSICAL_SHARD00_DERIVED.json;
  do not repeat raw-parent audits. Immutable dataset:
  `result/physical_learning/20260930-shard00-composite-v2`.
- Raw/admitted dataset backup: 1aa42d4; report and Luna admission review: f694d48.
  The original Google Doc now records these findings and the learning direction;
  exact append, report link and all six figures were verified
  (DOC_PHYSICAL_SHARD00_RECEIPT.json).
- NEXT_PHYSICAL_SHARD01_PROTOCOL.md freezes unchanged shard 1, IDs 10008–10015:
  16 source route solves plus 48 charging labels. One requested CPU, 8 GB, one
  native thread, two hours; child/controller/shell caps 100/6600/6900 seconds;
  no requeue; exclude scaglione-compute-01. Protocol/source backed up before launch.
- Next: one scoped check of 711779. On completion collect the entire new shard,
  sibling wrapper and Slurm logs/accounting. Compile once with the existing v1
  adapter, review compact health, then continue shard 2. While jobs run, implement
  pooled route/edge training from source-fleet supervision ahead of the 32-group
  fit checkpoint. Avoid further selector tuning on ties. Subsequent learning-curve
  checkpoints remain 64 and 128 independent groups; keep prediction, charging
  repair and global verification separate. Development/test and historical
  protected IDs remain untouched; manuscript deferred; hourly automation ACTIVE.

## Prior checkpoint — continuation submitted; partial findings preserved

- **Recorded EGG job 709011**, submitted 2026-09-30T17:34:24Z. The guard found
  no active EGG job. No post-submission queue/outcome check. Execution commit
  `2460d43d4161449aaeeda0699e2f4ac10418f739`; fresh remote checkout
  `/home/nc437/egg-physical-continuation-20260930`; exclusive attempt
  `result/physical_learning/20260930-shard00-continuation-attempt1`.
  LAUNCH_709011.json and PROTOCOL_PHYSICAL_CONTINUATION.md govern; do not duplicate.
- Job 703461 was PREEMPTED after 713 allocation seconds. All 40 completed plans
  (16 source, 24 charging) passed independent physical/native replay and exact
  curved-cost checks. Raw evidence and both Slurm logs are preserved; no parent
  wrapper or complete-shard summary exists. One launched cell remains censored
  with unknown outcome and child time; exactly 23 cells were never launched.
- Source pairs share movement topology in 5/8 groups. Among the first four ordered
  groups, 9/12 tariff pairs tie within the preset 1e-6 tolerance; source0 wins two
  and source1 one, all three separated outcomes in base10003. This ordered prefix
  does not establish registry-wide generalization. No new model fit or speedup.
  See RESULTS_PHYSICAL_SHARD00_PREEMPTED.md and its replay JSON/reproducer.
- Sol implemented and Root/Luna reviewed a separate no-retry continuation for only the
  23 untouched charging cells. Parent inventory and source plans are frozen and
  checked; the interrupted cell is never retried. Budget: 1 CPU, 8 GB, one thread,
  45 minutes; child/controller/shell caps 100/2500/2600 seconds; no requeue;
  exclude scaglione-compute-01. Implementation and final review backed up before
  the guarded submission; the complete parent tree was copied into the new checkout.
- The separate v2 composite adapter admits parent plus continuation only after a
  successful continuation wrapper and 23 new receipts. It preserves row origins,
  the typed censor and separate spent-time totals, and replay-checks saved plans.
  Seven focused checks passed; full composite replay remains due on completion.
  Archive integration checks require collected parent stdout, which is gitignored.
- Parent evidence backed up at 8803962; reviewed results at 10ccbd7. The original
  Google Doc now contains the partial findings and prospective continuation, with
  all six figures preserved (DOC_PHYSICAL_PREEMPTION_RECEIPT.json).
- Next: one scoped check of 709011; collect accounting and the complete new attempt,
  sibling wrapper and Slurm logs on completion. Compile/review the composite once,
  then advance distinct eight-group training shards toward 32/64/128 independent
  groups and grouped learning curves. Compare constant/direct-bill/EdgePrior,
  ridge and a modest nonlinear baseline. Weak source-choice signal favors route
  proposals, not more epochs on ties. If preemption repeats, generalize this
  explicit censor/continuation policy rather than repeat bespoke recovery audits.
  No development/test data opened, no manuscript work; hourly automation ACTIVE.

## Prior checkpoint — train-only dataset adapter prepared during shard 00

- **703461 remains the sole recorded EGG job.** One scoped check in this follow-up
  observed RUNNING at 5:12 elapsed, 1 CPU / 8 GB, snavely-cpu-01 (recorded
  2026-09-30T16:05:30Z). No further queue check or partial scientific outcome
  access. Execution commit/path/budget remain the unchanged LAUNCH_703461.json.
- Sol implemented, Root and Luna reviewed a completed-shard dataset adapter:
  `src/egglab/physical_learning_dataset.py` and its experiments CLI. It validates
  train identity, exactly 64 cells/receipts, one matching successful wrapper,
  saved source lineage, physical/cost replay and fixed-route source joins. Failed
  cells remain censored; returned incumbents and curved LP bills remain uncertified.
  Source bounds are preserved imported evidence, not re-certified by this adapter.
- New PHYSICAL_DATASET_INTERFACE.md explains immutable outputs and usage. Input
  hashes and downstream adapter policy hashes are separate from frozen solver pins;
  the running job's code/protocol/pins were not edited. Input containers preserve
  full routes, graphs and direct pre-charge bills; outcome/status/time/bounds are
  separate. A future trainer must define an explicit numeric feature projection
  excluding IDs and outcomes. This package fits no model and opens no dev/test data.
- Four synthetic completed-shard fixture tests cover normal compile, missing cells,
  failed wrapper admission and mixed censored/replayed labels. Data health records
  group/regime/size denominators, source equality, exact paired margins/ties,
  descriptive winner entropy and exclusions. These are infrastructure checks, not
  results from 703461. CLI help and diff checks also passed.
- Next follow-up: one scoped check of 703461; if vanished, scoped accounting and
  complete receipts. Collect the entire NEW physical_learning attempt plus its
  sibling wrapper receipt. Compile once using the interface command, preserve all
  failures/time, review actual label yield and source-plan diversity, then continue
  justified new training shards toward 32/64/128 groups. Incomplete attempts remain
  archived and are excluded from training; do not retry automatically. Any resource
  scaling needs a recorded prospective budget, not renewed routine user approval.
- Manuscript deferred; hourly learning automation ACTIVE. No second job submitted,
  no fitted-model claim, and no original Google Doc append for infrastructure-only
  preparation; consolidate the next append with verified first-shard findings.

## Prior checkpoint — first expanded physical-training batch submitted

- **Recorded EGG job 703461**, submitted 2026-09-30T15:58:56Z. The guard found
  no active EGG job. No post-submission queue or scientific outcome inspection.
  Do not duplicate. Hourly learning automation ACTIVE; all workers finished.
- Execution commit `032d02d3f8f227a0716a3e74a66e55260f5139f8`; fresh remote
  `/home/nc437/egg-physical-learning-20260930`; exclusive attempt
  `result/physical_learning/20260930-shard00-attempt1` (note new result root).
  LAUNCH_703461.json, PROTOCOL_PHYSICAL_LEARNING.md and
  PHYSICAL_LEARNING_LAUNCH_REVIEW.md govern. Source/protocol backed up.
- User explicitly prioritizes extensive ML and puts manuscript drafting aside.
  Registry: 128 train / 32 development / 32 sealed test base timetables. This
  first shard materializes only eight train IDs 10000–10007 and 64 cells:
  16 source solves + 48 tariff-specific fixed-route charging labels. It fits no
  model. Full graph/route/charging outcomes and provisional bounds/status/time
  are retained for larger pooled fits and later route/whole-fleet proposals.
- New physical generator has battery spans 80/174.24/232.32 kWh, consistent drive
  and idle energy, explicit engines-off depot dwell, and independent 54-way
  factorial assignment of battery, size, consumption and depot access. All 128
  training constructive fleets replayed once. No development/test materialized;
  historical reserved 2004/05/2020/21 untouched. Eight focused tests and bounded
  independent reviews passed; 18 source hashes frozen.
- One requested CPU, 8 GB, one native/BLAS thread, 2 h; child 100/controller 6600/
  shell 6900 seconds; no retry/requeue; exclude scaglione-compute-01. No array.
  Later modest parallel workers require a prospective budget after label-yield
  review, as described in LEARNING_SCALE_PLAN.md. Do not block routine work on
  another user approval; current standing authorization covers continued training.
- Completed 700498: 1104 Slurm / 1099 wrapper seconds; all 44 plans and exact costs
  replayed. Ridge switches with tariffs but mean excess 0.5342 is worse than
  EdgePrior 0.0670 and nearest-price 0.1540 on four grouped timetables. Raw ff682c1a,
  reviewed report/replay eb6bde5. Original Google Doc append and two links verified,
  preserving all six figures: DOC_LEARNING_PRIORITY_RECEIPT.json. No draft edits.
- Next: one scoped check of 703461; accounting/receipts if vanished; collect full
  shard 00 evidence from the NEW physical_learning root. Check completeness,
  physical/cost replay, source-plan diversity, ties and margins, and actual time.
  Then continue justified training shards toward 32/64/128 groups, grouped model
  comparisons and route proposals. Keep tests sealed, preserve every failure,
  and avoid repeated broad audits or tuning only the old tiny development set.

## Prior checkpoint — first physical-learning shard ready for launch

- User priority is extensive ML work; manuscript drafting is set aside. The
  hourly automation was updated and remains ACTIVE. Continue dataset collection,
  grouped learning curves and route-proposal development beyond smoke tests.
- Job 700498 completed: 1104 Slurm / 1099 wrapper seconds, one CPU, 8 GB,
  285268 KiB MaxRSS. All 44 physical plans/costs independently replayed and all
  paired summary metrics checked. Ridge switches under tariffs but performs
  worse than the simple controls: mean excess 0.5342 vs EdgePrior 0.0670 and
  nearest-price 0.1540. Four independent groups, twelve variants. Raw backup
  ff682c1a, report/replay eb6bde5. Google Doc learning-priority append and two
  links verified with all six figures preserved: DOC_LEARNING_PRIORITY_RECEIPT.json.
- New generator and shard runner are ready: registry 128 train / 32 dev / 32
  sealed test, first eight training groups and 64 cells (16 source + 48 charging).
  Three explicit battery spans, consistent drive/idle energy, depot opportunities
  and a corrected full 54-combination physical factorial. All 128 training
  constructive fleets replayed once; no development/test case materialized.
  Eight focused tests, shell/design checks and independent physical review passed.
- Eighteen source pins; exclusive attempt
  result/physical_learning/20260930-shard00-attempt1. First allocation one CPU,
  8 GB, one native/BLAS thread, two hours; child100/controller6600/shell6900,
  no retry/requeue, exclude scaglione-compute-01. No active job yet. Root publishes
  and makes one guarded launch from /home/nc437/egg-physical-learning-20260930.
  PROTOCOL_PHYSICAL_LEARNING.md and PHYSICAL_LEARNING_LAUNCH_REVIEW.md govern.
- After collection, perform compact data-health/replay checks and advance new
  training shards toward 32/64/128 groups, with stronger models and route proposals.
  LEARNING_SCALE_PLAN.md records grouped validation, learning curves, baseline
  comparisons and a subsequent modest parallel-worker option. Freeze any later
  resource expansion before launch. No repeated broad qualification campaigns.

## Prior checkpoint — frozen-model tariff transfer submitted

- New user steering: broaden battery capacity and synthetic-route regimes;
  current 80-kWh usable span is a synthetic setting. Hyundai confirms 290.4-kWh
  nameplate; Son et al. use 20–80% SOC, giving 174.24 kWh at that pack size.
  Proposed 10–90% sensitivity gives 232.32 kWh. See the sourced next-dataset
  design BATTERY_REGIMES_AND_TRAINING_DIRECTION.md. No frozen attempt changed.
  Current ridge used only six training groups/twelve labels and a one-shot fit;
  next data work should expand independent physical/tariff regimes, not epochs.
  First collect 700498, then freeze a bounded implementation/labeling protocol.
- Latest scoped observation during this user question: 700498 RUNNING after
  17 minutes, one allocated CPU, 8 GB requested, on snavely-cpu-01. No partial
  scientific outcome inspected. This supersedes the unpolled launch observation
  below; no second job was submitted.
- **Recorded EGG job 700498**, submitted 2026-09-30T15:08:01Z after the guard
  found no active EGG job. No subsequent queue/outcome inspection yet.
  Do not duplicate. Hourly automation ACTIVE; all workers finished.
- Execution commit `15b0053aa2aaaea3d9ffbaafdc84dbf9c803af92`, backed up to the
  existing research branch. Fresh remote `/home/nc437/egg-tariff-response-20260930`;
  exclusive attempt `result/learning_campaign/20260930-tariff-response-attempt1`.
  `LAUNCH_700498.json`, `PROTOCOL_TARIFF_RESPONSE_TRANSFER.md` and
  `TARIFF_RESPONSE_LAUNCH_REVIEW.md` record the prospective design and resources.
- Four new development timetables, seeds 2032–2035 (20/28 services twice), each
  receive late-cheap, day-cheap and flat tariffs. Four independent groups,
  twelve tariff variants. Eight source acquisitions, then all twelve frozen
  model/control choices before 24 charging LPs and twelve cold controls.
  Always-0, always-1 and training-majority are prospective controls. No model
  refit; archived training-majority uses only the six original training groups.
- One requested CPU, 8 GB, one native/BLAS thread, 100-minute Slurm allocation;
  no retry/requeue, exclude scaglione-compute-01. Child 100 seconds, inference
  60, controller 5400 and shell 5700. Seven focused tests, pure design, wrapper
  syntax and bounded independent reviews passed. 27 source and seven input
  hashes frozen. Reserved seeds 2004/2005/2020/2021 remain untouched.
- Completed 697180: all 44 cells independently verified. Ridge beat cheapest
  direct selection on three of four cases, but chose source 1 everywhere.
  Always-source-1 and training-majority match it exactly; no adaptive advantage
  established. Report/CSV/figure at 433ca1c, raw evidence 59b3acab, independent
  replay c7d6bc5. Original Google Doc updated with a sixth figure and verified
  preservation of all previous content/images: DOC_CHARGE_RESPONSE_RESULTS_RECEIPT.json.
- Next: one scoped queue check of 700498; scoped sacct/receipts if vanished.
  Collect complete source/LP/cold labels, frozen choices, inference and timing.
  Verify paired exact costs and source lineage; compare tariff switching and
  excess by timetable, with source acquisition charged once per group. Keep
  one-LP, two-LP, shared inference and cold times distinct. No outcome-tuned
  refit or reserved-test access. Choose the next package from complete evidence.

## Prior checkpoint — charge-response result reviewed; tariff transfer ready

- Job 697180 completed successfully: 1427 Slurm seconds, 1421 wrapper seconds,
  one requested/allocated CPU, one native thread, 8 GB, 246832 KiB MaxRSS.
  All 44 cells and source topology, exact costs and prediction order were
  independently verified. Accounting and full result manifest are archived.
- Ridge chose source 1 on all four development timetables. Mean candidate-pool
  excess was 0.0555 versus 0.3901 for cheapest-direct and 0.1827 for the old
  EdgePrior. An always-source-1 rule and the six-pair training majority match
  ridge exactly; these were post hoc diagnostics in this completed attempt.
  No adaptive learning or global speedup has been established. Source acquisition,
  shared model processing and charging times remain separately reported.
- Raw evidence backed up at 59b3acab; independent verification at c7d6bc5;
  report, CSV and figure at 433ca1c. Original Google Doc update and sixth image
  verified, preserving all five previous images. Receipt:
  DOC_CHARGE_RESPONSE_RESULTS_RECEIPT.json. The saved-incumbent own-price
  pool has positive deviation witnesses in three of four cases, not a claim
  about unknown optimal fleets. See RESULTS_CHARGE_RESPONSE.md.
- Next package: unchanged frozen model on four new development groups, seeds
  2032–2035 with 20/28 services twice each. Every group has late-cheap 22–26,
  day-cheap 10–14 and flat 41/150 tariffs, equal nominal 30-hour mean and b=1/900.
  Eight source acquisitions, 24 charging LPs and 12 cold controls: 44 cells.
  Always-0, always-1 and training-majority controls are now prospective.
  All twelve choices precede target outcomes; no refit. Four independent groups,
  not twelve. Reserved seeds 2004/2005/2020/2021 remain untouched.
- Budget: 100 seconds per child, 60 seconds inference; controller 5400,
  shell 5700 and Slurm 6000 seconds. One CPU, 8 GB, one native/BLAS thread,
  no retry/requeue; exclude scaglione-compute-01. Bounded independent code
  review found no blocker. Root finishes publication and a single guarded
  submission from /home/nc437/egg-tariff-response-20260930. No launch yet.
  Existing hourly automation ACTIVE. Never duplicate the completed attempt.

## Prior checkpoint — grouped charge-response training/evaluation submitted

- **Recorded EGG job 697180**, submitted 2026-09-30T14:15:07Z after the guard
  found no active EGG job. No subsequent queue or outcome inspection yet.
  Do not duplicate. Hourly automation ACTIVE. All workers finished.
- Execution commit `9232d5250158d7402c896de33c99d0225e8a914a`; fresh remote
  `/home/nc437/egg-charge-response-learning-20260930`; exclusive attempt
  `result/learning_campaign/20260930-charge-response-attempt1`.
  `LAUNCH_697180.json`, `PROTOCOL_CHARGE_RESPONSE_LEARNING.md`, and
  `CHARGE_RESPONSE_LEARNING_LAUNCH_REVIEW.md` are authoritative. Source pushed.
- **44 cells:** 20 source acquisitions; 12 training charging labels; one
  fit/inference call; then eight development charging and four cold cells.
  Fresh training seeds 2022–2027 have 12/20/28 services twice each; development
  seeds 2028–2031 have 20/28 services twice each. All six training pairs must
  replay before fitting. Missing labels cause a recorded model failure while
  independent controls continue. All four development choices are frozen before
  any development outcome. Ridge penalty 1.0, training-only scaling, no tuning;
  old EdgePrior retains its original topology projection and tie rule.
- Labels are nonlinear costs from the pinned linear-tariff charging procedure,
  not minimum nonlinear costs for those routes. Compare each one-LP chooser's
  cost, feasibility and excess over the paid best of two LPs. Baselines are
  cheapest-direct, nearest-price, old EdgePrior, two-LP best and contextual cold.
  Preserve source acquisition, model/inference/LP/replay time, all failures and
  provisional labels separately. Candidate-pool excess is not global regret.
- Budget: 44 children capped at 100 seconds plus a 60-second fit/inference call;
  controller 5400, shell 5700, Slurm 6000 seconds (100 minutes). One requested
  CPU, 8 GB, one native thread; no retry/requeue; exclude scaglione-compute-01.
  Eight focused tests, wrapper/design/diff checks and bounded reviews passed.
  23 source pins and three archived old-model inputs. Reserved seeds
  2004/2005/2020/2021 remain untouched.
- Previous job 696684 completed in 84 seconds (wrapper 78): one requested CPU,
  two allocated, one native thread, 8 GB, MaxRSS 154000 KiB. All eight original
  and eight recharged plans verified. Recharging improves archived native
  controls on both 28-service cases by 1.277433 and 2.163295; nonlinear/global
  optimality remains unknown. Raw backup e8fb362, replay 2bdaaef, report/CSV/figure
  55e3e16. Google Doc append and fifth image verified, preserving all history:
  `DOC_FIXED_SOURCE_CHARGE_RESULTS_RECEIPT.json`.
- Next: one scoped queue check of 697180; scoped accounting/receipts if vanished.
  Collect the full catalog/labels, coverage/model/proposals/inference and logs.
  Verify prediction order and exact-cost/source lineage; compare paired excess
  costs and all paid time. No outcome-tuned refit or test access. Choose the
  next justified data, model or solver package from complete evidence.

## Prior checkpoint — grouped charge-response learning ready for one launch

- No active EGG job: 696684 completed, all eight direct and eight recharged
  plans independently verified. Best recharged costs 516.150310 /684.511264 /
  522.238860 /683.304406 for seeds 2016–2019. Both 28-service cases improve
  their archived native controls; nonlinear/global optimality remains unknown.
  Source acquisition separately paid. Slurm84s/wrapper78s, requested1CPU but
  allocated2, native thread1, 8GB, MaxRSS154000KiB; all actual usage preserved.
- Raw evidence e8fb362; independent replay2bdaaef; report/CSV/figure55e3e16
  backed up to GitHub. Original Google Doc append, report link and fifth figure
  verified, with all four previous images preserved. Receipt:
  DOC_FIXED_SOURCE_CHARGE_RESULTS_RECEIPT.json. Result workers finished.
- New charge-response learning runner/model/protocol/wrapper/tests are ready.
  Fresh train2022–27 (12/20/28 services twice), dev2028–31 (20/28 twice).
  Twenty source cells, twelve training charging labels, then all four frozen
  predictions before eight dev charging and four dev cold cells:44 total.
  Fixed ridge1 predicts per-trip post-charge cost change; train-only scaling,
  no tuning. All six pairs must replay; otherwise model failure is preserved
  and independent controls continue. Old EdgePrior retains exact projection rule.
- Labels describe the pinned linear-tariff charging procedure's nonlinear cost,
  not minimum nonlinear route cost. Compare cheapest-direct, nearest-price,
  old EdgePrior and ridge one-LP choices against paid two-LP best and cold.
  Account for source acquisition/model preparation/inference/LP/replay separately.
  Report candidate-pool excess, not global regret or premature speedup claims.
- Eight focused tests, wrapper syntax, design and diff checks passed. Independent
  bounded reviews checked leakage/order/failure continuation/baseline semantics;
  root verified final fixes.23sourcepins/3old-model-inputpins. Budget44×100s
  children +60sfit, controller5400/shell5700/Slurm6000s;1CPU8GBthread1,
  no retry/requeue, exclude scaglione-compute-01. Reserved2004/05/2020/21untouched.
- Root next: commit/push and submit once from fresh
  /home/nc437/egg-charge-response-learning-20260930, exclusive attempt
  result/learning_campaign/20260930-charge-response-attempt1. Launch guard must
  reject any active EGG job/existing checkout. Record job/receipt before ending.
  Existing hourly automation ACTIVE. Read newest state before acting.

## Prior checkpoint — charging comparison collected; training-label follow-up being scoped

- Job 696684 COMPLETED exit 0 in 84 Slurm seconds (78 wrapper seconds).
  Requested one CPU; Slurm allocated two, while native threads remained one.
  8 GB, MaxRSS 154000 KiB, node snavely-cpu-16. Eight cells completed; complete
  raw attempt/wrapper/logs collected and 77 files hashed (68 Git-included).
  ACCOUNTING_696684.json / RESULT_MANIFEST_FIXED_SOURCE_CHARGE.json preserve it.
  No active EGG job as of collection. Existing hourly automation ACTIVE.
- All eight fixed-source charging LPs returned replayed plans with linear-LP
  status OPTIMAL; full nonlinear/global optimality remains unknown. Best of two
  nonlinear costs: 2016 516.150310, 2017 684.511264, 2018 522.238860,
  2019 683.304406. Both 28-service cases improve their archived native target
  controls. Child times about 5–6 seconds; source acquisition is separately paid.
  No matched-runtime speedup claim. Independent replay now verifies all costs,
  topology, identities and hashes; nonlinear/global optimality still unknown.
- Root manages: Energy verifies eight plans/topologies/costs and scoped bounds;
  Luna writes reproducible CSV/report/figure; Sol implements fresh grouped training
  with route quality judged after charging rather than inherited schedules.
  Approved44cellprofile: train2022–27 (12/20/28 twice), dev2028–31 (20/28 twice);
  20source →12trainLP →fixedridgefit/inference →8devLP+4devcold. Training-only
  scaling, fixed hyperparameters, no tuning; six trainpairs exploratory. Perchild100s,
  trainer60s, controller5400/shell5700/Slurm6000s (100min),1CPU8GBthread1.
  Failures preserved; failed learning must not stop independent dev controls.
  No new launch before specific protocol/code/resource budget review.
- Next: finish current evidence review, GitHub backup and original Google Doc
  append, then implement/launch the next bounded data/training package. Keep
  reserved seeds 2004/2005/2020/2021 untouched; no duplicate submissions.

## Prior checkpoint — fixed-source charging comparison submitted

- **Recorded EGG job 696684**, submitted 2026-09-30T13:09:07Z after a guard
  found no active EGG job. No post-submission queue/outcome inspection yet.
  Do not duplicate. Existing hourly automation ACTIVE. All workers finished.
- Reviewed execution commit c9f50bfc6a5cc916da4ea10f9e2747e6ccd4a338, fresh remote
  /home/nc437/egg-fixed-source-charge-20260930, exclusive attempt
  result/learning_repair/20260930-fixed-source-charge-attempt1.
  LAUNCH_696684.json, PROTOCOL_FIXED_SOURCE_CHARGE.md and
  FIXED_SOURCE_CHARGE_LAUNCH_REVIEW.md are authoritative. Backed up to GitHub.
- Eight fixed-route charging cells: source0/source1 on development 2016–2019.
  The LP optimizes the linear target tariff; independently replay and exact-score
  the nonlinear target cost. No route MILP, refit, fresh hull or global optimum
  claim. Best-of-two LPs pays both; cheapest-direct and frozen learned source
  choices each pay one. Retain original schedules as candidates. Unknown time
  remains unknown; all failed/timeout children retain provisional feasible plans.
- Budget: 45-second phase / 55-second wall / 100-second child; controller 1200,
  shell 1350, Slurm 1800. One CPU/8 GB/native thread, no retry/requeue, exclude
  scaglione-compute-01. Twenty related pure tests passed; after final status/time
  fixes six focused tests passed. Twelve source pins, 18 archived input pins;
  bounded independent review found no remaining blocker. Reserved seeds untouched.
- Prior transfer job 696441 completed: 18 feasible cells, 941 seconds. New
  20-service near-optimal physical plan costs 520.892028, target lower 520.793306;
  own-price deviation saves 0.486362 but true cost rises to 521.004698. Exact
  optimum support unresolved. Learning did not beat cold solving overall; the
  28-service learned repair had a costly extra bus at its time limit.
  Evidence b26e6d9; report/CSV/figure 13fe963. Original Google Doc now includes
  the result and fourth figure, preserving history; DOC_TRANSFER_RESULTS_RECEIPT.json.
- Next heartbeat: one scoped queue check of 696684, scoped sacct/receipts if
  vanished. Collect the complete eight-cell attempt and wrapper/logs, independently
  replay and analyze single-LP, two-LP and unchanged-source controls. Include
  source acquisition/model preparation and failed time. Historical target bounds
  are not fresh online certification. Use the baseline findings to choose the
  next training/solver package; do not access reserved 2004/2005/2020/2021.

## Prior checkpoint — transfer reviewed; fixed-source charging comparison ready for launch

- Completed job 696441: 18/18 feasible cells, 941 seconds, one CPU/8 GB,
  339384 KiB MaxRSS. Complete attempt/wrapper/accounting and 185 hashes preserved.
  No active EGG job as of collection; no retry. Hourly automation ACTIVE.
- Independent replay verifies all 18 labels and four new repaired fleets. On the
  new 20-service development timetable, the best physical fleet costs 520.892028
  with target lower bound 520.793306 (physical gap at most 0.098722). Another
  verified fleet saves 0.486362 at its own-load prices but costs 521.004698 in
  true system cost. This concerns a near-optimal incumbent, not support of the
  unknown exact optimum. For 28 services, the physical gap remains wide.
- Frozen learned proposals did not beat cold solving overall. Learned direct
  route repair was cheaper but slower for 20 services; its time-limited cover
  had an extra bus and much higher cost for 28 services. No speedup/generalization
  claim. Report, CSV and cost/time figure backed up at 13fe963; evidence b26e6d9.
  Original Google Doc append, report link and new figure verified; all three
  prior figures preserved. DOC_TRANSFER_RESULTS_RECEIPT.json records the update.
- Next package is the missing cheap baseline: fix each of two pre-target source
  fleets' routes for development seeds 2016–2019, minimize charging at the target
  linear tariff, independently replay and rescore the nonlinear target cost.
  Eight cells, no route MILP/refit/fresh hull. Single-LP cheapest-direct and frozen
  learned source choices are separate from paying for both LPs and choosing best.
  Original schedules remain alternatives because linear charging can worsen F.
- Prospective budget: 45-second charge phase / 55-second wall / 100-second child;
  controller 1200, shell 1350, Slurm 1800 seconds; one CPU/8 GB/native thread,
  no retry/requeue, exclude scaglione-compute-01. Protocol/runner/wrapper and
  tests passed: 20 related checks, then 6 focused checks after final fixes.
  Failures retain feasible replayed plans with provisional status. No unknown
  time becomes zero. Reserved 2004/2005/2020/2021 untouched.
- Root next: commit/push and submit exactly once from
  fresh /home/nc437/egg-fixed-source-charge-20260930; exclusive attempt
  result/learning_repair/20260930-fixed-source-charge-attempt1. Record job receipt
  before ending turn. Do not duplicate any existing submission. After completion,
  assess whether stored topology selection adds value once charging is updated;
  use that evidence for the next training or solver package.

## Prior checkpoint — independent transfer collected; diagnosis before next campaign

- Job696441 COMPLETED exit0 in941s, oneCPU,339384KiB on snavely-cpu-01.
  Complete18cellattempt/wrapper/logs collected;185hashes in RESULT_MANIFEST_TRANSFER.json,
  ACCOUNTING_696441.json. No activeEGGjob; no retry. Automation ACTIVE.
- Summary18/18feasible labels; frozen inference succeeded3.995s beforetargets.
  Initialcompactresults:2018/20 allnativephysical520.892, warmhulls certified
  about520.793 while physicaloptimumunknown.2019/28 learnednative685.709 vs
  cheapest689.533, cold685.468; directsharedlearned782.648 vs costonly693.552.
  Do not admit beyond independent review or call this generalMLbenefit/speedup.
- Activeworkers: Energy independentlyreplays18labels/candidatebounds and scoped
  own-pricewitness; Luna producesTRANSFER_CELLS.csv/results/figure; Sol diagnoses
  model-vs-time-limitedsearch and recommendsnextboundedpackage (noimplementationyet).
  Root collected185files and startedtrustedDocread; no newjobsubmissionauthorized
  untilnextspecificprotocol/resourcebudgetreviewed. No duplicates/broadsweeps.
- Next: complete evidence review, back up andappendoriginalGoogleDoc; use observed
  bottleneck/negativelearnedrepair outcome tochooseconcrete nexttraining/solver
  package.2004/2005/2020/2021 reserved untouched. Sourceboundsnevertransfertotarget.

## Prior checkpoint — independent transfer campaign submitted

- **Recorded EGG job 696441**, submitted 2026-09-30T12:06:42Z. Scoped startup
  check: PENDING, one requested CPU/8GB. No outcome inspected; do not duplicate.
  Existing hourly automation ACTIVE. All three workers finished; no pending edits.
- Execution commit `2f382902163c55d565f0964320d9e7c47cb036ae`, fresh remote
  `/home/nc437/egg-transfer-campaign-20260930`, exclusive attempt
  `result/learning_campaign/20260930-transfer-attempt1`.
  LAUNCH_696441.json / PROTOCOL_TRANSFER_CAMPAIGN.md / TRANSFER_LAUNCH_REVIEW.md
  are authoritative. No old checkout or other project/held job altered.
- Only new development 2018/20services and 2019/28services generated. Frozen
  stage-2 model, no refit. Reserved 2004/2005 plus future size-matched
  2020/20services and 2021/28services stay unmaterialized. Four source cells,
  one prospective inference attempt, then ten target native and four repair
  cells (18 total). Direct prediction/replay, repair and hull checking distinct.
- Budget: native70solver/100hard; repair30cover,45/55charge,70hull,240hard;
  inference45hard; controller3000/shell3300/Slurm3600; oneCPU/8GB/thread,
  no retry/requeue, exclude scaglione-compute-01. Fourteen pure tests, wrapper,
  31 source pins/design/diff checks and two bounded reviews pass. Failed
  inference kept without retry; independent controls continue. A projected
  learned proposal needs successful hash-checked inference. Provisional feasible
  repairs survive later hull failure with failure status and unknown optimality.
- Prior job 696067 complete in214s: replayed five-bus direct repairs689.100163
  learned/691.228570 cost-only, covergap~0.20. New saved physical685.695043,
  targetglobalLB597.829694; wide gap87.865349. Among21replayedplans, own-price
  regret>=5.092135 at that incumbent; no unknown-optimum support claim.
  Exact results/independent replay/core evidence backed up5a7c7b04, pool review
  25fe868. Original Google Doc append verified; three previous figures retained.
  DOC_SHARED_BUDGET_RESULTS_RECEIPT.json records it. No general ML or speedup claim.
- Next: one scoped queue check of696441, scoped sacct/receipts if vanished;
  collect complete18cellattempt, catalog/inference receipt, native logs, wrapper.
  Independent same-case/market replay and costs, bound status, full paid times;
  source acquisition once per timetable, shared inference once, don't add lookup
  twice to worker wall. Preserve every failure. Choose next bounded campaign
  step from this evidence; no automatic refit, budget escalation or test access.

## Prior checkpoint — independent transfer campaign ready for one launch

- No active EGG job: 696067 completed in 214s, full evidence collected and
  independently reviewed. Two new five-bus direct repairs cost 689.100163
  (learned) and 691.228570 (cost-only); both cover gaps stay about 0.20. New
  saved hull physical plan 685.695043, best fresh target lower 597.829694;
  physical gap 87.865349 stays wide. A 21-plan own-price comparison witnesses
  regret >=5.092135 at this incumbent, not the unknown optimum. Candidate and
  pool reproduction checks pass; exact fractions/hashes retained.
- Core result backup 5a7c7b04; pool review 25fe868. Original Google Doc append
  verified, including history/three figures, heading and result hyperlink;
  DOC_SHARED_BUDGET_RESULTS_RECEIPT.json records it. All result workers finished.
- New transfer runner/protocol/wrapper/tests ready: independent development
  2018/20services and 2019/28services, existing frozen stage-2 model, no refit.
  Reserve 2004/2005 and new 2020/20services,2021/28services without generating
  them. Four source cells before one inference attempt; then each group's
  cold/retained/nearest-price/cheapest-bill/learned target + two shared repairs.
  Exactly 18 cells. Direct proposals, repair, global verification and paid
  source acquisition are separately receipted; failures/provisional labels kept.
- Budget: native70solver/100hard; repair30cover,45/55charge,70hull,240hard;
  inference45hard; controller3000/shell3300/Slurm3600; oneCPU/8GB/thread,
  no retry/requeue, exclude scaglione-compute-01. Protocol and launch review
  recorded before outcomes. Fourteen pure tests, wrapper syntax, 31 source pins,
  design and diff checks pass; independent review found no remaining blocker.
- Next root action: commit/push, guarded fresh checkout and one submission;
  record job/launch receipt before ending turn. No duplicate or old-job retry.
  New attempt result/learning_campaign/20260930-transfer-attempt1;
  planned remote /home/nc437/egg-transfer-campaign-20260930.
  Existing hourly automation ACTIVE. Check latest state/receipts before acting.

## Prior checkpoint — 28-service repairs collected; independent development expansion being implemented

- Job 696067 completed, exit 0, 214 seconds, one CPU, max RSS 301796 KiB.
  Full attempt and wrapper/logs collected; ACCOUNTING_696067.json and the
  33-file RESULT_MANIFEST_SHARED_BUDGET.json preserve evidence. No active EGG job.
  Do not repeat this attempt. Hourly automation remains ACTIVE.
- Both 30-second covers returned new five-bus plans: learned target cost
  689.100163, cost-only 691.228570. Both are time-limit incumbents with cover
  gap about 0.20; no minimum-bus claim. Fresh best target lower 597.829694;
  new saved physical hull column 685.695043 slightly improves archived retained
  685.788696. Independent replay and complete report are being finalized.
- Root manages this turn: energy_diagnosis writes independent two-candidate
  and shared-row/bound review; Luna writes two-cell CSV/results; Sol implements
  a new two-group development expansion. Avoid concurrent edits to their files.
- Approved prospective profile: independent seeds 2018 (20 services) and 2019
  (28 services), no refit of frozen stage-2 EdgePrior, reserved 2004/2005 untouched.
  Four source cells first, frozen-model inference before any target solve.
  Each group: source0/source1; cold/retained/nearest-price/cheapest-bill/learned
  target arms; cost-only/learned shared-interval repairs at 30 seconds: 18 cells.
  Native 70 solver/100 hard, repair 240 hard, inference 45 hard; controller
  3000, shell 3300, Slurm 3600 seconds, one CPU/8GB/thread, no retry/requeue,
  exclude scaglione-compute-01. No launch until code/protocol/tests reviewed
  and execution commit pushed. Do not broaden sweep or tune previous outcomes.
- Next: finish current evidence review, back up and update original Google Doc;
  review and launch the independent-group runner once. Read newer state and
  active workers first. Old source-market bounds cannot be used as target bounds.

## Prior checkpoint — targeted 28-service cover budget study launched

- **Recorded EGG job696067**, submitted2026-09-30T10:52:23Z. Single scoped startup
  check observed PENDING, requesting1CPU/8GB. No result inspected. Do not duplicate.
  Existing hourly automation stays ACTIVE.
- Execution commit `3e32d3189fa42ac971c6ee0319bfb54555072f2e`, remote checkout
  `/home/nc437/egg-shared-budget-repair-20260930`, exclusive attempt
  `result/learning_repair/20260930-shared-budget-attempt1`. LAUNCH_696067.json,
  PROTOCOL_SHARED_BUDGET_REPAIR.md and SHARED_BUDGET_LAUNCH_REVIEW.md authoritative.
- Only2017/28service learned then cost_only run, with cover30sec instead of5.
  Model/case/market/objectives/constraints unchanged; no refit/test access. Other
  limits stay charge45phase/55wall,hull70wall,child240,controller1500,shell1650;
  oneCPU/8GB/30min/one native thread,no retry/requeue,exclude01. This is a separate
  prospective budget comparison justified by prior no-incumbent outcomes.
- Sol final aggregate42tests+8subtests,wrapper/design/54sourcepins/diff checks
  pass. Root reviewed subset guards, cap propagation/receipts and resource budget.
  Historical4cell/5sec profiles preserved. No local GRB/full development solve.
- Completed695461 in171sec:2016only and learned new4bus repairs522.792412 and
  516.926077. Direct source baseline553.474774; historical target-verified
  control515.515556 remains cheaper. Both2017 cover solves hit5sec without
  integral incumbent, so sourcefallback724.660042; no infeasibility conclusion.
- Fresh independent replay/hash/exact-cost checks pass all4; positive shared
  charge witnesses of two2016 covers satisfy rows within4e-13kWh. Learned hull
  bounds515.356816–515.471130 (upper mixture, not physical). Compatible historical
  physical control gives physical enclosure515.356816–515.515556, still open.
  No general ML benefit or speedup. Full evidence/script backed up in3e32d31.
- Saved-column review replays10new and5archived2016 plans. Best new515.648054
  does not improve on archived515.515556. At that archived incumbent's own-load
  gradient prices, another replayed4bus plan witnesses regret>=0.724020 while its
  true target cost is higher516.505682. Incumbent gap<=0.158740 from freshlower.
  This supports an incentive mismatch at this near-optimal incumbent, not the
  unknown true optimum. SHARED_INTERVAL_PHYSICAL_POOL_REVIEW.json/.md and its
  reproducibility script retain exact arithmetic/provenance. Scope15plans only.
- Consolidated report and verified schedule figure are complete and backed up in
  `8e17264ffc71eb9b5ed0851b429d5d3927f43ac8`. The original Google Doc now includes
  the results, incentive witness and actual fleet figure; text, heading, link and
  all three inline figures verified. DOC_SHARED_INTERVAL_RESULTS_RECEIPT.json
  records the append. All three workers finished; no edits pending. No second
  cluster check or additional submission this turn; job696067 remains recorded
  as last observed PENDING, not rechecked. Read newer state/workers next turn.
- Next: one scoped check of696067; use scoped sacct/receipts if vanished, collect
  complete attempt/native logs/wrapper. Summarize with existing summarizer into
  SHARED_BUDGET_REPAIR_CELLS.csv; the attempt has2cells, read frozen design.
  Independently replay candidates/fallbacks, assess full repair+verification time
  and open bounds. Select next step from evidence, with no automatic budget
  escalation, duplicate, extra-bus repair or refit to these development cases.
  Reserved2004/2005,protected outcomes/privateGIRO/PRmerge/submission untouched.

## Prior checkpoint — shared-interval results collected; targeted budget study in preparation

- Job695461 COMPLETED exit0 in171seconds,1CPU/8GB,MaxRSS205836KiB on
  snavely-cpu-04. Full artifacts/logs/receipt collected,55 file hashes preserved
  in RESULT_MANIFEST_SHARED_INTERVAL.json; ACCOUNTING_695461.json authoritative.
  No EGG job active. Do not repeat this attempt. Automation remains ACTIVE.
-2016 both arms yield new replayed4bus fleets: cost_only522.792412, learned
  516.926077; historical target-verified control515.515556 remains better. Learned
  hull lower515.356816, mixture upper515.471130; open gap. These are preliminary
  until independent verification/report completes.2017 both cover solves hit5s
  with no integral incumbent, so source fallback724.660042, no newhull or
  infeasibility conclusion.
- Root managing one targeted next package: sol6_campaign_runner implements
  2017-only two-arm30sec cover study with all other budgets unchanged and an
  explicit frozen profile; energy_diagnosis independently replays4outcomes and
  positive charge witnesses; Luna prepares concise report and actual2016 learned
  schedule/charging plot. No launch approved or recorded yet. Check active workers.
- Prospective outer budget stays1CPU/8GB/30min/one native thread/no retry/exclude01;
  no refit, protected outcomes or reserved-test access. New30sec cover is a
  separately recorded budget experiment justified by no-incumbent5sec results,
  not an automatic retry. Review source/protocol before root-only submission.

## Prior checkpoint — shared-interval repair pilot launched

- **Recorded EGG job695461**, submitted2026-09-30T10:00:53Z; one scoped startup
  check observed PENDING, requesting1CPU/8GB. No result inspected. Do not duplicate
  this attempt. Existing hourly automation remains ACTIVE.
- Execution commit `96ac96da5250d1b44b3a19aae5a066ee2fdc748c`, remote checkout
  `/home/nc437/egg-shared-interval-repair-20260930`, exclusive attempt
  `result/learning_repair/20260930-shared-interval-attempt1`. LAUNCH_695461.json,
  PROTOCOL_SHARED_INTERVAL_REPAIR.md and SHARED_INTERVAL_LAUNCH_REVIEW.md under
  research-20260930/learning-campaign are authoritative. Source backed up to GitHub.
- New screen includes continuous grid energy per eligible visit/compiled interval,
  linked to selected movements, shared interval capacity, depot SOC and terminal
  refill equalities. Positive charge allocations are saved for diagnosis. Full
  native charging and physical replay remain mandatory. This approaches a coupled
  fleet MILP; a5sec failure to find a useful incumbent is not method inferiority.
- Same4 crossed development cells, frozen stage2 model, no refit/test access.
  Costs, open gaps, failures, repair/verification time and fallback provenance are
  separate. Fallbacks skip redundant hulls; new physical plans get fresh hull checks.
  Budget1CPU/8GB/30min/one native thread/no retry/exclude01; cover5sec,
  charge45phase/55wall, hull70wall, child240, controller1500, shell1650.
- Sol aggregate38tests+6subtests, wrapper/design/48sourcepins and diff checks
  passed. Final charge-witness addition passed2focused tests. Root reviewed units,
  selected/unselected implications, refill and physical source witnesses. No local
  GRB or full development fleet optimization was run.
- Completed691594:109sec, one new2017 learned8bus plan at980.998586; worse than
  source724.660042 and archived target-verified689.474312. Three charging failures
  used source fallbacks. Independent replay exactly matches all4 saved outcomes.
  No learned advantage or speedup. Evidence/diagnosis backed up in7a58914.
- Fixed-cover LP isolation: all4 feasible with independent visit capacities;
  shared interval sums make precisely the3 native failures infeasible. Diagnostic
  extra grid energy5.189/1.922/70.822kWh (2016only/learned,2017only). Numerical
  findings, not exact or global infeasibility proofs. See CHARGING_CAP_FAILURE_DIAGNOSIS.
- Compatible cost-aware/charging-cap receipts combine to CH approximately
  [588.165909,686.653533] and physical optimum[588.165909,689.474312]; both open.
  New lower588.165909 beats prior579.538921, but its mixture upper688.761949
  is weaker than prior686.653533. Do not treat a mixture upper as physical.
  BOUNDS_CHARGING_CAP_COMPARISON.json stores exact endpoints/domain IDs/hashes;
  scope is these compared runs, not a claim of strongest bounds over all history.
- Google Doc verified consolidated results/diagnosis append; previous history and
  both figures preserved. DOC_CHARGING_CAP_RESULTS_RECEIPT.json records the check.
- Next: one scoped queue check of695461, scoped sacct/receipts if vanished. Collect
  complete attempt/native logs/wrapper receipt. Summarize with existing
  summarize_cost_aware_repair.py using the shared-interval attempt and output
  SHARED_INTERVAL_REPAIR_CELLS.csv. Independently replay new candidates/fallbacks,
  assess physical cost and repair/verification work. Use saved positive charge
  witness if native charging disagrees. Diagnose before choosing the next bounded
  protocol; no automatic repeat, extra-bus repair or refit to these2development cases.
  All implementation workers finished; inspect active/newer state before action.
  Reserved2004/2005, protected outcomes/privateGIRO/PRmerge/submission untouched.

## Prior checkpoint — charging-cap result collected; shared capacity diagnosis underway

- Job691594 COMPLETED exit0 in109seconds, one allocated CPU/8GB, MaxRSS230152KiB,
  snavely-cpu-04. Complete attempt and native logs collected; ACCOUNTING_691594.json
  and RESULT_MANIFEST_CHARGING_CAP.json preserve accounting and57 artifact hashes.
  No EGG job is active. Do not repeat this attempt; automation remains ACTIVE.
- One new physical plan:2017 learned8bus, exact target cost980.998586. This is
  worse than the historical target-verified control689.474312 and source724.660042.
  It arose from a5sec cover timeout with0.5003 gap. The other3 proposals failed
  fixed-route charging and replayed source fallbacks. Fresh hull for the new plan
  remained open at588.165909–688.761949; upper is a mixture, not a physical plan.
- Root manages review: energy_diagnosis independently replays all4 saved outcomes
  and diagnoses shared-capacity failure; luna_campaign_review prepares the report;
  sol6_campaign_runner prepares a conditional shared-interval harness/protocol.
  No new source approved or launch recorded yet. Inspect worker/newer state first.
- Next bounded ceiling stays1CPU/8GB/30min/one native thread/no retry/exclude01.
  Shared-charging work is conditional on verified diagnosis; no refit/test access.
  Do not claim learning benefit, speedup or optimality from the sole8bus candidate.

## Prior checkpoint — charging-cap repair pilot launched

- **Recorded EGG job 691594**, submitted 2026-09-30T08:55:45Z. One scoped
  startup check observed PENDING, requesting one CPU/8GB. No result inspected.
  Do not duplicate this attempt. Existing hourly automation remains ACTIVE.
- Execution commit `77122c800bbc04fec35dffd43a1f4030bf1699b1`, remote checkout
  `/home/nc437/egg-charging-cap-repair-20260930`, exclusive attempt
  `result/learning_repair/20260930-charging-cap-attempt1`. Authoritative receipts:
  LAUNCH_691594.json, PROTOCOL_CHARGING_CAP_REPAIR.md and
  CHARGING_CAP_LAUNCH_REVIEW.md under research-20260930/learning-campaign.
- Completed energy-aware job 688750 produced no feasible new repaired fleet:
  all four optimal energy-relaxed covers failed native charging. Independent
  arithmetic now identifies insufficient individual charging windows in 12/14
  selected routes, across all four fleets. It grants each bus exclusive charging,
  so shared congestion is unnecessary to explain these selected failures. This
  does not rule out every 3/4-bus fleet. See CHARGING_WINDOW_DIAGNOSIS.md/.json
  and RESULTS_ENERGY_AWARE_REPAIR.md. Full evidence backed up in 535fc36.
- New cap-aware screen adds maximum depot energy gains from actual compiled
  charging windows and terminal refill capacity. These are necessary bounds;
  shared charging competition remains omitted. Native fixed-route charging and
  independent replay decide feasibility. No new charging-cap result claimed yet.
- Same four crossed development cells and frozen stage2 model; no refit or
  reserved test access. Compare cost_only/cost_learned separately. Failed repairs
  preserve failures/time and replay the archived fallback without redundant
  hull solving; new feasible repairs receive fresh bounded hull verification.
- Resource budget: one CPU/8GB/30min/one native thread, no retry/requeue,
  exclude scaglione-compute-01. Cover5sec, charge45phase/55wall, hull70wall,
  child240, controller1500, shell1650. Root reviewed inequalities/profile/budget;
  Sol aggregate checks passed 33 tests+4subtests, diagnosis/design/39sourcepins,
  wrapper syntax and diff checks. No local GRB fleet optimization ran.
- Google Doc has the verified charging-window diagnosis/results append and
  immutable evidence link. History and two existing inline figures preserved.
  Receipt: DOC_ENERGY_AWARE_RESULTS_RECEIPT.json. No new failure figure added.
- Next: make one scoped check of691594; use scoped sacct/receipts if vanished.
  Collect the complete attempt, native stdout/stderr and wrapper receipt.
  Summarize with `python3 research-20260930/learning-campaign/summarize_cost_aware_repair.py
  --attempt result/learning_repair/20260930-charging-cap-attempt1
  --output research-20260930/learning-campaign/CHARGING_CAP_REPAIR_CELLS.csv`
  (one shell line). Replay new candidates and fallbacks, retain all costs/bounds/
  status/time, and choose the next bounded step from evidence. Do not refit merely
  to these two development cases. All workers finished; check newer state before
  acting. Reserved2004/2005, protected outcomes and privateGIRO remain untouched.

## Prior checkpoint — energy-aware pilot completed; charging limits under diagnosis

- Job **688750 completed**, exit 0 in 35 seconds on snavely-cpu-04,
  one allocated CPU, 8 GB, MaxRSS 116972 KiB. No EGG job is active.
  Full attempt collected at `result/learning_repair/20260930-energy-aware-attempt1`.
  ACCOUNTING_688750.json and RESULT_MANIFEST_ENERGY_AWARE.json preserve all
  receipts, failure evidence, timing and log hashes. Do not repeat this attempt.
- All four energy-relaxed covers were HiGHS OPTIMAL at 3/4 buses, but full
  fixed-route charging returned INFEASIBLE for every cover. No new repaired
  fleet. All source fallbacks freshly replayed with exact costs 553.47/724.66;
  no fresh hulls or bounds (correctly skipped). See RESULTS_ENERGY_AWARE_REPAIR.md,
  ENERGY_AWARE_REPAIR_CELLS.csv and INDEPENDENT_REPLAY_ENERGY_AWARE.json.
- Root manages one next bounded package, pending pure arithmetic diagnosis of
  actual charging-window energy caps and cumulative route deficits. Sol
  energy_diagnosis owns this analysis; Sol campaign_runner is preparing minimal
  harness reuse; Luna has finished the compact results report. Check active
  workers and newer state before edits/submission. Root alone submits after a
  prospective protocol and reviewed source. No refit or test access.
- Initial next ceiling remains one CPU/8GB/one native thread/at most 30 minutes,
  no retry/requeue, exclude scaglione-compute-01. No new launch is recorded yet.
  Keep the existing hourly automation ACTIVE under the user's current request.

## Prior checkpoint — energy-aware four-cell pilot launched

- **Recorded EGG job688750**, submitted2026-09-30T08:02:39Z; one initial
  scoped queue check observed RUNNING, one allocated CPU/8GB on snavely-cpu-04.
  No result inspected yet. Do not duplicate this attempt. Heartbeat remains ACTIVE.
- Execution commit`f45c5a99850266831c0cd257d2117226c33644e4`, remote checkout
  `/home/nc437/egg-energy-aware-repair-20260930`, exclusive attempt
  `result/learning_repair/20260930-energy-aware-attempt1`. LAUNCH_688750.json,
  PROTOCOL_ENERGY_AWARE_REPAIR.md and ENERGY_AWARE_LAUNCH_REVIEW.md under
  research-20260930/learning-campaign are authoritative. Source is on GitHub.
- Four crossed cells:2016/cost_only,2016/cost_learned,2017/cost_learned,
  2017/cost_only. Same development cases and frozen stage2 model; no refit or
  reserved test access. Cost-only receives no model. A necessary post-trip SOC
  relaxation screens route covers, allowing optimistic full reset only where
  positive charging capacity exists. It ignores capacity size/competition and
  terminal full refill. Passing it is not physical feasibility or optimality.
- Full fixed-route linear-tariff GRB charging and independent physical replay
  still follow. New repaired plans get fresh target-hull checks. Failed repairs
  preserve evidence/time and replay the historical source fallback; they skip
  another redundant hull solve and claim no fresh bounds. Historical runner
  defaults unchanged. Report direct proposals, repair, fallback and hull separately.
- Budget:1CPU/8GB/30min/one native thread, no retry/requeue, exclude01.
  Cover5sec, charge45phase/55wall, hull70wall, child240, controller1500,
  shell1650. Root/ Sol implementation and Luna review found no launch blocker;
  27 focused tests+2subtests passed, including small HiGHS fixtures and archived
  physical SOC witnesses. No local GRB fleet optimization ran.
- Completed job685697: all four minimum-structural-bus covers failed charging.
  Independent route arithmetic rejects14/14 proposed routes: uncharged stretches
  exceed80kWh usable battery (91.33–241.63kWh longest stretches). This does not
  rule out other3/4bus fleets. All cells fell back to existing4/5bus source plans
  at553.47/724.66; fresh physical replay passed. No learned benefit or speedup.
  Full results/failures/time/figure backed up in7a35971 and later clarification.
- Google Doc has verified consolidated results plus the new14-route energy
  figure, preserving prior history/figure. Receipt:DOC_COST_AWARE_RESULTS_RECEIPT.json.
  Source PNG visually checked; native placement verified, full Doc pagination not.
- Next: one scoped check of688750, collect full artifacts and wrapper accounting.
  Run `python3 research-20260930/learning-campaign/summarize_cost_aware_repair.py
  --attempt result/learning_repair/20260930-energy-aware-attempt1
  --output research-20260930/learning-campaign/ENERGY_AWARE_REPAIR_CELLS.csv`
  (one shell line). Review new candidates with fresh physical replay, report all
  failures/skipped hulls/timing, compare feasible costs against frozen sources and
  each other. Then choose the next bounded step from evidence, without repeating
  the same failed covers or refitting to these two development cases.
- All workers finished; check newer state/active workers before acting. No
  protected outcomes, reserved2004/2005, privateGIRO, PRmerge or submission.

## Prior checkpoint — cost-aware failure diagnosed; energy-aware cover in implementation

- Job **685697 completed**, exit0 in4:43 on snavely-cpu-04, one allocated CPU,
  8GB, MaxRSS229396KiB. Full attempt collected at
  `result/learning_repair/20260930-cost-aware-attempt1`; accounting, manifest,
  four-cell CSV and RESULTS_COST_AWARE_REPAIR.md are under
  research-20260930/learning-campaign. Do not repeat this attempt.
- All four covers achieved native optimal structural bus counts (3/4), but
  every fixed-route charging LP reported INFEASIBLE. All four cells used the
  archived source0 fallback. Root freshly replayed and exactly rescored each
  saved fallback: 4buses/553.47 for2016 and5buses/724.66 for2017. No learned
  benefit, new feasible repaired plan or speedup. Hull checks stayed open.
- Necessary energy diagnosis: each selected vehicle route has a segment without
  charging whose drain exceeds usable battery80kWh. This rejects these covers;
  it does not prove 3/4buses impossible in the full physical model.
- No EGG job currently active. Root manages the next concrete four-cell
  development package: optional necessary SOC relaxation in the route-cover
  MILP, allowing optimistic full reset at a positive declared depot charging
  opportunity, then unchanged full charging LP/replay/fallback/hull checking.
  Sol energy_diagnosis owns module/tests and diagnosis; Sol campaign_runner owns
  harness/protocol; Luna result report and subsequent review. Check active
  workers/newer state before edits. Root alone submits after review/freeze.
- Prospective initial next ceiling is unchanged:1CPU/8GB/30min, one native
  thread, no retry/requeue, exclude scaglione-compute-01; no refit/test access.
  Do not launch until final PROTOCOL_ENERGY_AWARE_REPAIR.md and source reviewed.
  Existing ACTIVE hourly heartbeat continues. Meaningful findings only.
- Prior source remains682a860; raw logs (including native diagnostics) retained
  locally/remotely and hashed. Reserved2004/2005 and protected outcomes untouched.

## Prior checkpoint — cost-aware four-cell experiment submitted

- **Recorded EGG job: 685697**, submitted at 2026-09-30T06:52:37Z. Initial
  scoped queue check was PENDING; later scoped accounting confirmed PENDING,
  zero allocated CPUs and no execution artifacts (PENDING_685697.json).
  No result is available at this checkpoint.
  Do not submit another job or repeat this attempt. The heartbeat stays ACTIVE.
- Pinned execution commit `682a8604a93804a74bc54666cbe1f626e5c9c788`, remote
  checkout `/home/nc437/egg-cost-aware-repair-20260930`, attempt
  `result/learning_repair/20260930-cost-aware-attempt1`. See LAUNCH_685697.json,
  PROTOCOL_COST_AWARE_REPAIR.md and COST_AWARE_REPAIR_LAUNCH_REVIEW.md under
  research-20260930/learning-campaign. The source/protocol is backed up on GitHub.
- Four serial cells: 2016/cost_only, 2016/cost_learned,
  2017/cost_learned, 2017/cost_only. Only frozen stage2 development cases and
  model are used; no refit or test access. The unlearned arm passes no model to
  repair and performs no inference. Both cost modes minimize structural pullout
  count; the learned score perturbation cannot compensate for one extra bus at
  an exact optimum. Positive vehicle cost and zero deadhead cost are required.
- This does not minimize the whole nonlinear supply bill or certify physical
  minimum fleet size. Native cover status/gap, charging feasibility and physical
  replay remain separate. Charging is still an LP under the linear tariff;
  full nonlinear cost is computed after replay. Failed repairs retain evidence
  and use the pre-target source fallback, followed by fresh target hull checking.
  No second cover, extra bus, hidden cold solve or retry is used for a failure.
- Requested resource budget: one CPU/8GB/one native thread/30 minutes,
  no requeue, exclude scaglione-compute-01. Cover5 seconds, charging55 wall/45
  solve, target hull 70, child 240, controller 1500, shell 1650 seconds. Report actual
  allocation separately after start/completion. Do not alter other projects.
- Root and Luna reviewed the math and launch delta; 18 focused tests passed.
  The historical repair runner now uses a shared explicit per-cell evaluator;
  its historical attempt remains untouched. A Sol capacity error was handled
  by root finishing the small module delta; it did not block the launch.
- Original Google Doc has a verified append explaining the comparison and
  linking the prospective protocol (DOC_COST_AWARE_LAUNCH_RECEIPT.json).
  No new native result, learning benefit or runtime improvement is claimed.
- Next: collect complete receipts for job685697, preserve failed/missing cells
  and all spent time, compare structural bus count, repaired feasibility, direct
  candidate cost, source-fallback cost and separate hull work. Luna completed
  summarize_cost_aware_repair.py to produce COST_AWARE_REPAIR_CELLS.csv; run it
  after collecting the attempt. It keeps all four rows and gates candidate cost
  on saved independent replay. All workers have finished this package. Check
  newer state before acting; independently replay new candidates,
  write RESULTS_COST_AWARE_REPAIR.md, make a useful comparison visual if supported,
  then append the consolidated result to the Doc and back up all evidence.
- Previous results remain in RESULTS_STAGE2.md and RESULTS_REPAIR.md. Reserved
  seeds 2004/2005 and protected A6/B3/confirmation outcomes remain untouched. No
  private GIRO publication, PR merge, journal submission or reset-credit use.

## Prior checkpoint — route repair works, but uses too many buses

- **No EGG job is currently active. Do not pause the heartbeat.** Both newly
  analyzed batches are complete; the next justified package is a cost-aware
  route-cover decoder with a cost-only (unlearned) ablation on the same frozen
  development cases. Implement and review its prospective protocol before one
  serial launch; do not retrain or expand the sweep to hide the present result.
- **Job 682689 completed**, exit 0 in 2:28 on snavely-cpu-04, one allocated CPU,
  8 GB, MaxRSS 214948 KiB. Frozen execution commit
  `d731a416c1ac560a840869000e8f51248643a8f0`; remote checkout
  `/home/nc437/egg-route-repair-20260930`. Complete attempt is downloaded at
  `result/learning_repair/20260930-attempt1`. See LAUNCH_682689.json,
  ACCOUNTING_682689.json, RESULT_MANIFEST_REPAIR.json, PROTOCOL_REPAIR.md and
  RESULTS_REPAIR.md under research-20260930/learning-campaign. Do not resubmit.
- The new decoder produced legal routes and the fixed-route charging LP yielded
  replayed feasible fleets in both cases, with repair routines taking 1.01 and
  1.40 seconds. However, it used **18 and 28 buses**, versus **4 and 5** in the
  cheapest archived source fleets. Direct costs were **1919.93 and 2999.52**,
  versus **553.47 and 724.66** for those sources. The score-only route objective
  omits fleet cost. Charging feasibility works; proposal quality is poor.
- Separate global hull checks took 60.75 and 61.30 seconds and remained
  budget-exhausted. Both lower and mixture certificates replayed. No fallback
  was used; the fallback branch has unit/replay checks, not a native failure
  demonstration. No speedup, learning benefit or physical optimum is established.
- Next correction: account for bus cost while decoding routes, and compare a
  matched cost-only decoder to the learned-score variant. Keep charging repair,
  physical replay and target hull checking separate, with all failure/time
  receipts. The current LP optimizes the linear tariff and then scores the full
  nonlinear bill; it is not a fixed-route quadratic optimizer. Keep that limit
  explicit. Use only dev2016/2017 and the frozen stage2 model initially.
- **Stage2 job 678708 is also complete**, 44/44 replayed feasible fleets in 38:05;
  5 hull results certified, 37 budget-exhausted, 2 stalled-bounded. All physical
  labels remain provisional. The model trained on 18 labels from six groups in
  14.97 seconds (outer receipt). Learned, nearest-price and cheapest selection
  chose the same source in both development cases; all ten dev hull arms remained
  open. Source acquisition cost 124.82/128.72 seconds. See RESULTS_STAGE2.md,
  RESULTS_STAGE2_CELLS.csv and stage2_development_bounds.png. Both stages and
  all raw evidence are retained; native license stdout is hashed but not public.
- The original Google Doc has a verified appended stage2 result/launch section
  and the objective-bound figure (DOC_STAGE2_REPAIR_LAUNCH_RECEIPT.json).
  The independently replayed repair result is also appended and linked
  (DOC_REPAIR_RESULTS_RECEIPT.json). Both result packages are backed up on the
  existing research branch; the evidence commit is f498e28.
  The existing hourly automation is ACTIVE. No user approval is needed for the
  routine next package; notify substantive results or genuine decisions only.
- Preserve reserved test seeds2004/2005, no protected A6/B3/confirmation data,
  no private GIRO publication, PR merge, journal submission or reset-credit use.
  Initial resource ceiling stays one requested CPU/8GB/one native thread/<=2h,
  no retry/requeue and exclude scaglione-compute-01. The completed repair pilot
  used a tighter30-minute allocation. Check active workers/newer state first.

## Prior checkpoint — larger batch complete; route repair under implementation

- **Completed job 678708**, execution commit `822be2c7bdc2bef9ab6364c2e97d9747c048898b`,
  finished with exit 0 in 38:05 on snavely-cpu-04. All 44 cells have feasible
  fleet labels; no child exception files. The trainer completed in 14.97 seconds.
  Actual allocation: one CPU, 8 GB, batch MaxRSS 258724 KiB. Full artifacts are
  downloaded locally and retained at `/home/nc437/egg-learning-stage2-20260930`.
  See ACCOUNTING_678708.json and RESULT_MANIFEST_STAGE2.json. Do not resubmit.
- Luna is analyzing stage2 quality/time comparisons. Sol proposal-learning and
  campaign-runner workers are implementing one bounded route-fixed charging
  repair pilot on development cases 2016/2017 using the frozen stage2 model.
  Root alone submits after their implementation, tests and prospective protocol.
  No EGG job is active at this checkpoint; keep the heartbeat active while this
  concrete next launch is being implemented. Inspect workers and newer state.
- The current attempt is `result/learning_campaign/20260930-stage2-attempt1`.
  See `research-20260930/learning-campaign/CAMPAIGN_STATE.json`,
  `LAUNCH_678708.json`, `PROTOCOL_STAGE2.md` and `STAGE2_LAUNCH_REVIEW.md`.
  Six training groups and two development groups have 12, 20 or 28 services.
  All development source cells precede one trainer call and both target cold
  solves. Seeds 2004/2005 remain unmaterialized. This is development, not testing.
- Budget: one requested CPU, 8 GB, one native thread, 100 minutes, no requeue,
  exclude scaglione-compute-01. Native cells get 70 seconds with a 100-second
  hard cap; trainer 45 seconds, controller 5400, shell 5550. Record actual allocation
  separately: the earlier job requested one CPU but Slurm allocated two logical
  CPUs. Do not alter other projects or held jobs. Root alone submits.
- **Completed pilot 677817** finished in 91 seconds (wrapper 85), exit 0. All 17
  cells yielded replayed feasible fleets; 15 hull results certified, two source
  runs stopped with nonclosing valid bounds. The CPU model trained successfully
  on six provisional fleet labels from two training timetables before the dev
  cold solve. Complete result copies are local and on its original cluster
  checkout `/home/nc437/egg-learning-campaign-20260930`, frozen at 79ad457.
  Full metadata, model and solver evidence are backed up on GitHub; native
  stdout/license diagnostics remain local/remote with hashes by repo convention.
- The first learned arm showed no benefit: target solve 3.08 s versus cold 2.88 s,
  all with the same hull bracket. Source acquisition cost 6.56 s. The 0.045 s online
  inference is contained in the 0.492 s trainer runtime (outer subprocess 1.023 s),
  not an additional disjoint cost. Learned picked the more expensive cached
  fleet; raw predicted edges did not form a valid path cover. See
  `RESULTS_STAGE1.md` and `MODEL_STAGE1.md`. Do not claim learning gains or
  physical optimality from a hull certificate alone.
- New code passed ten focused pilot tests, three stage2 tests and independent
  review. Two pilot review fixes were made before launch: full nonlinear
  cheapest-cost selection, and trusted bounds gated on saved replay flags.
  The larger batch uses a feasible-pool proposal, not a native MIP start.
- Original Google Doc received verified launch and result entries; receipts are
  `DOC_LAUNCH_RECEIPT.json` and `DOC_RESULTS_RECEIPT.json`. Coauthor draft 0.10
  remains historical; no new computational result has been inserted into it.

Next: finish compact stage2 analysis and the bounded repair pilot. Compare
cold/retained/nearest/cheapest/learned arms including acquisition, training,
prediction, replay and target verification. Do not refit on development outcomes.
Separate legal-route decoding, charging repair, physical replay and global hull
verification. Today's learned proposal is limited to its existing source pool;
repair should test whether a newly generated route can produce a feasible fleet.
Follow CONTINUATION_PLAN.md, preserve all failed attempts and spent time, and
back up meaningful milestones. Check newer workers/state first. No protected
A6/B3/confirmation outcomes, private GIRO publication, PR merge, journal
submission or reset-credit use.

## Prior checkpoint — draft 0.10 ready for coauthor discussion

- User's detailed review is incorporated with three scientific qualifications:
  the analytic dual run stops 1.21877605e-6 below CH (not within 1e-6); standard
  averaging citations do not directly cover its .5/sqrt(k) steps; and neither
  a universal Shapley–Folkman own-price-regret bound nor literal derivation of
  Alizadeh's network as a continuum limit is asserted.
- Same-model archived evidence confirms three column-generation pricing calls,
  including one initialization call, with a final hull interval about 1e-6 wide.
  Global/pool stopping tolerances were 1e-4/1e-6. Section 5.2 contrasts this
  computational method with 20,000 cheap analytic coordination calls; it is
  not a matched runtime experiment. No new solve was run or receipt changed.
- A new direct proof for the exact quadratic recurrence establishes convergence
  of step-weighted fleet cost/load to the unique hull optimizer. Projection is
  inactive from k=7; boundedness, telescoping updates and the norm identity allow
  the nonsquare-summable steps. Weighted one-bus frequency tends to 27/40, so both
  counts recur infinitely often in this specific iteration. The finite value
  stays .6603. Cite LPS1999 and Gustavsson et al.2015 as context; AW2009's checked
  primal claim is LP-specific. All details/access limits are in
  `research-20260929/review-response-v010/THEORY_AND_AVERAGING.md`.
- New Corollary 1: at a hull-optimal load, minimum marginal-price regret equals
  the physical plan's cost excess H(x). A restricted price set must contain an
  attained hull-dual price. The saved HiGHS endpoint (6,5,5) and the ramp example's
  minimum regret 3.5 are now explicit. Gross generation cost notation C_gen avoids
  reusing H. A two-row institution table separates Figures 1 and 4.
- Replication prose leads with gap/incentive decoupling and connects separately
  reserved pairs to divisible-flow coordination as an analogy. The revised
  abstract has 147 words. Sol independently verified the proof and corollary;
  Luna checked receipts/model identity and the targeted prose. The 23-page
  `output/pdf/egg-journal-v0.10-coauthor-draft.pdf` is built and visually checked.
  Release QA and the verified Google Doc append receipt accompany the review.
- This is a coauthor discussion draft, not a completed journal submission.
  The public-timetable support question and fleet-solver bottleneck remain open.
  No new cluster experiment or native implementation change; automation remains
  PAUSED. The next substantive computational choices remain the justified
  fleet-oracle formulation studies described in the preceding checkpoint.
  Do not restart idle checks or broaden a sweep just to keep research active.

## Prior checkpoint — hourly generation extension implemented; draft 0.9 ready

- The user recognizes Hreinsson et al. (2021) as the likely paper and authorized
  the hourly dispatch / dual decomposition / nonsmooth support extension. It is
  now implemented in draft 0.9, `output/pdf/egg-journal-v0.9-reviewed-draft.pdf`
  (21 pages). The earlier v0.8 and all prior PDFs remain preserved. Read the new
  Sections 3, 4.1 and 5 for this change; the public computations are unchanged.
- New `src/egglab/convex_dispatch.py` supplies a small linear-cost convex dispatch
  LP with capacities, initial outputs and hourly up/down ramps, balance prices,
  primal/dual checks and an optimal-price-face range diagnostic. Each LP requests
  one native thread and a ten-second limit. It is not wired into timetable MIPs.
- Exact three-consecutive-hour example: fleet load `(x,0,30-x)`, background
  `(0,15,0)`, two generators, both A up-ramps binding. Physical optimum 112,
  hull optimum 110.5, gap 1.5; hull price `(5.7,5,5)` and physical-optimum
  dispatch price `(6,5,5)` with regret 3. Mean-load price face `(s,5,5)`,
  `3<=s<=6`; best-price regret of the physical two-bus mean-load plan is 3.5.
  Relaxing only the two up-ramps gives physical=hull=104. Exact algebra,
  rational certificate, LP receipts and independent review are in
  `research-20260929/generation-dispatch-pilot/`. These are synthetic examples.
- Proposition 1 now handles subgradients and states dual attainment qualifications.
  Dual best-value convergence is distinguished from last-price convergence;
  positive gap excludes a balanced joint limit of exact fleet/supply responses,
  not all possible schedule convergence. The family's O(1) whole-operator
  incentive is not a universal Shapley–Folkman theorem. Hreinsson is cited for
  aggregation context; full theorem text was unavailable, so no constants or
  rates are borrowed. Source and independent theory checks are in
  `research-20260929/nonsmooth-coordination/`.
- An independent 20,000-call analytic replay logs current and best bounds
  separately: final current 94.830026914, best 94.887498781 versus exact 94.8875;
  38 switches in the last 60 responses. The supplied note had mixed diagnostics.
  This trace is not a timetable MIP experiment and establishes no speedup.
- Sol completed implementation and independent algebra/replay reviews; Luna
  completed primary-source attribution checks. Two focused tests and the
  Fraction certificate passed. The built PDF and all pages were visually
  checked. `RELEASE_QA.md` records scope and limitations. The initial two-period
  pilot omitted the middle hour and its JSON was overwritten; this failure is
  explicitly retained in `RUN_LOG.md`, not reconstructed or promoted as evidence.
- The original Google Doc received one consolidated v0.9 result entry and Saved
  to Drive was verified; see `nonsmooth-coordination/DOC_UPDATE_RECEIPT.json`.
  This is a meaningful GitHub backup milestone on the existing draft-PR branch.
- No EGG job is active or newly launched. The conditional automation remains
  PAUSED. Do not resume empty-queue polling. No native fleet code, protected
  outcomes or compute budgets were changed. Timetable-scale exact fleet pricing
  remains the bottleneck; dual coordination calls that oracle repeatedly.
- Next useful implementation is a same-model formulation study to improve the
  fleet oracle before scaling dispatch coordination. The cardinality/energy-row
  nonredundancy check and direct quadratic-planner comparison remain candidate
  approaches, not implemented launches. Keep network LMPs and generator UC
  separate until the single-node convex generation/fleet model has a useful
  computational baseline. Retrieval precedes learning, with independent tests
  still reserved. This release is ready for author review; the larger
  computational journal-paper objective remains incomplete.

## Prior checkpoint — generation-pricing literature assessed; no new launch

- User asked for a deeper search beyond Scaglione-authored papers and whether
  the methods fit EGG. The source trace and mathematical mapping are in
  `research-20260929/generation-pricing-literature/REVIEW.md`. Wang et al. (2013)
  EPSD Part I and Gribik–Hogan–Pope (2007) are closer recognition candidates;
  the specific paper sent to the user remains unidentified. A verified related
  Parvania–Khatami (2017) bibliography connects Scaglione's trajectory work to
  CHP references; do not misstate this as direct citation by the seed papers.
- Sol assessed the existing whole-fleet hull/Fenchel implementation and checked
  the proposed dispatch-LP dual and nonsmooth support diagnostic. A convex
  generation value function can replace quadratic supply, but requires reviewed
  domain, price-selection and dual-attainment assumptions. Several admissible
  prices require a support test over the price set. Generator UC hulls and the
  complete-fleet hull address different nonconvexities.
- The note proposes a same-model direct MIQP/MISOCP comparison with tangent
  planning, and separately a tiny convex-generator/ramp example. These are
  formulation recommendations, not implemented launches or measured speedups.
  The earlier cardinality/energy-row nonredundancy check remains a candidate.
  Current bottleneck/results remain as recorded below; v0.8 is unchanged.
- No EGG job is recorded active. Automation remains PAUSED; do not resume
  empty-queue checks. No solver, cluster launch, protected outcome or new compute
  budget was used for the literature assessment. The original Google Doc has
  a consolidated literature entry; see this package's documentation receipt.

## Latest experiment checkpoint — public sensitivity complete; idle monitoring paused

- Job 600028 completed successfully in 54 min 9 s (3249 s), exit 0:0,
  29 September 2026 02:12:17–03:06:26 UTC, on sonic-cpu-01, one CPU/8 GB.
  All 24 declared stages returned on time; there was no retry or requeue.
  No EGG experiment remains recorded active and no new launch is implemented.
  The existing `advance-egg-journal-research` automation was updated through
  the app tool to PAUSED at 03:18:59 UTC and its saved state was verified.
  Do not resume empty-queue polling or rerun preparation/submission helpers.
- All eight native physical-minus-hull intervals include zero, with upper
  endpoints about 106–282. Eight planners are bounded; eight cold hulls
  exhausted wall time at the pricing reserve; three own-price responses
  certified and five are bounded. This establishes neither a positive public
  gap nor its absence. The 204–563-unit regret belongs to named bounded planner
  incumbents and cannot establish lack of support at an optimal dispatch.
  The two depots and all economic variants are one development timetable.
- Complete curated results, outward-rounded table, PNG/SVG interval figure,
  diagnosis, 183-file raw manifest, frozen identities and receipts are in
  `research-20260929/public-economic-sensitivity/results-attempt1/`.
  Luna independently checked all manifest entries, 24 stages, eight identities,
  interval arithmetic and saved-price/regret lineage. The curator now verifies
  manifest coverage/bytes/hashes, retains paid receipt time even on rejected
  rows, and suppresses ideal upper claims without ideal witness verification.
  Its initial review and resolution are preserved. No raw event-log dump or
  new native qualification was performed.
- Sol diagnosed the limiting work: native MIP time is 1411.77 of 1469.95
  planner-child seconds. The hull made 24 total pricing/master calls; QP
  proposals total 6.29 s and exact replay 3.19 s, with zero pairwise polishing
  and rational sizes well below the cap. Other hull work includes global
  pricing, construction and validation but is not fully timed separately.
  Raising master or rational-size limits would miss these observed stops.
- Useful solver-free follow-up replayed saved individual pool fleets. Three
  guarded native physical uppers improve by about 9.88, 9.28 and 6.66 units;
  corresponding gap caps become 96.110615, 126.249088 and 258.333062, all still
  zero-compatible. `evaluate_pool.py` and `pool_candidates.json` record the
  column/witness identities and gates. Root inspected and independently reran
  this evaluation, obtaining a byte-identical receipt. These are separate
  post hoc native uppers, not ideal exact witnesses or convex hull mixtures.
  Original stage table/figure and original incumbent regrets remain unchanged.
- Paid child totals: planner 1469.95 s, hull 1402.01 s, response 357.64 s;
  supervisor 3233.90 s, wrapper 3247 s, Slurm 3249 s are nested clocks.
  All transports are recorded in COLLECTION_RECEIPT.json. Full raw archive
  stays outside Git in workspace-parent
  `research-20260929/cluster/public-economic-sensitivity-attempt1/`;
  archive SHA256 501818f182cbd3c1f037c49fd225505cf27ac4b14b6aafa77bca5c782cafe8d8.
  Keep remote `/home/nc437/egg-public-economic-20260929` frozen. Do not poll
  completed 600028/597526/595105 or retry retrieval 584876.
- Next useful research target, when work resumes, is a proof-driven check of
  whether the cardinality/energy inequality adds a nonredundant root-relaxation
  constraint beyond the existing aggregate energy-balance rows. Inspect the
  proof/model first; only a justified formulation should lead to a prospective
  native pilot. This is a recommendation, not a concrete implemented launch.
  Do not turn it into an automatic larger sweep or ML experiment. A separate
  route-fixed convex charging refinement is another possible upper-bound
  method, not something measured by the existing hull polish counter.
- Both result workers (Sol `sol6_integrate_theory`, Luna
  `luna_integrate_literature`) finished their assigned package. The old
  `sol6_cardinality_bound` pending-init entry is stale, not a running study.
  Execution-source CI36511357899 and backup b200445 CI36512241508 passed;
  do not repoll them. This result package is a new GitHub backup milestone.
- The original Google Doc received one consolidated result/bottleneck entry;
  Saved to Drive and a unique match after reload were verified. Local update
  and receipt accompany the result package. Reviewed v0.8 PDF remains unchanged
  and predates both the six economic examples and this public sensitivity.
  PR56 remains OPEN/draft; no merge or journal submission. The computational
  journal objective remains incomplete; scheduled idle checks are paused,
  not scientific work declared complete.

## Prior launch checkpoint — public sensitivity job 600028 running

- User monitoring preference updated after a scoped check at 02:17:42 UTC:
  job 600028 was RUNNING, elapsed 5:25, one stage receipt. The existing hourly
  heartbeat was updated in place and read back as ACTIVE; it must pause when
  no active experiment or concrete justified next launch remains. Results,
  decisions and review-ready artifacts are the only requested notifications.
  No routine cluster-status or test-passing messages. Scheduling intent is saved
  in the automation and this checkpoint; no duplicate automation was created.
- Sol worker `sol6_integrate_theory` is preparing local result curation only,
  owning `research-20260929/public-economic-sensitivity/summarize.py` and
  `RESULT_REVIEW_PLAN.md`. Check its state before any overlapping work; no new
  solve/submission authorized by that subtask. This prepares the eight-cell
  table with all missing/failed outcomes and separate native/analytical bounds.
- Job 600028 submitted once at 02:11:37 UTC on 29 September 2026. A compact
  check at 02:12:37 UTC found RUNNING, elapsed 20 s, on sonic-cpu-01, one CPU/8 GB.
  The eight-case/24-stage design is frozen. A receipt-only check at 02:15:48 UTC
  confirmed controller/supervisor startup: the first planner returned on time
  (183.736 s child wall, exit 0) and the first cold hull had launched. This is
  startup verification, not scientific result admission. No result claims yet. Do not duplicate
  submission, modify the execution checkout or poll completed jobs 597526/595105.
- Execution source 07b8ca94798b8872239113e00781ad81fde315d1 is published.
  Four focused pure tests passed independently by implementer and root; shell
  syntax, compile and deterministic source/design checks passed. Luna's bounded
  source review passed before submission, checking the exact runner/wrapper hashes;
  its final text was added after execution-source publication and is backed up
  with this launch receipt. Full source CI 36511357899 was in progress at launch and subsequently passed;
  do not poll it again. Backup 51a66b3 CI36511839207 was in progress at the
  monitoring-preference update. Earlier backup CI 36510140256
  was in progress when checked at turn start; source 41fa5f1 CI36508984595 passed.
- New driver/wrapper/tests are `src/experiments/public_economic_sensitivity.py`,
  `src/cluster/public_economic_sensitivity.sbatch`, and
  `src/tests/test_public_economic_sensitivity.py`. Protocol, implementation,
  validation and review: `research-20260929/public-economic-sensitivity/`.
  Launch receipt: `research-20260929/cluster/public-economic-600028.json`.
- Fixed order: (f, curvature multiplier) (100,1), (40,1), (20,1), (40,2),
  each with public depot 15 then 16. Intercept 0.20, base curvature 1/900.
  All are development variants of one 37-service Hildenbrand timetable.
  Each uses a fresh cost/market identity and fresh planner, cold QP hull and
  eligible own-price response. No old native bound/witness is imported; analytical
  availability/cardinality floors remain separate from solver bounds and cuts.
- Per cell: planner/hull 180 s wall, 160 s native; response 60/45 s;
  hard limits 210/210/90 s. Planner 16 rounds; hull 16 pricing/64 master calls,
  8192 bits, QP denominator 10^9/maxiter 500, reserve 10 s. Controller 5400 s,
  outer 5700 s, Slurm 100 min; one native thread/seed 0, no retry/requeue,
  exclude scaglione-compute-01. Keep every failed/incomplete/null outcome and
  every paid time; a skipped response remains a declared stage. No other
  projects or held jobs touched. No protected data, GIRO publication or ML.
- Remote checkout `/home/nc437/egg-public-economic-20260929` stays frozen.
  Attempt `result/public_economic_sensitivity/20260929-attempt1`; wrapper receipt
  is its sibling `.slurm_wrapper_receipt.json`, submission receipts in sibling
  `.launch/`; logs `egg-public-sensitivity-600028.out/.err`.
  Private local receipts (outside this worktree) are in workspace-parent
  `research-20260929/cluster/public-economic-sensitivity-attempt1/`.
  SSH preparation 18.630 s, submission 1.667 s, initial inspection 0.731 s
  are recorded separately; the receipt-only startup check cost 0.091 s SSH.
  Helpers `/private/tmp/egg_public_economic_remote.py`
  and `/private/tmp/egg_public_economic_inspect.py` are already spent; do not rerun.
- Next continuation: check newer state/active workers, one compact queue check
  for 600028 via unicorn2 after sourcing /etc/profile.d/slurm.sh. If vanished,
  use scoped sacct and saved receipts, collect all outcomes, and independently
  review the complete public cost/hull/incumbent-regret table before any new sweep.
  Do not treat a null gap as failure requiring a retry; diagnose the limiting
  stage/bounds. Retain D and CH native bounds separately from conditional uses
  of the ideal analytical floor. The 32–44 fee thresholds concern the bound,
  not a proved physical fleet crossover. No widening or ML launch while active.
- The original Google Doc has one consolidated launch entry; local text and
  save/reload receipt accompany this package. Manuscript v0.8 remains unchanged
  and readable; the six synthetic economic examples are in their separate result
  package below. PR 56 remains OPEN/draft. Hourly heartbeat remains active.

## Prior checkpoint — six economic examples complete; reviewed v0.8 ready

- No active EGG cluster jobs. Job 597526 completed in 176 seconds, exit 0:0,
  on sonic-cpu-01, 29 September 2026 01:41:15–01:44:11 UTC, one CPU/8 GB.
  All six planners and six own-price responses certified with complete on-time
  evidence. The completed QP hull bounds from job 595105 were imported, not rerun.
  Source 41fa5f1e23833922292e2f70e346f386485aaa51 passed CI 36508984595.
  Five focused pure tests, shell syntax and independent launch review passed.
- Flat-intercept cases with 8/16/24 services have native physical-minus-hull
  gap intervals approximately [0.005249,0.005328], [0.114493,0.114544] and
  [0.006730,0.006809]; named-incumbent regret is about 0.150/0.432/0.128.
  All three shifted-intercept gaps contain zero with upper endpoints about
  0.000002; regret is about 0.000001 or less. Both markets remain quadratic.
  Largest positive gap is below 0.03% of physical cost. Native solver/replay
  tolerances apply; one nested seed-1006 development family is not independent
  timetable evidence or an ideal-model exact proof. All positive and null results
  are retained. Every planner/response uses four buses; no hull fleet-size claim.
- Curated table, paired figure, summary-only curator, independent result review,
  raw summary/frozen identity, manifest and receipts are in
  `research-20260929/economic-support-diagnostic/results-attempt1/`.
  Luna verified all 97 manifest files, source identity and exact interval/regret
  arithmetic; Sol curated the interpretation and root checked the figure.
  Manifest describes the complete private raw tree, not the curated Git subset.
  Full archive remains outside this worktree in workspace-parent
  `research-20260929/cluster/economic-support-diagnostic-attempt1/`.
- Preserve all time: planners 133.29 s, responses 25.42 s, supervisor 161.58 s,
  wrapper 174 s (setup 10 s), Slurm 176 s are nested clocks, not additive.
  Imported hull job used 107 s separately. Preparation/submission/collection/
  accounting SSH times are in COLLECTION_RECEIPT.json. No retries or login-node
  optimization. Keep remote `/home/nc437/egg-economic-support-20260929` frozen;
  do not poll or resubmit 597526/595105 or retry retrieval 584876.
- Reviewed draft v0.8 merges both markets with the strongest public bounds,
  labels incumbent regret, adds exact undamped price cycle and posted-tariff
  institution, and restores three primary-source-checked references.
  `output/pdf/egg-journal-v0.8-reviewed-draft.pdf`: 17 pages, 3 figures, 2 tables,
  18 references; SHA 16afdc242f4007da8aa0a17e0a5e4904f8b2bb06caec53ec189bd89cf31d8db5.
  Root reviewed all page contact sheets and changed pages at full size. Cycle
  bills compare actual current loads: 147→134 and 194→167; 174 is a different
  two-bus charging optimum. Earlier PDFs remain preserved. Release/QA receipts:
  `research-20260929/review-response-v08/`. This PDF predates the new six-case
  results; do not silently claim they are already in this release.
- New reporting-only exact bound uses the union of ALL allowed charging visits.
  Six initial hourly energies are zero; first positive caps are 87/69 kWh,
  others 360. Four public floors improve to 429.22/430.29 (depot 15,
  original/changed) and 440.99/442.30 (depot 16), gains 4.86–12.03.
  Positive caps do not bind in these four bounds. Independent Sol window and
  closed-form review passed. Code/proof/values/review are in
  `research-20260929/charging-availability-bound/`. No native cut, solver status
  or historical evidence changed. The public positive-gap question remains open.
- Next bounded work package: implement and run the prospectively specified
  `research-20260929/economic-support-diagnostic/NEXT_PUBLIC_SENSITIVITY.md`.
  Two public depots × four bus-fee/curvature scenarios, keep f=100 control;
  one CPU/8 GB/100-minute ceiling, no retry, not yet submitted. Check active
  workers/newer receipts before acting. A 32–44 fee threshold is a dual-bound
  comparison, not a proved physical fleet crossover. Keep zero/unresolved gaps;
  do not search only for positives. This precedes a wider reuse/ML benchmark.
  Independent/protected test groups remain reserved; no protected data access,
  private GIRO publication, reset-credit redemption, merge or journal submission.
- Original Google Doc receives the v0.8/bound update and the independently
  reviewed experiment completion as distinct historical entries; save/reload
  receipts accompany each package. PR 56 remains OPEN/draft, unmerged.
  This package is complete after its GitHub backup. Next continuation checks
  that backup's CI once and advances the public study, not another audit.

## Prior checkpoint — QP master resolves six-cell arithmetic stops

- No active EGG jobs. Job595105 completed in1m47s, exit0:0, oneCPU/8GB on
  unicorn-cpu-87 at00:52:05–00:53:52 UTC29September2026. All six cells returned
  on time with complete native evidence. Do not poll or rerun595105/593482/591255.
  The short job was launched, completed and interpreted in this same session.
- QP certified6/6 versus native-LP3/6 on the SAME nested8/16/24-service seed1006
  development cells, two markets each. Flat-market QP native widths are at most
  0.000001/0.000003/0.000003; arithmetic maxima273/269/262bits versus
  LP8025/7978/8186. Existing QP master resolves the observed arithmetic stop under
  the unchanged16calls/8192bits/180scoordinator160sphase caps. All QP proposal
  non-success counts are zero. This does not establish ideal exact optima,
  physical D−CH gaps or price-support failure.
- Timing is mixed: flat16 child11.71→17.89s (4→10pricingcalls); flat24
  50.87→43.47s (5→6calls). Single sequential seed/one nested family, no general
  speedup. QP changes the price/column trajectory; route pricing is the largest
  measured component at16/24services. Native-LP master time is null/not applicable,
  not zero QP work. QP childsum91.62s, supervisor94.16s, wrapper102s and Slurm107s
  are nested clocks, not additive. Missing model-construction time stays unknown.
- Curated results/paired figure/summary-only curator/independent review and
  receipts: `research-20260929/qp-baseline-diagnostic/results-attempt1/`.
  Luna verified the49-file raw manifest and all six outcomes; Sol curated the
  paired table/figure and root visually checked it. Raw archive remains outside
  this git worktree under workspace-parent
  `research-20260929/cluster/qp-baseline-diagnostic-attempt1/`.
  Frozen identity summary omits bulky physical payloads, preserves raw hash;
  MANIFEST describes the complete private raw tree, not the curated subset.
- Source60a66e77be18e067aee4026f0e3a31dc120ec427 passedCI36504901386. The
  source/review/focused-check launch gate and earlier in-progress CI observation
  remain recorded honestly. Isolated remote checkout
  `/home/nc437/egg-qp-baseline-20260929` stays frozen. Launch receipt
  `research-20260929/cluster/qp-baseline-595105.json` now records completion.
  SSH preparation14.283s/submission0.871s/collection0.318s/accounting0.095s
  are preserved separately. No retries, login-node solves or other-project changes.
- Next bounded package: complete joint physical-planner D / CH / own-price-response
  regret evidence for these SAME six development cells, using the completed QP
  bounds for CH. Declare a separate prospective protocol and finite budget before
  launch; preserve incomplete planner bounds and name the incumbent whose regret
  is measured. Do not rerun CH solely to obtain new labels. This puts the paper's
  cost/incentive question ahead of another speed comparison. Then design matched
  cold/retained/nearest-neighbor evaluation using the viable QP baseline; ML waits.
  Independent test timetables stay reserved. No protected data or584876 retry;
  its pending one-replacement exception and frozen protocol are unchanged.
- One consolidated verified finding is appended to the original Google Doc;
  exact text and save/reload receipt accompany the result package. PR56 remains
  OPEN/draft, unmerged. No manuscript/PDF change; v0.7 remains current. Workers
  finished. Back up this meaningful milestone; next continuation checks only its
  newest CI once, then starts the economic-evidence package, not another audit.

## Prior checkpoint — six larger-case baseline runs completed and reviewed

- No active EGG jobs. Job593482 completed1m54s (exit0) on unicorn-cpu-87,
  oneCPU/8GB,00:30:04–00:31:58 UTC29September2026. Root caught completion,
  collected and reviewed all six outcomes in the launch session. Do not poll
  or resubmit593482/591255. No prior failed attempt was retried.
- Execution sourcee3ac75fc53c00594572126413b704ab1de42086e passed full hosted
  CI36503342208 after submission. Focused checks/independent review allowed
  launch while CI ran; solver/shared helpers were unchanged from601102a.
  Resultbackup8a278dd also passedCI36502491981. Remote execution checkout
  `/home/nc437/egg-cold-baseline-20260929` stays frozen, never pull/alter it.
- All six returned on time with complete native evidence: target prices
  certified in2/2/3pricingcalls for8/16/24services; all three flat source markets
  stopped on projected8192bit growth after3/4/5calls. Their native widths are
  at most0.347382/0.181109/0.053880cost units. Sixteen pricing calls did not bind.
  These are nested variants of seed1006, one development family and GRBseed0;
  no general speedup, independent-timetable result or ideal-model exact proof.
- At8/16services flat-market polishing exceeds recorded pricing; at24services
  pricing dominates (35.43s versus9.15s polishing). Arithmetic is a barrier to
  certification, not a universal runtime bottleneck. Missing model-construction
  time stays unknown. Retained/NN/ML benefit remains unestablished.
- Results/compact data and summary-only curator:
  `research-20260929/cold-baseline-viability/results-attempt1/`. Luna verified
  manifest/receipts/six assessments; Sol and root reviewed interpretation.
  Complete raw archive is outside git in workspace-parent
  `research-20260929/cluster/cold-baseline-viability-attempt1/`; all failures,
  stops and time preserved. Launch receipt `research-20260929/cluster/cold-baseline-593482.json`.
  Published identity summary omits reconstructed physical payloads; full frozen
  JSON remains in raw archive with its SHA. Wrapper112s/setup14s/supervisor96.61s
  and childsum94.05s are nested clocks, not additive. Preparation18.028s and
  submission0.579s SSH; result collection0.793s. No solver ran on login host.
- Next bounded computational package: separately freeze the SAME six cells with
  existing numerical-QP restricted-master proposal, changing only master policy
  and its declared existing controls (fixed denominator10^9/maxiterations500).
  Same16calls/8192bits/64master-pool/180scoordinator160sphase10sreserve,
  hardchild210s/controller1500s/outer1600s/Slurm30min1CPU8GB, no retry/requeue.
  Compare bound quality and all time, not one-run speedup. This tests the
  arithmetic barrier before a wider cold/retained/NN study. Do not inflate bits
  blindly or start ML. Old frozen retrieval584876/pending replacement unchanged.
- The user's idle-queue concern was addressed with concrete same-session work:
  previous591255 had finished51s; the new reviewed six-cell experiment was
  implemented, submitted, completed and interpreted. Short jobs must be followed
  in the same session where possible; hourly automation is fallback. No access
  or routine approval blocker. Do not fill the queue with arbitrary work.
- Original Google Doc launch and reviewed completion entries are both appended,
  Saved/reload-verified and found1of1, preserving history/visuals. Source/receipt
  files are in the package and result subfolder. PR56 is still OPEN/draft and
  describes both completed screens. No manuscript/PDF change; v0.7 remains
  current. Workers complete except stale pending cardinality agent (ignore).
  This package's receipt backup may have a new hosted CI; check it once next
  continuation. Next research package starts at the QP diagnosis above, not
  another audit of these completed jobs.

## Prior checkpoint — cold baseline limit diagnosis completed

- No active EGG job. Job591255 completed successfully (exit0) in51s on one
  CPU/8GB, 23:33:03–23:33:54 UTC,28 September2026. Source1dba007 and its
  remote checkout remain frozen. One scoped queue/accounting check found it
  finished; do not repoll or resubmit. Complete result archive is preserved
  privately under `research-20260928/cluster/budget-sizing-attempt1/` in the
  workspace parent, outside this git worktree. Curated results/receipts:
  `research-20260928/budget-sizing-diagnostic/results-attempt1/`.
- All eight cells returned on time with complete native evidence: three
  certified and five budget stops. Original market certifies in five pricing
  calls with either bit cap when sixteen calls are allowed. Changed market
  certifies in six calls at8192 bits;4096 bits stops it after three calls
  even with sixteen allowed. Four calls do not certify either market.
- This is controlled evidence for restrictive stopping limits on one development
  case/seed. It weakens the earlier tiny-case reuse advantage. No general
  speedup, public-case conclusion, learned benefit or ideal-model exact proof.
  Changed-market polishing took0.81s versus0.01s recorded native pricing;
  complete child3.70s. Keep component and whole-child times separate.
- Whole Slurm51s includes wrapper48s, setup17s and supervisor27.51s;
  child sum and measured components are nested, not additive. Preserve all
  five budget stops. Collection used4.730s SSH transport. Source/receipt CI
  passed:36498066050/36498838834. No new solver/source or manuscript change.
- User asked why idle. Explained the short job finished between hourly follow-ups;
  this was a follow-through delay, not cluster access or a permission gate.
  For future short jobs, collect completion in the same work session with
  bounded waits/checks; hourly automation is fallback, not a reason to leave
  a completed result unprocessed. Do not run arbitrary work just to fill the queue.
- Next bounded computational package: establish cold-baseline viability on the
  already generated larger 8/16/24-service development timetables with a new
  prospective source/design/resource freeze. Then compare cold/retained/nearest
  neighbor at common solution quality and paid source-plus-online cost. The
  tiny-case16-call/8192-bit result does not establish larger-case sufficiency.
  Diagnose the actually binding component; preserve all outcomes; no training.
- The old frozen retrieval attempt584876 and pending one-replacement exception
  are unchanged. Do not silently alter/retry it or use this diagnostic as a
  backdoor replacement. No protected/private cases or other-project resources.
- Sol completed the eight-row report, compact data, reproducible curator and
  SVG/PDF matrix; root inspected the rendered figure. Luna independently
  verified complete manifest/receipts/source pins and all eight assessments.
  Exactly three certifications/five budget stops; do not confuse the two
  relaxed-setting cells with the total number of certified cells.
- Original Google Doc appended once with “Cold solving succeeds when the
  stopping limits are relaxed — 28 September2026”, Saved and reload-verified;
  full opening sentence1of1, original heading intact, new heading last. Text
  and receipt are in the result package. v0.7 remains the author-review draft.
  No active workers except stale pending cardinality agent (ignore). This
  checkpoint/result package is being backed up on the existing research branch;
  check its newest hosted CI once on next continuation, without rerunning any
  experiment. The next six-cell design is prospective, not launched.

## Prior checkpoint — bounded cold-hull sizing diagnostic submitted

- Active EGG job591255, submitted once at23:32 UTC on28 September2026.
  The one launch queue observation was PENDING/Priority,1 CPU/8GB. Do not
  duplicate or poll old jobs. Receipt:
  `research-20260928/cluster/budget-sizing-591255.json`.
- Isolated execution checkout `/home/nc437/egg-budget-sizing-20260928`, source
  `1dba007ee4868f0d29373a84b7880171ab3c358c`, passed full CI36498066050.
  Leave this checkout unchanged. Attempt:
  `result/budget_sizing_diagnostic/20260928-attempt1`; runtime/design freeze
  occurs on its allocated compute node before any optimization. Sibling
  `.launch` holds the exclusive intent and submission receipt; sibling
  `.slurm_wrapper_receipt.json` records setup/freeze/preflight/run outcomes.

- New development diagnostic under `research-20260928/budget-sizing-diagnostic/`:
  eight independent cold cells on the existing three-service multivisit case,
  both markets, pricing calls4/16 crossed with arithmetic bits4096/8192. Native
  LP master and compact pricing stay fixed; master/pool64 provide common
  headroom. No retention, bound cache, starts or pricing reserve. Seed0, one
  native thread;60s coordinator/45s native phase,90s child hard limit plus
  termination grace,900s controller,1000s outer,20min Slurm,1 CPU/8GB.
- This separately recorded diagnostic follows the latest review discussion.
  It tests early stopping, not scalability, reuse speedup or learning. It does
  not rerun or change the failed frozen retrieval comparison or its pending
  replacement decision. All eight outcomes and all time must remain visible.
- New runner/batch/pure tests are isolated from the core solver. Root's three
  focused tests, shell syntax and diff checks pass; Sol reports20 focused plus
  adjacent checks during implementation. Luna's bounded review found no
  remaining launch blocker. Preparation used22.337s SSH wall without solving;
  submission used0.931s. Both transport receipts are preserved; these are not
  solver performance times. No core solver or manuscript/PDF change was made.
- Prior backupbef58e6 passed full CI36493009651. Its source-only predecessor
  CI36492634326 was superseded/cancelled, not a test failure. v0.7 remains the
  current author-review manuscript; this package makes no PDF change.
- Interpret call and bit contrasts within each market and report other binding
  limits as censoring. No assertion that sixteen calls suffices, and no automatic
  larger sweep. If arithmetic still binds, diagnose master/charging work before
  attributing benefit to route prediction. All cases remain development-only.
- Next follow-up: one scoped `squeue` check for591255 viaunicorn2 after sourcing
  `/etc/profile.d/slurm.sh`; if absent, scoped `sacct` and wrapper/supervisor
  receipts. Collect and interpret the eight-row result before any new run.
  No retry/requeue or wider sweep. The original Google Doc has one Saved and
  reload-verified append, “Testing the stopping limits — 28 September 2026”,
  with its opening phrase1of1, original heading intact and new heading last.
  Text/receipt are in this package. PR56 describes the new diagnostic and
  remains an unmerged draft. No active workers remain except stale pending
  cardinality agent (ignore). Check final receipt-backup CI once next follow-up;
  execution source1dba007 already passed and must not be changed on the cluster.

## Prior checkpoint — analytical baseline integrated into reporting

- Bounded package `research-20260928/analytic-baseline-integration/` implements
  the reviewed v0.7 public energy/cardinality floor as a pure module and opt-in
  `--analytic-energy-floor` appendix in the computational screen reporter.
  It checks complete physical-case identity, pinned proof lineage, supply-price
  conditions and all cardinalities. It covers only the two reviewed public
  cases and supported price-only changes; other cases remain unavailable.
- Exact ideal bounds remain separate from numerical solver evidence. Optional
  mixed intervals use native upper witnesses only, conditional on their ideal
  feasibility. Complete on-time stages and successful supervisor integrity are
  required; missing or incompatible evidence stays unavailable. Native lower
  bounds, statuses, timings, stage rows, CSV and default reports are unchanged.
  No coordinator, cache, pricing-cut or certification change was made.
- Sol implemented and Luna independently reviewed; root's final 10 focused
  tests pass, curated smoke reproduces byte-for-byte and all 32 native rows are
  unchanged. Four public floors reproduce the reviewed calculation. Outward
  conditional changed-market gap caps are 98.3611/117.6042, with zero lower
  endpoints; these do not prove a positive public gap or a speedup.
- No native optimization, new experiment, cluster call/allocation, protected or
  private data, manuscript/PDF revision, or ML training. No active EGG jobs.
  Previous receipt backup248f6b8 passed CI36490723183. Source backup
  `88daef8482aadd27bcf7605c4aced765fbffb205` is published. PR56 was updated and
  remains OPEN/draft, unmerged. Source CI36492634326 is still in progress at
  the final scoped check (setup/whitespace/shell checks passed).
- Original Google Doc update “Analytical benchmark integrated — 28 September
  2026” is appended once, Saved and reload-verified. Complete opening sentence
  appears1of1; original heading intact, new heading last, two source links.
  Text and receipt are `GOOGLE_DOC_UPDATE.md` and `GOOGLE_DOC_RECEIPT.md` in
  this package. No active workers remain except the stale pending cardinality
  agent (ignore). Check source/final receipt hosted CI once next continuation.
- Next bounded package: design a sizing diagnostic against the observed
  pricing-call/arithmetic stops before another comparison. Do not silently
  change the frozen four-call/4096-bit retrieval design, infer that sixteen
  calls would suffice, or launch the still-pending one-replacement exception.
  Do not re-ask that unanswered question. The v0.7 author-review draft remains
  current; computational scope, independent cases and equal-quality comparison
  remain unfinished. The wider research objective continues.

## Prior checkpoint — selective external-review revision 0.7

- User supplied Claude's review and authorized selected corrections. The review's
  strongest points are the missing analytic baseline, missing joint economic
  quantities, cap-dependent reuse claim and unconfirmed single-seed starts.
  We do not adopt a two-paper split, categorical rejection predictions, or the
  untested claim that sixteen pricing calls would certify the toy in seconds.
- Revised main draft `output/pdf/egg-journal-v0.7-reviewed-draft.pdf`: 17 pages,
  three figures, three tables, fifteen references, 150-word abstract. SHA-256
  `b02ed646e415686d74cd09f42d503e1dea46777cad93b9996628317113d4edea`.
  Seven-page historical development supplement:
  `output/pdf/egg-journal-v0.7-development-supplement.pdf`, SHA-256
  `dbb10babe6d291fae6e6555cd211b81334426b489aa659d6c3c20cd7031ce154`.
  The old computational chapter, figures, failures and spent time remain intact;
  main now inputs `computational_support.tex` and `joint_support_table.tex`.
- Sol reconstructed exact ideal energy floors for both matched depot cases:
  original/changed d15 424.365880667204 / 418.965880667204; d16
  435.674556453753 / 430.274556453753. The one-bus obstruction and positive
  three-plus-bus margins cover all cardinalities. The native-flat-derived
  423.27 proposal is not admitted as an exact ideal floor.
- Joint same-screen native D/CH/gap/incumbent-regret table includes all four
  changed-market cases. Existing response Fenchel evidence improves multivisit
  CH lower to84.622956 and gap upper to0.10 without another solve. Public
  incumbent regret is positive, but neither public optimality nor a positive
  public gap is proved. Conditional mixed exact-floor/native-upper gap caps
  are98.37/117.61; original-market exact d15 cap88.41 remains separate.
- Luna restored Andrianesis/Madani/Hümbs from primary records and reviewed the
  new claim scope. Root checked the bound logic and all rendered pages; clean
  builds, exact reconstruction and generated table reproduce. Response, scripts,
  independent checks, QA and release hashes: `research-20260928/review-response-v07/`.
- No new native optimization, cluster call or allocation. No active EGG jobs.
  No protected/private data accessed. The old no-incumbent bug was already
  fixed and tested; historical failures are not reclassified. No old-terminal
  damping outcomes imported, and cycling is not equated with no price support.
- Computational research objective remains active. Next bounded package:
  integrate a scope-checked analytical baseline in reporting/coordinator,
  then design a bounded sizing diagnostic before any further comparative run.
  Review the frozen retrieval design's four-call/4096-bit limits against actual
  stops; do not silently alter it, submit a duplicate, or infer approval for
  the still-pending one-replacement exception. Eberbach is already adapted;
  independent cases, repeated-seed/common-quality evaluation precede ML.

- Source/artifact backup: `c058236436fe84d83dde1f1e5769f53e5e550c5c`.
  PR56 is OPEN/draft and updated, unmerged. Initial CI36490355397 stopped only
  on trailing whitespace in four generated-log lines; those are normalized
  in the receipt follow-up, with no scientific/PDF change.
- Original Google Doc has one appended, Saved/reload-verified update titled
  “Review response and stronger bounds — 28 September 2026”; original heading
  intact, new heading last, complete opening sentence1of1, three links rendered.
  Source/receipt: `research-20260928/review-response-v07/GOOGLE_DOC_UPDATE.md`
  and `GOOGLE_DOC_RECEIPT.md`. Luna's final independent review found no blocker.
  Final receipt-backup CI should be checked once, without rerunning solvers.
  No active workers remain except stale pending cardinality agent (ignore).

## Prior checkpoint — integrated research draft 0.6 complete

- The complete LaTeX first draft is ready for author review: 19 pages, five
  vector figures, four tables, twelve cited references and a149-word abstract.
  PDF `output/pdf/egg-journal-v0.6-computational-draft.pdf`, SHA-256
  `1689d2e24538eb4761bdfd05624f01c55239862cb93d10d2f692fc031e905962`.
  `paper/latex/main.tex` now integrates model, theory, proofs, related work,
  condensed public case and the unchanged reviewed computational chapter.
  Historical v0.5 and the standalone six-page chapter remain untouched.
- Sol wrote the theory/model/proofs and independently checked the flat-round-0
  reconciliation; Luna checked the twelve primary literature records and the
  assembled core's consistency. Root checked the math, final source hashes and
  all19 rendered pages; final Tectonic/BibTeX compilation has no warnings.
  Source maps, bounded reviews, QA and ARTIFACTS.json are under
  `research-20260928/manuscript-integration/`. No solver suite was rerun.
- The reviewer's flat-price observation is confirmed: archived attempt2 round0
  has the identical physical case and a tangent objective that eliminates to
  the flat linear objective. Native OPTIMAL value is approximately408.53.
  A read-only compact metadata script and independent source-diff/design review
  distinguish redundant energy rows and native tolerances from the ideal model.
  Exact ideal flat enclosure remains[404.92,408.54]; no exact equality or
  experimental reclassification. Exact nonlinear evidence gives
  424.36<=CH<=D<=512.77 and0<=D-CH<=88.41, without a positive gap certificate.
- This completes a readable first draft, not journal readiness. The public
  evidence remains one Hildenbrand timetable/two depots; public global gaps
  remain open and no equal-quality speedup, retrieval or learned result exists.
  Qualification history/failed nonlinear headline moved out of the main story;
  the useful original public witness visual and computational evidence map stay.
- No active EGG jobs or cluster calls. Prior backup df1d562 passed
  CI36479784860. Do not poll old584876/577225 or resubmit them. The one-replacement
  decision below is still pending; do not infer approval or ask again.
  No reserved/protected/private data, native optimization or new allocation.
- Artifact/source/maps/reviews backed up at
  `6ffe5f8171c75c6a2646b253f6f63bcfab54d8a7`. PR56 reflects the complete draft
  and is confirmed OPEN/draft, unmerged. Original Google Doc update appended
  once, Saved and reload-verified: original heading intact, new heading last,
  unique body sentence1 of1, four links rendered. One stray verification phrase
  from an early keyboard action during reload was removed before the final
  persistence check; receipt records the correction. Wait for loaded UI before
  keyboard actions after a Docs reload.
  Source `research-20260928/manuscript-integration/GOOGLE_DOC_UPDATE.md`,
  SHA-256 `d8292f875c0bab4fa9c79383e3aec08cffce96d26d7e72c5deadeed81ed64b3a`.
  Receipt `research-20260928/agent-notes/google-doc-integrated-draft/RECEIPT.md`,
  SHA-256 `e7bae9575f1f8ae319a5fee9ccedce1a521f94fe558889f1e4a567479e327c86`.
  No active workers remain except stale pending cardinality agent (ignore).
  One Doc-helper follow-up hit the agent task limit; root completed the append.
  Final receipt/checkpoint backup CI can be checked once next heartbeat.
- Next bounded package: an independent reviewer-style assessment of the
  integrated draft's scientific contribution and the precise computational
  evidence still needed for the intended journal scope. Do not repeat proof,
  scalar-data or corruption audits. Use the existing pending comparison design
  and decision; no new run or training is authorized by manuscript completion.
  Flag any major change of scientific direction, not routine editorial fixes.

## Prior checkpoint — computational chapter ready for review

- The six-page LaTeX computational chapter is complete and independently checked:
  `output/pdf/egg-computational-chapter-20260928.pdf`, SHA-256
  `4873ab9db128ab3ba4a98c4ca4a9505a78e1bbad3597a0e80580d4181f1a88eb`.
  It contains four tables and two vector figures, with all six pages visually
  inspected after the final changes and a clean Tectonic log. Source and wrapper
  are `paper/latex/computational_results.tex` and `computational_review.tex`.
  `research-20260928/manuscript-computational/` records the source map, independent
  claim review, rendering QA and artifact hashes. No solver suite was rerun for
  this manuscript-only package.
- The chapter consolidates three overlapping development campaigns: 24 feasible-
  pool cells, 32 ordered-baseline cells, and 16 fixed-price calls. Both public
  depots are one Hildenbrand timetable. Reuse improves particular bounds, public
  global gaps remain open, and pricing starts show mixed effects. No public
  optimality, equal-quality acceleration, independent-network generalization or
  learned benefit is claimed. Failed rows retain missing intervals and paid time.
- This is a readable component, not the completed expanded first draft. The old
  v0.5 and `paper/manuscript.md` remain historical; `paper/latex/main.tex` remains
  an old outline. Next bounded package: consolidate theory, physical/economic
  model and literature into the complete LaTeX manuscript, integrating this
  reviewed chapter under `DRAFT_COMPLETION_PLAN_20260928.md`. Do not start a new
  experiment, sweep or training campaign merely to fill the manuscript.
- No active EGG jobs or cluster calls in this package. Prior backup e84642a
  passed CI36472242725. Do not poll completed584876 or577225. The pending
  one-replacement question below remains unanswered; do not infer approval or
  ask it again. No protected/reserved/private data were opened.
- Chapter source, PDF and reviews are backed up at
  `70eb7173b1b4347d99e5475354ed3f77e825b8ec`. PR56 now describes the completed
  chapter and remaining full-draft work and is confirmed OPEN/draft.
- Original Google Doc chapter update appended once and verified Saved after
  one normal reload: new heading last, unique body sentence1 of1, four links
  rendered. Source `research-20260928/manuscript-computational/GOOGLE_DOC_UPDATE.md`,
  SHA-256 `50ed9184f865074268e4f414e7cdaaaa2fe73ab9ecaf4f4ad678ccdebdf202e6`.
  Receipt `research-20260928/agent-notes/google-doc-computational-chapter/RECEIPT.md`,
  SHA-256 `2e5fcb78d207d016223a6f4bc9bffa8e003a0026395ff883a09ab3827d802b82`.
  No active implementation/review/Doc workers remain; ignore stale pending agent.
  Final source/receipt checkpoint backup CI can be checked once next heartbeat;
  no new solver test run is needed. Resume the manuscript integration above,
  without another queue poll or another request for the pending exception.

## Prior checkpoint — preflight failure repaired; replacement decision pending

- No active EGG jobs remain. At the19:05 UTC heartbeat, receipt backup513bc48
  passed CI36468333145. One scoped queue query found584876 absent; sacct reports
  FAILED1:0,12s on unicorn-cpu-75,1 CPU/8GB. Do not poll/resubmit that job.
- The wrapper failed in preflight after7s (all setup), before native probe,
  supervisor/controller or any of48 planned optimization children. Attempt
  directory contains only frozen.json. Its SHA matches the launch pin. Failure
  does not provide algorithm evidence. Preserved receipts, all48 unstarted rows,
  traceback and private-collection hashes are in
  `research-20260928/retrieval-comparison/failure-attempt1/`.
- Login kernel6.8.0-136 versus compute kernel6.8.0-138 necessarily fails the old
  exact full-environment equality check. Scoped scontrol node metadata confirms
  this sufficient cause; old generic diagnostics did not prove all other checks.
  Raw archive is private under
  `/Users/nadan/Documents/ChatGPT/egg/research-20260928/cluster/retrieval-comparison-attempt1/failed-job-584876/`.
- Minimal repair source `478d5656fac27173187e69d7c932da2d133a7055` is published
  and passed full CI36471163895 (4m25s). Nine focused pure tests, py_compile and
  independent Luna review passed. Full Python build/implementation/ABI, machine,
  packages, Gurobi runtime and native library/seed checks remain strict; kernel
  and hostname are recorded separately. Mismatch errors now identify fields.
  No native probe, optimization, replacement freeze or new allocation occurred.
- **User decision pending:** the frozen protocol expressly forbids retries.
  Root asked once via async question whether to permit one separately recorded
  replacement with identical scientific design and1 CPU/8GB/2h, or consolidate
  with existing evidence. Proposed disposition is
  `failure-attempt1/REPLACEMENT_DECISION.md` under the research package. Do not
  infer approval, repeat the question every heartbeat, or launch while pending.
- If the user authorizes exactly one replacement, use a NEW isolated checkout,
  leave `/home/nc437/egg-retrieval-comparison-20260928` at failed source68cfa64,
  and execute repaired source478d565. Freeze once, require unchanged scientific
  design digest `dc9ca0df332650f48dc4bb4ba1905dc80103847ce6c7202f239b494f91851abd`,
  create an exclusive new launch intent, then one sbatch. Full cases/markets/
  controls/order/caps stay fixed. No further replacement or wider sweep follows
  automatically. Relative attempt paths stay source-defined in the new checkout;
  job ID, source and isolated root distinguish it from the preserved failed run.
- While waiting, the next bounded package may start LaTeX consolidation from
  already reviewed evidence under DRAFT_COMPLETION_PLAN_20260928.md. Keep the
  six-case retrieval study explicitly unexecuted unless new results exist.
  ML remains optional; do not open reserved groups or train on failed labels.
- Original Google Doc failure/repair update appended once, Saved and one reload
  verified: new heading last, unique sentence1 of1, four links rendered. Source
  `research-20260928/retrieval-comparison/failure-attempt1/GOOGLE_DOC_UPDATE.md`,
  SHA-256 `e5170566cb29458d4279692004bf0b2f812b4edb6c544210ab6e9fe551e96ce0`.
  Receipt: `research-20260928/agent-notes/google-doc-retrieval-preflight-failure/RECEIPT.md`,
  SHA-256 `7e41a8cc16f2e5fd14a3d133199a41aad6b64bf10e600e57e61a3d4e55012d0f`.
  PR56 reflects the failed preflight and repaired source, stays draft/unmerged.
  No active implementation/review/Doc workers remain; ignore stale pending agent.
  Current final receipt backup CI can be checked once on the next heartbeat;
  do not repeat the already successful repair-source validation.

## Prior launch checkpoint — six-case retrieval comparison submitted

- **Active EGG job584876**: submitted once at18:46 UTC on28 September2026.
  The one launch queue check was PENDING/Priority,1 CPU/8GB. Do not resubmit.
  Launch receipt: `research-20260928/cluster/retrieval-comparison-584876.json`.
- Frozen execution checkout `/home/nc437/egg-retrieval-comparison-20260928`, HEAD
  `68cfa64fed41b61b423628b5f112eeb0b43934e2`; source passed full CI36466637135
  (test job4m56s). Do not pull or change this checkout while the attempt runs.
  Result path `result/retrieval_comparison/20260928-attempt1`; sibling `.launch`
  and `.prepare` hold exclusive intent/receipts. Frozen SHA-256
  `9fb6c638cef4c40de79b4084f82129fd5b2c76f634c33f7110ab3c0cf3f51889`.
- Scope: five generated synthetic DEV cases (seed1006:8/16/24 services;
  seeds1012/1009:16 each) plus Eberbach105. No reserved groups opened. Two fresh
  source hulls produce the shared checked pool; target arms are cold, retained,
  nearest actual source price and exact cheapest-current-bill. Each receives
  fresh global pricing without inherited bounds/native starts. Shared target
  planner/own-price response preserve the price-support question.
- Prospective cap:48 children,5160s routine allowances+1440s complete-child
  margins; controller6900s/outer7100s/Slurm2h,1 CPU/8GB,1 native thread, seed0,
  serial, no retry/requeue, excluded reserved node. Target arm order rotates.
  Full protocol `doc/RETRIEVAL_COMPARISON_PROTOCOL_20260928.md`.
- Three pure generator tests and eight pure runner tests passed. Independent
  Luna review found no remaining blocker; root matched all nine review pins.
  Direct proposals persist before verification; primary intervals exclude late
  or failed returns; paid source work includes pool preparation. Earlier checked
  source plans remain usable after later failed calls without relabeling failure.
- Mandatory service energy forces approximately33.59–234.34kWh outside any
  four-hour/90kW window for16/24-service cases; the8-service witness fits.
  These are input properties, not optimized fleet counts. Every fixed case stays.
- Initial remote preparation stopped at Slurm profile initialization under
  nounset before checkout creation/freeze/submission. Correcting source order
  allowed one successful freeze (2.906s); total preparation SSH work32.103s,
  including failed0.052s. Logs/time are preserved in PREPARATION_RECEIPT.json
  under `research-20260928/retrieval-comparison/`, raw logs privately at
  `/Users/nadan/Documents/ChatGPT/egg/research-20260928/cluster/retrieval-comparison-attempt1/`.
  This was not a solver attempt or job retry; exactly one sbatch succeeded.
- Original Google Doc updated once, Saved/reload verified: the new heading is
  last, its unique body phrase occurs once and all four links render. Source
  `research-20260928/retrieval-comparison/GOOGLE_DOC_UPDATE.md` SHA-256
  `37583ff8ae8b49528ea22f6a5ac509b10d1ecd99380be9d054d1390d80e5c2f2`;
  receipt `research-20260928/agent-notes/google-doc-retrieval-comparison/RECEIPT.md`
  SHA-256 `257686871da3eff7a2c9c2eb6f1df82e46c6033626013e69f32cbfc5389472a7`.
  PR56 description now reflects the fixed comparison and launch; stays draft.
  No implementation workers remain active. The only active research execution
  is job584876; do not revive the stale pending cardinality worker.
- Launch/CI/preparation/Doc receipts are being backed up in the current final
  documentation commit. At the next heartbeat check that newest backup CI once;
  do not rerun the already successful execution-source gate.
- Next heartbeat: one scoped `squeue -j584876` via unicorn2 after sourcing
  `/etc/profile.d/slurm.sh` BEFORE enabling nounset. If vanished, use scoped
  sacct and terminal receipts. If active, do not inspect partial outcomes or
  submit duplicates. On completion, collect sealed results plus sibling
  wrapper/preparation/launch receipts, independently review once, then produce
  complete tables/figures with failures, paid source costs, direct proposals,
  fresh intervals and qualified price-support metrics. Do not rerun to seek
  a favorable result. Consolidate the LaTeX draft after that review even if
  retrieval has no acceleration; ML is optional for the first draft.
- Old checkouts and completed jobs remain unchanged; do not poll577225.

## Previous checkpoint — independent timetable intake published

- Receipt backup 570f822 passed CI 36450899363. No active EGG jobs remain.
  No cluster queue query, solver or submission occurred in this package; do not
  poll completed 577225. Its execution checkout remains at 6759daa.
- Eberbach105/depot36 is now a development NativeCase. Its 105 services, 14 stops
  and 196 directed source travel arcs yield 10,359 movement modes. Pure native
  validation/compilation and a conservative 105-bus full-replenishment witness
  passed. Last charge ends at minute 1189.267, before the 1800-minute deadline.
  This is feasibility under declared EGG assumptions, not an optimized fleet.
- The compact model estimate is 291,637 variables and approximately 312,316 rows
  over 186 resource intervals; no native model was allocated. Preparation took
  7.417s including archive verification and JSON serialization, not model build
  or optimization. The future solve must count model construction inside its cap.
  EGG assumptions remain 400kWh usable, shared360kW/one connector, full initial
  and terminal inventory, 30h horizon, fixed vehicle cost100 and zero travel cost.
- Sol's minimal operator adapter preserves Hildenbrand's default behavior and
  regenerated bytes (SHA-256 af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6).
  Eberbach artifact SHA-256 is
  5ffb2f3a322b40c9c6c56972607fd0c4b21130cd35cd08e0a465f34fba67dc19;
  case identity 9dc30e1034953808e0c98cd467ae02272eaf6ddde2428a326d26b08b6db94c48.
  Eleven focused intake/regression tests passed. Notes/receipt and source context
  are in `research-20260928/benchmark-intake/`. Root matched both artifact hashes
  and checked the model-size formula against the compact formulation. Luna’s
  narrow adapter review found no blocking issue; root matched its five file
  pins. Review: `benchmark-intake/EBERBACH_ADAPTER_REVIEW.md` under the research folder.
- Public reservation is metadata/hash-only: 20 base groups, ten future training,
  four development, six test. Hildenbrand/Eberbach and all prior screens stay
  development. Every depot/day/tariff/timing/physical variant stays with its base.
  Byte differences do not establish semantic independence; a test alias of an
  exposed base loses clean-test status. Reservations are not a run commitment.
  Synthetic scaling is design-only: 8/16/24 services, seed groups1000–1014;
  test1011/1013/1010/1003 and dev1006/1012/1009. Root matched the recorded hash
  ranking. Full terminal replenishment is required; do not
  substitute the old 10%-terminal-SOC generator.
- Source Methods context was checked against the original Nature paper. Source
  deadhead inputs include estimates, not measured telemetry. Current browser
  access to Figshare/Table2 failed; pinned archive/previous attribution is reused,
  without claiming a fresh table or license check. No publisher schedules were
  used. Existing source/model assumptions remain explicit.
- **Next bounded package:** implement the small synthetic development generator
  and freeze one comparison protocol/runner for cold, retained-column and
  nearest-neighbor proposals, with exact cheapest-current-bill selection over
  the same stored fleet pool for price-only changes. Separate direct proposal,
  repair and global verification. Use the current full-charge physical model,
  keep build costs inside resource caps, preserve all failures and paid work.
  Do not adapt or inspect reserved test groups. No enlarged start sweep or ML
  training. One serial job maximum 1CPU/8GB, native thread1 and two hours, no
  retry/requeue, excluded reserved node, unless a later explicit budget is frozen.
- Follow `doc/DRAFT_COMPLETION_PLAN_20260928.md`: after that bounded comparison,
  consolidate the revised manuscript in LaTeX even if no speedup is observed.
  The v0.5 draft is historical; the expanded computational first draft is not
  yet complete. ML training is optional and cannot indefinitely delay writing.
- Intake milestone **4e789e3cc2a0b050040e827a9996b64eeb1c7b54** is pushed.
  Full CI **36458753423 passed** (test job4m24s): complete CBC tests and
  frozen-evidence reconstruction. Receipt `benchmark-intake/CI_RECEIPT.md`.
  Draft PR56 is updated and remains unmerged. The documentation/receipt backup
  CI may be checked once next heartbeat; no research workers remain active. Group reservation SHA-256
  34ba9087bc4ed1e6b55bfdce20f29ab501cfa3f7fa59dbc112d04ee4b6f055a3;
  final synthetic design SHA-256
  6e794dfd28d56eb5ae2016b3e5a80a334fd0c53cdf4af5644cdddecbbb30f02d;
  final review SHA-256
  c2ea810be3b761098f025de87ddf8d21b6e4a560a3589076f432062cb660ccd4.
  Root clarified that an energy upper bound does not prove realized charging
  pressure; retain uncongested generated cases rather than filtering outcomes.
- Original Google Doc appended ONCE under “Preparing independent timetables and
  protecting evaluation — 28 September 2026”. Luna verified Saved, final
  heading/body/four links and one normal reload with a unique body match.
  Source: `research-20260928/benchmark-intake/GOOGLE_DOC_UPDATE.md`, SHA-256
  f350add9a06a8683cda47e7e1e38e728f0af8f1b24ad3fcdc60862b9cd79dde4.
  Receipt: `research-20260928/agent-notes/google-doc-benchmark-intake/RECEIPT.md`,
  SHA-256 f18a0b742e3ddbd0c1c647c8b29672cd1e8eb68e5a4f5f61697bf64b5624bcf6.
  Root matched both. No export, duplicate append, or new cluster work.

## Previous checkpoint — pricing-start results published

- At the 16:01 UTC heartbeat, receipt backup b912078 passed CI 36444453893.
  One queue check for 577225 reported a vanished job ID; scoped accounting
  confirmed COMPLETED 0:0, 22m14s, one allocated CPU, 8 GB requested, on
  jingjie-cpu-15. No second queue check, optimizer call or new submission.
  **No active EGG job remains. Do not poll or resubmit completed job 577225.**
- Wrapper and supervisor returned 0, all processes quiescent, stable seal,
  frozen source/inputs unchanged. Execution checkout stays at 6759daa.
  Full private archive:
  `/Users/nadan/Documents/ChatGPT/egg/research-20260928/cluster/pricing-start-pilot-attempt1/sealed/20260928-attempt1`.
  Root matched all 119 manifest entries and the prospective frozen hash.
  MONITOR_20260928T1601Z.json, TERMINATION_577225.json and COLLECTION_RECEIPT.json
  are in `research-20260928/pricing-start-pilot/`.
- Sol's analysis is complete under `results-attempt1/analysis/`: all 16 calls,
  eight pairs, source/time accounting and two PNG/PDF scientific figures. Luna's
  independent physical/bound/source reconciliation passed without optimization;
  review at `research-20260928/agent-notes/pricing-start-result-review/REVIEW.md`
  (SHA-256 78be0fe9e3d89e2f8b9266e0a1f1df6b2b865946a02d05b30d9873fd234abf32).
  Root matched all reviewed pins and visually checked final figures. CSV line
  endings were normalized to LF for publication, with parsed values unchanged.
- All 16 calls returned on time: eight synthetic numerical certifications and
  eight public bounded outcomes. All eight hints were submitted; native
  acceptance is unobserved. Public native phases all reach roughly 160s.
  Starts improve one public incumbent by 1.105 and one lower by 11.785, weaken
  two lowers, and otherwise tie within the stated numerical tolerance. No
  general speedup, full iterative benefit or ML benefit follows.
- Common source costs are 0.32–2.74% above the best returned public incumbents,
  not the unknown optimum. Source generation once is 358.211s; online complete
  children 1317.507s; whole freeze command 1.956s. Their sum is 1677.674s.
  Internal freeze preparation 1.652s overlaps the whole command. Supervisor,
  wrapper and Slurm clocks enclose online work and are not added to that sum.
  The earlier pre-freeze helper parse failure remains preserved with unknown
  complete transport wall time. Raw logs stay in the private archive.
- **Next bounded package: independent timetable benchmark intake/design.**
  Validate one additional public network and a small synthetic scaling family;
  record physical assumptions and freeze base-network train/development/test
  grouping before training or comparative outcomes. Prepare cold, retained-
  column and nearest-neighbor proposal/repair comparisons with common quality
  targets and prospective resource caps. Current cases remain development.
  No immediate full-method start integration or enlarged start sweep; separate
  proposal feasibility/quality, repair and global verification. No protected
  A6/B3/confirmation outcomes or private GIRO publication.
- Results milestone **f3a388cda3034f212aeeb141acd7b17022706501** is pushed.
  Full CI **36450248274** passed (test job 4m26s); receipt is
  `research-20260928/pricing-start-pilot/results-attempt1/CI_RECEIPT.md`.
  Draft PR 56 now links the result tables and figures and records the next
  benchmark-intake step; it remains draft and unmerged. Original Google Doc
  appended ONCE with “Feasible starts help selectively, without a measured
  speedup — 28 September 2026”. Luna verified Saved, final heading/body/four
  links, then one normal reload with a unique body match. Source:
  `research-20260928/pricing-start-pilot/results-attempt1/GOOGLE_DOC_UPDATE.md`
  SHA-256 `1e90dc175e3d1b204ba73e91d193a3bb5e9158597243c4758e59a92e6e5d3f57`;
  receipt `research-20260928/agent-notes/google-doc-pricing-start-results/RECEIPT.md`
  SHA-256 `ab6a13e4f8be90bbddfd74480ef4dcbc2f3eceb60e2ed8b02bea51d59134936f`.
  Root matched both. No export or duplicate append. No new experiment ran in
  this results-publication package. Final documentation/receipt backup CI can
  be checked once next heartbeat; do not alter the remote execution checkout.

## Previous checkpoint — pricing-start pilot submitted

- At the 14:59 UTC heartbeat, prior receipt backup e72779f passed CI 36436107349.
  Sol implemented the fixed-price runner; Luna's independent static review found
  no blocking issue. Root matched the seven reviewed pins. Ten pure tests,
  shell syntax and compile checks passed. No extra optimizer qualification ran.
- Execution source **6759daa4eaeb92152607a3d60840d52988093973** is pushed and
  passed full CI **36443216684** (test job 4m21s). Draft PR 56 stays unmerged.
  `research-20260928/pricing-start-pilot/` contains the current launch receipts.
- **Active job 577225**, submitted once 28 September at 15:28 UTC. One launch
  queue observation: `PENDING (Priority)`, 1 CPU/8 GB requested, 1-hour limit,
  one native/numerical thread, no retry/requeue, exclude scaglione-compute-01.
  Receipt: `research-20260928/cluster/pricing-start-pilot-577225.json`.
- Execution checkout: `/home/nc437/egg-pricing-start-pilot-20260928` at 6759daa.
  Attempt: `result/pricing_start_pilot/20260928-attempt1`.
  Keep this checkout at its execution commit until collection. The old source
  comparison checkout remains f4b342d; completed job 575215 was not polled.
- Prospective frozen input SHA-256:
  `3204f528d8ef25b75c76841a5d0ed8d86b914d3f30126f5aabf580fb7aab385a`.
  All four pools eligible; eight selected fleet/price queries, 16 cold/start
  calls. All marginal vectors differ from their linear query. Observed GRB
  seed 0 and library hash, Python 3.12.13/MIP 1.17.6/GRB 12.0.3,
  NumPy 1.26.4/SciPy 1.13.1. Source physical plans only; no historical bounds
  consumed. Both arms share the known feasible-plan baseline.
- Freeze command 1.956s including startup/write; internal preparation 1.652s
  overlaps it. A first root helper failed Python parsing before any freeze,
  native probe or submission; transport is preserved, complete wall unmeasured.
  Corrected helper performed the sole input freeze. Details in PREPARATION_NOTES.md.
  Controller/outer caps 2700/3000s; synthetic core/child 60/90s, public 180/210s.
- No outcomes have been inspected. Next bounded package: one compact queue check
  for 577225 via unicorn2 after loading `/etc/profile.d/slurm.sh`. If vanished,
  inspect scoped sacct and the sibling `.slurm_wrapper_receipt.json`, attempt
  `supervisor_receipt.json` and `MANIFEST.json`. Require quiescence/stable seal
  before collection and independent review. Preserve all failures/paid time.
  Compare quality and timing against the common feasible baseline; do not infer
  start acceptance, global certification, full iterative speedup or ML benefit.
  No resubmission, enlarged sweep, or partial-outcome adaptation.
- Original Google Doc appended ONCE with “Fixed-price starting-point pilot
  launched — 28 September 2026”. Luna verified Saved to Drive, final heading,
  body and four links, then one normal reload with a unique body match.
  Source `research-20260928/pricing-start-pilot/GOOGLE_DOC_UPDATE.md` SHA-256
  `aa83e9258899b956d35e11e1a7c8364400e85da90ad1340560f5c1bb5bbcefaf`;
  receipt `research-20260928/agent-notes/google-doc-pricing-start-pilot/RECEIPT.md`
  SHA-256 `c0765ff0f1463f389f398cb797ca59a828b6275b462b76598fc0c9104e3d3bd8`.
  Root matched both. No export or duplicate append. Draft PR 56 updated with
  the actual launch and claim limits. The receipt backup containing this
  checkpoint changes documentation/receipts only; check its CI once next
  heartbeat, without changing the remote execution commit.

## Previous checkpoint — pricing-start core and prospective design complete

- At the 13:58 UTC heartbeat, prior receipt backup
  9867fdf27d7444a65706dbcd2bb36f36782d2c09 passed full CI 36429393790.
  No active EGG job remains; completed jobs were not polled or resubmitted.
- Current bounded package: an opt-in known-feasible-fleet start for compact
  fixed-price native pricing, plus prospective pilot design. Sol owns core
  mapping/validation/telemetry and focused tests; Luna reviews the contract and
  method; root manages protocol, source inventory and publication. No main-hull
  integration, pilot runner or cluster launch in this package.
- Mapping is viable: the compact model has one binary family, movement
  selection. Assign every movement binary, including zeros, after checking the
  full physical plan and provenance; native continuous variables are completed
  by the solver. Hint submission is not evidence of native acceptance or a
  certificate. Start setup belongs inside the same complete-call deadline.
- Draft protocol: `doc/PRICING_START_PILOT_PROTOCOL_20260928.md`.
  It declares 16 calls, four existing development cases by two price queries
  by cold/start, with order counterbalanced within query across cases. Both
  arms share a known feasible baseline when interpreting quality. Preserve
  historical source generation cost separately from measured online work.
  Public variants remain one timetable group. Prospective resource ceiling:
  one serial job, 1 CPU/8 GB/1 hour, all threads one, no retry/requeue, exclude
  scaglione-compute-01. No submission has occurred.
- Metadata inventory: `research-20260928/pricing-start/SOURCE_INVENTORY.json`.
  Intended state-0 qp-cache pools contain 2/4/2/2 columns and have on-time
  return-0 receipts. Original public child costs are about 175.48/175.47s.
  This is an inventory, not a new source admission or solver-start check.
- Core implemented in `src/egglab/native_pathflow.py`; 40 focused pure tests
  passed. One CBC cyclic-case functional check (5s wall/3s phase cap) returned
  a certified numerical interval around 37 in about 0.23s total. It preceded
  the final pure-tested guard against unexpected integer variables. This is
  not Gurobi/public-case performance evidence; start acceptance is unknown.
  Implementation and smoke receipt: `research-20260928/agent-notes/pricing-start/`.
  Luna's independent code/protocol review passed; root matched its six pins.
  The final index merely records that review verdict; code and protocol are
  unchanged. Core/protocol source **d0df8d7440d026aabe236bafa3c8031b31b14bc9**
  is pushed; draft PR 56 links the implementation and prospective protocol.
  Full CI **36435346518** passed on attempt 1 (test job 4m19s), including the
  complete CBC suite and frozen-evidence reconstruction. Receipt:
  `research-20260928/pricing-start/CI_RECEIPT.md`.
- Original Google Doc appended ONCE with “A feasible fleet as a solver starting
  point — 28 September 2026”. Luna verified Saved to Drive, heading/body/links,
  then one normal reload with the distinctive claim-limit phrase found once.
  Source: `research-20260928/pricing-start/GOOGLE_DOC_UPDATE.md` (SHA-256
  `1208336bf2abd50a82d15442d2049311c62292beaf159dee8f9f325993e84890`).
  Receipt: `research-20260928/agent-notes/google-doc-pricing-start/RECEIPT.md`
  (SHA-256 `d603bf396c27d4f19cbd4f5915b6ff12d5a53b22ab1f9c3e11194617647e4cf4`).
  Root matched both hashes. No export or duplicate append.
- This package is complete; no worker assignment or EGG job remains active.
  Next heartbeat: check the final receipt-only backup's CI once, then proceed
  directly to the runner/launch package below. No core or protocol redesign is
  needed unless implementation exposes a specific new issue.
- Next separate package: build the bounded pilot runner, freeze source and
  exact selected inputs, complete relevant checks, then submit the one job.
  Its reader must account for `mip_start_setup` submission/rejection/timeout;
  the legacy pathflow qualification reader rejects this new opt-in event.
  Freeze Python-MIP/backend versions and effective model seed for both arms.
  Do not repeat core design, old outcome audits or tiny smoke tests without a
  specific new issue. No pilot or main-hull integration has run.

## Previous checkpoint — no-plan pricing repair complete

- At the 12:58 UTC heartbeat, no active EGG job or outstanding worker assignment
  remained. Previous receipt backup 453783266d5bfff0fcb80f762540ca95d9e5acd7
  passed full CI 36423716489. Completed job 575215 was not polled or rerun.
- Sol repaired the compact wrapper and shared coordinator: both assumed an
  explicit pricing result contained a plan. A distinct `pricing_unresolved`
  event retains the full return and is accepted by the qualification reader.
  Successful pricing-result/bound/cache admission remains strict. No cluster
  submission or MIP-start implementation was made.
- Final behavior: a correctly identified unresolved return with no
  plan ends without a new certificate. Earlier verified lower and feasible
  mixture are preserved as `stalled_bounded`; without both, status is
  `unresolved`. The reason identifies the no-plan pricing return. Invalid
  present witnesses and claimed success without a witness remain errors.
- Package index: `research-20260928/no-plan-repair/README.md`.
  Implementation note: `research-20260928/agent-notes/no-plan-repair/`.
  Independent review: `research-20260928/agent-notes/no-plan-repair-review/`.
  All 156 focused tests passed in 0.87s over seven test files, including first
  and late unresolved calls, finite decoy lower, invalid present witnesses,
  cache-only noncertification and admission of a bounded prefix with unresolved
  tail. No local optimization was run. Luna's independent code/contract review
  passed; root matched all six review pins. Repair source
  **2343d492fe629af2fe2b70b2bbbc79b123fecbb3** is pushed to the existing branch;
  draft PR 56 describes the repair and links the immutable package. Full CI
  **36428652019** passed on attempt 1 (4m27s test job), including complete CBC
  tests and frozen-evidence reconstruction. Receipt:
  `research-20260928/no-plan-repair/CI_RECEIPT.md`.
- Original Google Doc appended ONCE with “Handling incomplete pricing calls —
  28 September 2026”. Luna verified Saved to Drive, heading/body/immutable link,
  then one normal reload and a unique body match. Source:
  `research-20260928/no-plan-repair/GOOGLE_DOC_UPDATE.md` (SHA-256
  `caafbf8075012fe6264906a3ad7ce7df1f4b57a9dfc41e3c5b1ae71facf46c75`).
  Receipt: `research-20260928/agent-notes/google-doc-no-plan-repair/RECEIPT.md`
  (SHA-256 `e1508176b32652715325aca1964e9d45fe199506bb902f0492e4648e9ce2f08d`).
  Root matched source and receipt; only an immutable link was added to the
  reviewed Doc draft. No export, retry or duplicate append.
- This work package is complete; no EGG job or worker assignment remains active.
  Next heartbeat: check this final receipt-only backup's CI once, then move to
  the next package below. Do not repeat source/evidence audits or poll 575215.
- Next separate package: assess mapping a checked known feasible fleet into a
  physical-pricing MIP start. Keep the other master/cache choices fixed, define
  outcomes (incumbent availability, final bounds and complete paid time), and
  record prospective cases/caps before launching any comparison. Start mapping,
  validation and overhead all count; a retained master column alone is not a
  native start. No speed or optimality claim is added, no failed comparison row
  is reclassified, and this repair commits no additional experiment budget.

## Previous checkpoint — completed solver comparison results

- At the 11:58 UTC heartbeat, one scoped squeue check reported no current job
  575215. Scoped sacct records COMPLETED, exit 0:0, elapsed 48m15s, allocated
  2 CPUs/8 GB on snavely-cpu-16. The request was 1 CPU and configured threads
  remain one. Wrapper elapsed is 2887s; supervisor elapsed is 2873.925s.
- Supervisor confirms quiescence, stable seal and unchanged source. Root
  collected the sealed attempt privately and verified all 260 manifest files,
  all 25 frozen source pins, and the previously recorded frozen-file hash.
  Source remains f4b342dc85799d01d9313baeaf8c9ec527759d59.
  Completion receipt: `research-20260928/cluster/solver-baseline-comparison-575215-completion.json`.
  Private evidence root:
  `/Users/nadan/Documents/ChatGPT/egg/research-20260928/cluster/solver-baseline-comparison-attempt1/sealed/20260928-attempt1`.
- All 32 declared rows are present: final counts are 11 certified,
  18 budget-exhausted and 3 failed. Failed rows are public depot15/state1/cold,
  and public depot15 and depot16/state1/QP feasible without cache. These child
  failures occurred inside their hard deadlines; `on_time=false` reflects
  exit 2, not a timeout. Keep their spent time and failure status visible.
- Results, full tables, compact traces and two PNG/PDF figures:
  `research-20260928/solver-baseline-comparison/results-attempt1/`.
  Luna independently reproduced all 29 available raw assessments, all 12
  own-source admissions, four target-cache lineages and 16 paid-pair totals.
  Review: `research-20260928/agent-notes/solver-baseline-comparison-results/`.
  Root visually checked the final figures, including failed-target markers.
- Public cache targets end at numerical intervals [405.83, 471.52] and
  [420.45, 491.46], with paid two-state time about 352s each. Within those
  same runs, inherited pricing evidence strengthens the lower by 98.82/69.83
  over the fresh target lower. This posthoc decomposition does not isolate a
  cross-arm speed effect. The intervals remain open; stored-float exact replay
  does not remove native solver-tolerance qualifications. Both depots share
  one development timetable. No optimality, scalability or ML benefit claim.
- Three failures share one confirmed wrapper bug: native pricing returns
  NO_SOLUTION_FOUND with no incumbent/plan, and the compact wrapper checks the
  absent plan's extraction policy. An earlier bounded pricing call exists in
  each trace. This is not evidence of a bad completed physical witness. Keep
  all three attempts failed; never promote their saved prefixes to final runs.
- **Next bounded package:** repair that no-plan return path in the compact
  oracle wrapper, with focused regressions for the observed shape. Preserve
  previous verified evidence, explicit unresolved outcomes, rejection of bad
  present witnesses and the fresh-pricing certification gate. Do not rerun the
  full 32-cell comparison solely for a status fix. Then assess a prospectively
  timed known-feasible-fleet MIP-start baseline for physical pricing before
  broader cases, nearest-neighbor retrieval and learned proposals.
- No active EGG job remains. Do not poll/resubmit 575215. No rerun, new
  experiment or solver change was made in this results package.
- Reviewed results milestone **5e53dc81ed4a05711e76fa647f23a9f31afae81a**
  is backed up on the existing research branch. Draft PR 56 now describes
  the complete comparison, unresolved public gaps and observed return-path
  defect, and links immutable reviewed tables and figures. Results CI
  **36422951827** passed the complete gate on attempt 1 (test job 4m23s).
  Receipt: `research-20260928/solver-baseline-comparison/RESULTS_CI_RECEIPT.md`.
- Original Google Doc appended ONCE with “Completed ordered solver comparison
  — 28 September 2026”, including immutable report/figure links. Luna observed
  Saved to Drive, the new outline heading and the distinctive interval phrase
  exactly once; after one normal reload the heading and same body match
  persisted. No export or duplicate append was attempted.
  Source: `research-20260928/solver-baseline-comparison/RESULTS_GOOGLE_DOC_UPDATE.md`
  (SHA-256 `19ce40943eb0e09492a8bc3c30640a44053f1bc5d6d1acd2b91a3b9ae11a25f3`).
  Receipt: `research-20260928/agent-notes/google-doc-solver-baseline-results/RECEIPT.md`
  (SHA-256 `cb71ea0130d9602fcd099c48f48b5f22955e92ad46e79d9cfab9f5c69c417b90`).
  Root matched both hashes. Final source differs from the reviewed draft only
  by the explicit outward-rounding label and published immutable links.
- Results package is complete. No workers have outstanding assignments and
  no EGG job remains active. Next heartbeat should check the final receipt-only
  backup's CI once, then undertake the bounded no-plan wrapper repair above.
  Do not repeat the sealed archive/replay review or poll completed job 575215.

## Previous checkpoint — ordered solver comparison running

- Documentation backup db46181 passed full CI 36410820696, verified at the
  10:57 UTC heartbeat. Completed jobs 569799/572392 remain unchanged.
- New protocol: `doc/SOLVER_BASELINE_COMPARISON_PROTOCOL_20260928.md`.
  It freezes 32 development cells: four cases, four ordered methods, two states.
  Methods are reserve-cold, reserve with retained feasible plans, numerical
  master with retained plans, and numerical master with retained plans plus
  checked physical pricing bounds. Both public depots share one timetable.
- New runner/wrapper: `src/experiments/solver_baseline_comparison.py` and
  `src/cluster/solver_baseline_comparison.sbatch`; index:
  `research-20260928/solver-baseline-comparison/README.md`.
  Sol completed implementation; all 12 focused pure tests passed. Luna's
  independent static review passed; root checked the final source/protocol
  hashes. Review: `research-20260928/agent-notes/solver-baseline-comparison/REVIEW.md`.
  Execution source **f4b342dc85799d01d9313baeaf8c9ec527759d59** is published
  and passed full CI **36408897677**, attempt 2. Attempt 1 stopped during
  unchanged dependency installation (kiwisolver unavailable), before tests;
  one CI retry passed all gates in 4m13s. Both attempts are retained in
  `research-20260928/solver-baseline-comparison/CI_RECEIPT.md`.
- Paid two-state totals include each method's own initial solve, target solve,
  and parent source-validation overhead outside those children. Worker replay
  remains inside the child time. Failed or ineligible sources are preserved;
  there is no fallback to another method's pool or a substituted cold run.
- Resource ceiling: one serial job requesting 1 CPU/8 GB, all native/BLAS
  threads one, Slurm two hours, no retry/requeue, exclude scaglione-compute-01.
  Native targets sum to 64 minutes; child hard caps to 80; controller cap 90;
  outer wrapper cap 100. Runtime preflight found existing NumPy 1.26.4 and
  SciPy 1.13.1 with GRB; no install or optimization was performed.
- Exclusive execution checkout:
  `/home/nc437/egg-solver-baseline-comparison-20260928`; attempt
  `result/solver_baseline_comparison/20260928-attempt1`. An exclusive submission
  intent preceded the single sbatch call. **Job 575215** was submitted once at
  10:25 UTC and observed **PENDING (Priority)** with 1 CPU/8 GB requested.
  Receipt: `research-20260928/cluster/solver-baseline-comparison-575215.json`.
  At the 10:57 UTC heartbeat's one scoped queue check, the job was RUNNING,
  elapsed 32:40, on snavely-cpu-16, with 2 CPUs and 8 GB allocated despite the
  1-CPU request. The source still configures all numerical/native threads to one.
  Frozen metadata confirms f4b342d and GRB 12.0.3, MIP 1.17.6, NumPy 1.26.4,
  SciPy 1.13.1 and Python 3.12.13. Frozen file SHA-256:
  `62411caa9bf34b2de2d825c681e76f37386118aee1bda4e110b1bd524c740f38`.
  Private metadata snapshot is retained; compact observation:
  `research-20260928/cluster/solver-baseline-comparison-575215-monitor-20260928T1057.json`.
  No scientific outcomes have been read; the running attempt is not yet sealed.
- Next heartbeat: make one compact scoped queue check for **575215**, via
  unicorn2 after loading `/etc/profile.d/slurm.sh`. If vanished, use scoped
  sacct and the recorded attempt/wrapper/supervisor receipts. Do not duplicate
  submission or retry/requeue. Collect/review all declared rows only after
  quiescence; preserve failures, spent time and incomplete cells. Compare
  bounds and paid time before claiming improvement or expanding the sweep.
- Original Google Doc appended ONCE with “Ordered solver comparison launched
  — 28 September 2026”. Luna observed Saved to Drive, the launch outline entry,
  corrected body wording and commit links. Root verified source/receipt hashes.
  Source: `research-20260928/solver-baseline-comparison/GOOGLE_DOC_UPDATE.md`;
  receipt: `research-20260928/agent-notes/google-doc-solver-baseline/RECEIPT.md`.
  Full-export/prefix verification remains unavailable after the prior browser
  block; do not repeat that route or duplicate the section.
- A narrow reconciliation found zero matches for both the previous numerical
  master title and its distinctive opening, despite the earlier save receipt.
  The saved source remains intact. Luna restored that one missing note ONCE as
  “Recovered prior update: Numerical master integration completed — 28 September
  2026”, with a historical lead noting that the comparison is now submitted.
  Saved to Drive and final heading 39/39 were observed; the unique opening now
  matches once, and the launch heading remains present. Exact recovery source:
  `research-20260928/solver-baseline-comparison/RECOVERED_NUMERICAL_MASTER_UPDATE.md`.
  Root verified both append sources and the final receipt hashes. The cause of
  the earlier discrepancy is unknown; no broader history audit was performed.
- Launch documentation backup db46181 is verified; do not recheck that CI.
  This heartbeat records operational monitoring locally; consolidate its receipt
  into the next completed-results GitHub/Google Doc milestone. No duplicate
  Doc update, submission or new experiment was made while the job is running.
  No implementation or Doc worker remains active. PR56 describes the submitted
  comparison and stays draft/unmerged. No user decision is pending.

## Previous checkpoint — numerical restricted-master integration

- Previous documentation backup 2e15dec passed full CI 36396998189. No active
  EGG jobs; do not poll/resubmit completed 569799/572392.
- Added explicit `master_policy="numerical_qp_proposal"` to core and compact
  wrapper, with `qp_denominator=1_000_000_000` and `qp_maxiter=500`. Controls
  enter opt-in identity/events. The default native-LP path stays unchanged.
- One SLSQP proposal replaces the native LP and pairwise rational polish for
  each selected master call. Exact fixed-denominator simplex and physical
  mixture replay produce an upper; exact restricted-pool residual is reported.
  An open restricted residual may proceed to fresh physical pricing, which
  remains required before global numerical certification. SLSQP success is
  diagnostic only; valid non-success candidates can still be used.
- Proposer/import/malformed-weight failures return `proposal_failed` with prior
  verified bounds/mixture retained. Physical replay errors remain hard failures;
  time/bit limits remain `budget_exhausted`. No hidden native fallback. A final
  negative enclosure fails closed in either new opt-in policy.
- Proposal/setup and replay work count inside the target deadline; solver
  status, iteration diagnostics, rational-bit maximum and component time are
  recorded. In-process SciPy is not forcibly preempted: the new runner must
  preserve whole-child deadlines, actual elapsed and all overshoot/failures.
- Core files: `src/egglab/native_hull.py`, `src/egglab/native_pathflow_hull.py`.
  New tests: `src/tests/test_native_hull_numerical_master.py`.
  Existing helper: `src/egglab/restricted_qp_proposal.py`.
  Note: `research-20260928/numerical-master/README.md`;
  focused review: `research-20260928/agent-notes/numerical-master/REVIEW.md`.
  The 37 focused numerical-master/cache/reuse tests passed. Independent review
  passed and root verified all four reviewed file hashes (including the unchanged
  proposal helper). Implementation **dc5e01480996ae97adb08821e9fb518cba43492b**
  is backed up and passed full CI **36402944039**, including the complete CBC
  suite and frozen-evidence reconstruction.
- **Next bounded package:** freeze and run a new matched development comparison,
  retaining reserve-cold and reserve-feasible baselines, then adding numerical
  master and numerical master + cached bounds. Candidate: the same four physical
  cases and two markets, four ordered arms (32 cells), not a full factorial.
  Use one serial job requesting 1 CPU/8 GB, native/BLAS threads=1, <=2 h, no
  retry/requeue, exclude scaglione-compute-01. Freeze exact caps/source/accounting
  before submission; do not reuse completed attempt paths. Preserve
  `proposal_failed`, bounded/late/ineligible outcomes and all paid preparation.
  No new cluster experiment or performance claim belongs to this code package.
- Original Google Doc updated ONCE with “Numerical master integration completed
  — 28 September 2026”; Luna observed Saved to Drive, final heading, full body
  and review link. Do not duplicate. Source and receipt:
  `research-20260928/numerical-master/GOOGLE_DOC_UPDATE.md` and
  `research-20260928/agent-notes/google-doc-numerical-master/RECEIPT.md`. Root
  verified source bytes/hash. Full-export/prefix verification remains unavailable
  after the prior browser block; do not repeatedly retry that route.
- Final receipt/handoff backup is documentation only. Check its latest CI once
  next heartbeat, then build/freeze the comparison runner and proceed under the
  existing resource ceiling after its required checks. No active agents/jobs
  remain at handoff. PR56 remains draft/unmerged. No user decision is pending.

## Previous checkpoint — physical pricing-bound cache implementation

- Prior documentation backup 703f460 passed full CI 36392455640. No active
  EGG jobs; do not poll or resubmit completed 569799/572392.
- A separate opt-in `bound_cache_policy="physical_pricing"` now supports checked
  transfer of the immediately preceding state's physical pricing bounds. It is
  independent of feasible-column reuse. Source calls retain original prices,
  numerical bounds, replay projections, oracle/physical/extraction identity,
  source-state lineage and integrity digests. Target Fenchel conjugates are
  recomputed individually; their strongest valid lower is eligible for use.
- Core/wrapper: `src/egglab/native_hull.py`, `src/egglab/native_pathflow_hull.py`.
  Focused tests: `src/tests/test_native_hull_pricing_cache.py`; 26 new-cache and
  existing feasible-reuse tests passed. Independent review passed against the final three source hashes. Execution
  implementation **8a54521b92c518aa999c6f18a915eca2ffdc8e21** is backed up and
  passed full CI **36396410119**, including complete CBC tests and reconstruction
  of frozen journal evidence. This does not benchmark native cache performance.
- Source/preparation accounting: validation/re-evaluation occurs within the
  target deadline; measured coordinator/native pricing costs are retained.
  Complete child/startup/preparation costs stay unknown in the core. A future
  runner must pin source files, code and original on-time receipts, and account
  for complete paid costs. Digests do not independently prove native bounds.
- Certification requires a successful fresh target pricing call. A cache can
  strengthen an unfinished result but cannot alone certify it. A reversed final
  enclosure fails closed even when a work limit prevents fresh pricing. Default
  outputs/identities and all frozen pilot arms remain unchanged.
- Scientific/API note: `research-20260928/pricing-bound-cache/README.md`.
  Focused review: `research-20260928/agent-notes/pricing-bound-cache/`.
  This is implementation only: no new optimizer benchmark, timing advantage,
  public gap closure, data intake or learned method is claimed.
- Next bounded package after this change passes CI/review: integrate the existing
  separate numerical restricted-master proposal in
  `src/egglab/restricted_qp_proposal.py` (tests in
  `src/tests/test_restricted_qp_proposal.py`) under replay/global-bound checks,
  then freeze a new matched comparison. Keep reserve-cold/feasible-plan
  baselines and make cached bounds an explicit factor. No new cluster job yet.
- Original Google Doc updated ONCE with “Pricing-bound reuse implemented —
  28 September 2026”; Saved to Drive, last heading, full body and link were
  observed by Luna. Do not duplicate. Source and receipt: respectively
  `research-20260928/pricing-bound-cache/GOOGLE_DOC_UPDATE.md` and
  `research-20260928/agent-notes/google-doc-pricing-cache/RECEIPT.md`. Root verified
  the append-source hash. Full-export preservation verification remains
  unavailable; do not repeat the blocked export route at each heartbeat.
- Final receipt/handoff backup is documentation only. Check its latest CI once
  next heartbeat, then proceed with the next bounded QP integration package.
  PR56 stays draft/unmerged. No active workers or EGG jobs remain at handoff.

## Previous checkpoint — matched pilot completed and analyzed

- **No active EGG job is recorded.** Job 572392 completed 0:0 in 36:49 on
  snavely-cpu-15. Requested 1 CPU/8 GB; Slurm allocated 2 CPUs, while the serial
  runner, native solver and numerical libraries were configured for one thread.
  Wrapper elapsed 2,194 s; supervisor 2,188.9533 s; batch MaxRSS 408,956 K.
  No timeout, source drift, extra job or retry. Do not poll jobs 569799 or 572392.
- Execution source **77dee963eb30ba85bca68b3efcf61d099fa33076** passed full CI
  36385045833; launch/Doc backup 3bdf51d also passed full CI 36386621965.
  Remote checkout: `/home/nc437/egg-feasible-pool-pilot-20260928`.
  Attempt: `result/feasible_pool_pilot/20260928-attempt1`.
  Frozen SHA cc3f61e5357680064da513bbbf93e8f2e62f46d749ee94463db2e541a3f73649;
  original seal SHA b2f3630f4229792c47f60bc2a1a60645d506fd887feaa2a3e379bd8107628e6a.
- Collection: `research-20260928/cluster/feasible-pool-pilot-572392-collection.json`.
  All 191 sealed entries plus the seal verified unchanged. Private 147,312,640-byte
  archive SHA a5cf8dbd31a1a18e417871b57a57d3deb27602399a5672705dad42157868d2e0.
  It and the extracted package are in OUTER
  `research-20260928/cluster/feasible-pool-pilot-attempt1/collected/`.
  Public ZIP contains 75 original scientific files; 117 omissions are listed.
  Full raw events/logs stay private. Never edit the sealed attempt.
- Results/figures/evidence index:
  `research-20260928/feasible-pool-pilot/results-attempt1/README.md`.
  Analysis backup: **b2b160046cd56dfcab87986b961011b0041d8345** on GitHub;
  full CI 36391559312 passed (including complete tests and frozen-evidence reconstruction).
  Pure reporter: `src/experiments/feasible_pool_pilot_report.py` (6 focused tests
  passed). It accounts for all 24 cells, 12 paired comparisons and 12 paid
  two-state totals, with 57 compact pricing traces. Bounds display outward;
  root visually reviewed both final figures. Independent review checks raw
  receipts, all saved physical/mixture/Fenchel replays and matched arithmetic.
- **7 native-certified, 17 budget-exhausted**, all 24 on time with complete
  evidence. The four public reserve-cold runs processed two masters instead
  of one and improved upper bounds by about 17.80–69.39 cost units. Paid public
  two-state time was about 350 s versus 369 s legacy cold. These are descriptive
  final-bound/time results, not a measured equal-quality speedup.
- Feasible reuse certified the shifted three-service case; both cold arms hit
  rational-polishing limits. Public reused pools improved upper costs but
  weakened fresh lower bounds: shifted widths 154.12 versus 186.96 for depot15,
  and 161.44 versus 154.24 for depot16. Both public reused runs stopped on the
  projected rational-bit limit after adding a current-market column. Their paid
  times were slightly above reserve cold (~351 versus ~350 s). No public gap
  closure, scalable acceleration or learning claim follows. Both public depots
  remain one base timetable; all these cases are development data.
- **Separate posthoc lead:** a saved physical pricing bound at unchanged p=.20
  is reusable under a changed supply cost after RECOMPUTING its target Fenchel
  conjugate. The penalty is about 2.70, giving shifted target lower bounds
  405.8331/420.4551 and gaps about 64.05/70.21 using this run's saved uppers.
  This changes no frozen outcome/time and remains tolerance-qualified.
  Script: `research-20260928/feasible-pool-pilot/cached_oracle_bound_diagnostic.py`;
  note/data: `results-attempt1/posthoc_oracle_bound/` under that pilot directory.
  Root and Luna independently checked the algebra and original pricing evidence.
- **Next bounded work package:** add a separate opt-in physical-oracle-bound
  cache with verified same-physical-model/oracle/extraction/price provenance,
  re-evaluate the target conjugate, include all preparation/checking costs,
  and still require fresh target-market pricing before certification. Preserve
  current defaults and old frozen arms. This is a prospective policy change;
  never silently relabel the posthoc bound as a timed result. Use focused tests,
  not another broad qualification campaign. Then address the rational-polishing
  stop using the existing separate numerical-QP proposal before a larger sweep
  or learning. Different timetables cannot inherit pricing certificates directly.
- Google Doc results update was appended ONCE and showed Saved to Drive, with
  its heading last in the outline and full body/link observed by Luna. **Do not
  append again.** Receipt/manifest: `research-20260928/agent-notes/google-doc-feasible-pilot-results/`.
  Chrome blocked both post-edit exports (ERR_BLOCKED_BY_CLIENT), so exact
  before-prefix/full-export preservation verification remains incomplete. Root
  verified all three available manifest file hashes; no after export exists.
  This export limitation does not block the next solver package. Avoid repeated
  export retries; verify at a later meaningful Doc update if the route works.
- PR56 description now reflects the completed pilot, mixed reuse outcome and
  separate posthoc bound lead; draft/unmerged. No new optimizer run was made
  in this analysis. The final receipt/handoff backup is documentation only;
  check its latest CI once at the next heartbeat before code work, without
  repeating the completed execution or analysis checks.

## Previous checkpoint — first computational screen completed

- **No active EGG job is recorded.** Job 569799 completed 0:0 in 35:57, on one
  CPU/8 GB. Do not poll or resubmit it. Execution source e39bc7e31ea21dae64365c31fa88a85e4b0de349;
  frozen SHA b36b15a5b9ac8945cff3b4cfd5e8441c705c3c536870f7a34c3d08e7f6f2dca2.
  Wrapper elapsed 2,139 s; supervisor elapsed 2,136.29 s; whole Slurm elapsed
  2,157 s includes setup. Reporter source 6242218 passed full CI 36376089314.
- Collection receipt: `research-20260928/cluster/computational-screen-569799-collection.json`.
  Full 155 MB archive stays private in the OUTER workspace at
  `research-20260928/cluster/computational-screen-attempt1/collected/full-private-archive.tar`.
  Extracted attempt is in `collected/package/result/computational_benchmark/20260928-attempt1`.
  Original manifest SHA 78d642e204143a05938a19fc447791178ae7890f5a01a8e05a179e73f6eab160;
  237 listed files plus seal verified unchanged. No raw stdout/stderr publication.
- All 32 declared stages are accounted: 10 native-certified, 10 bounded,
  9 budget-exhausted, 3 ineligible. All 29 launched stages returned on time with
  complete author-side assessments. No hard stage failures/timeouts. The two
  Hildenbrand depot variants are ONE timetable group; all screen cases are development.
- Only the cyclic example supports a certified two-state cold/retained comparison.
  Shifted-state pricing requests drop 3 to 1; both initial states are paid for.
  This tiny example is not a public-data speedup or a learning result.
- All six launched public hull stages spent about 173 s in two native pricing
  solves out of about 184 s end-to-end, versus about 0.005 s in polish. Each
  returned two columns but only completed the one-column master; the next master
  stopped at its wall limit. Public planner/hull enclosures remain broad and do
  not establish a positive planner-hull gap or equality. This screen's public
  bottleneck is pricing time and time allocation, not expensive polishing.
- Multivisit shifted hull instead stopped at the rational-bit limit, after
  19 polish steps and about 0.236 s polish. The existing numerical-QP proposal
  remains relevant to this separate arithmetic issue. Do not conflate time,
  pricing-call, and bit-limit stops.
- Public derived analysis/figures: `research-20260928/computational-results/attempt1/`;
  reproducible analysis script is `research-20260928/computational-results/analyze_attempt1.py`.
  Native enclosures remain numerical/tolerance-qualified. Full-fleet hull
  mixtures are not individual operational schedules. Any offline postprocessing
  must be timed separately and cannot change the recorded baseline outcomes.
- A closed-form two-column calculation on the four public cold pools reduces
  this run's mixture upper bounds by about 37–69 cost units, with about 0.1 s
  measured per-pool postprocessing (excluding imports/case construction/output).
  Physical columns and the new exact stored-number mixtures replayed. Saved
  global lower bounds are unchanged; this is additional analysis, not baseline
  timing, a physical fleet, a global optimum, or a replacement for stronger
  compatible historical bounds. It supports reserving a final master step.
- Public `scientific_evidence.zip` contains 101 original scientific JSON files
  (263,156 bytes); its selection manifest records all included/omitted hashes.
  No raw logs/JSONL were published. The complete private archive remains available.
- Results are published at 967f603; SVG export whitespace was corrected at aa7442b
  without changing figure content or scientific data. Full CI 36381206518
  completed SUCCESS after that correction. The final handoff/Doc-receipt backup
  is documentation only; inspect any newer CI once at the next follow-up.
- Google Doc updated ONCE with “First computational screen — findings and next
  experiment (28 September 2026)”. Saved-to-Drive and exact prior-export prefix
  preservation were verified by Luna and root (99,374 to 102,109 bytes).
  After Markdown SHA 7c822028b4b860307924206f147037395f81032d975600b7f0516eb28b5bbee1.
  Public receipt: `research-20260928/agent-notes/google-doc-screen-results/`;
  full exports remain private in the outer `research-20260928/google-doc-screen-results/`.
  Do not append this milestone again. PR56 description now reflects the completed
  screen and remains draft/unmerged. Hourly follow-ups continue.

## Next bounded work package

Use the measured bottlenecks to design and implement a separate feasible-pool
reuse mode and reserve time for processing a newly returned column. The current
strict certified-predecessor arm stays unchanged. A bounded predecessor can
supply physically replayed complete-fleet columns, but never transfer its old
market weights, duals, or lower certificate as new-market evidence. Preserve
physical/source/extraction identities, unique keys, all preparation costs and
fresh global pricing. Use focused tests for the changed admission/budget logic;
reuse existing physical qualification rather than starting another audit campaign.
Specify/freeze a matched development pilot before execution, within the standing
one serial job / one CPU / 8 GB / two-hour ceiling, no automatic retries, excluding
`scaglione-compute-01`. Do not alter other projects or held jobs. Improve the
restricted QP separately where the arithmetic limit matters, using the existing
standalone helper and exact replay/global-bound checks. No larger sweep or ML
training should precede this measured solver work and retained/retrieval baselines.

Roadmap: `doc/COMPUTATIONAL_RESEARCH_ROADMAP_20260928.md`. The six-reference learned
proposal review, 20-base public inventory and Eberbach 105-service input plan are
under `research-20260928/computational-design/`. The LaTeX scaffold is preliminary;
the user's manuscript critique still governs the next draft. No submission or
PR merge. No protected A6/B3/confirmation outcomes, private GIRO publication or
reset-credit redemption. Routine work needs no approval; flag major scientific,
resource or data-release decisions. Back up useful milestones and append verified
consolidated findings to the original Google Doc, preserving history/visuals.

### Historical delivered first draft (superseded as active direction)

### Delivered first draft checkpoint

27 September 2026. The journal-oriented first-draft objective is complete for
expert user review. No journal submission or PR merge has occurred. Keep routine
future work on GPT-6 Sol and Luna Max; Astra manages scientific decisions.

- Reviewed draft0.5: 27pages,8figures,5tables. Canonical PDF and the named
  output/pdf/egg-journal-working-draft-v05-reviewed.pdf are byte-identical to
  the accepted r2candidate: SHA256
  8c8192c6259b5294449c655047313f7799ee1aa74092fc669748362bbfdad8eb,
  1954122bytes. Reviewedv04 is preserved unchanged. Editable manuscript SHA
  a97a7f9267d9aa69fdd5d9975bf5282eda47f0aaa10760d270ef86c509f3c88e.
- Final independent science/layout review passes all27pages, with pages1–6
  rechecked after the abstract correction. All five numerical intervals round
  outward. No actionable claim/layout issues remain for user review. See
  research-20260927/agent-notes/manuscript-v05-final-review/ and
  paper/RELEASE_V05_20260927.json. This is not journal-submission clearance.
- Artifact release commit10d3381ea725ae893cadbf574a220bbb0157c704 is published
  on codex/journal-research-20260927. PR56 description is current, draft/unmerged.
  CI36358582888 passed the complete CBC suite and frozen journal reconstruction.
  Evidence backup0ce36c184a5c9725462694dfe376d7c75a0ecb43 also passed CI.
- Original GoogleDoc now has one 'Reviewed research draft0.5' milestone.
  SavedtoDrive; before92478bytes are an exact prefix of after94931bytes.
  After SHA256ac33ad4d498ed47ba0de3c8e5a03e146cafe9b543c52ac4e0000662420556dcd.
  Exact heading spacing and verification are recorded under
  research-20260927/agent-notes/google-doc-v05-final-release/.
  Full before/after exports stay outside public Git in the outer workspace.
- Job559907 is COMPLETED0:0,9m36s. Conditional numerical reconstruction PASS;
  strict protocol FAIL; NO OVERALL PASS. Hull polishing5.190904918592423s
  exceeded the frozen cumulative5s cap. Only off-protocol secondary reporting
  is allowed. Signed public gap remains unresolved at five; positive regret
  belongs only to the named bounded incumbent, not a proven physical optimum.
  No retrospective waiver, third attempt, larger budget or new campaign.
- Sealed v2 review manifest2edb2a60a1efdaf37159d6934e317700953e5013284517d5139fc9a18e726e61;
  full reportdc1b176371cd5295d9bfcfd562b7cb69aaa8c3026c5c3a344a023d83a8027598.
  Execution sourcee23a653; raw manifest
  68032692ea5c5b349115bd6bd64740f0bd799fac9a8a4dcdf09462a844901cf9.
  Public subset retains all scientific bytes and declares only three whole
  licensing-only stdout omissions. Complete local/cluster archives remain.
  See doc/SISTIG_NONLINEAR_V2_SECONDARY_REPORTING_20260927.md for scope and
  fresh-output/public-copy reproduction. Never overwrite sealed evidence.
- Exact ideal depot15 minimum fleet2 and flat enclosure independently pass;
  separate exact ideal nonlinear bounds give424.365880667204... <= CH <= D
  <=512.7694256264009... without determining a gap. Depot16 numerical upper
  stays distinct. Do not combine ideal and native bounds into an exact claim.
- Fresh queue23:13:54UTC showed no active EGG jobs; other-project held jobs were
  untouched. Hourly heartbeatadvance-egg-journal-research is now PAUSED and was
  verified in its saved config. Do not restart automatic research on completion.
  No reset credits were used. No further monitoring is needed for these runs.
- Next substantial decision belongs to the user: pursue an analytical/methods
  journal framing, or invest in calibrated operational evidence before submission.
  The draft supports existence and declared-model claims, not prevalence,
  operational savings, daily recurrence, stochastic reliability or deployment.
  Preserve private GIRO, protected outcomes, all failed attempts and other projects.
  Future CPU jobs must exclude scaglione-compute-01 if separately authorized.

## Objective and completion standard

Produce an excellent journal-oriented first draft with a defensible contribution,
source-verified related work, explicit physical and economic assumptions,
reproducible experiments and publication-quality figures/tables. Completion means
a coherent rendered manuscript, all claimed results traceable to frozen sources
and independent checks, a reviewer-style audit with no major unresolved claim
errors, and a clear register of remaining submission limitations. Do not equate
a long draft or many experiments with journal readiness.

## Current source of truth

- Worktree: `/Users/nadan/Documents/ChatGPT/egg/journal-research-work`.
- Branch: `codex/journal-research-20260927`, initially based on reviewed PR55
  head `e2a98a25167aa4af3b5dfdc01fbce2026cab13a6`.
- Repository: https://github.com/ndandnd/egg.
- Earlier checkpoint: `../review-20260921/IMPLEMENTATION_SPRINT.md`.
- Local sprint evidence: `../research-20260927/`.
- Research document: https://docs.google.com/document/d/1NmPC_qo_uOnA48dV6Ibhs3Pj9EgOD-oJTBuVi41p6bg/edit?tab=t.0.
- Local working solver: `../.research-venv-repaired-1176/bin/python`.
- Main is still `7e18463`; PR52–55 are draft research branches. Inspect current
  refs and receipts before assuming any integration or new result.

## Completed 27 September milestones

The fully replenished cyclic construction and all 24 fixed parameter cases
passed an independent exact arithmetic and physical audit (10 corruption
controls). Nominal D=97, CH=94.8875, gap=2.1125; both fleet structures buy 30 kWh.
The frozen source is 7bf913a and the immutable results are in
`result/cyclic_gap/20260927-attempt1`.

The harder reuse frontier at frozen 7d3d764 attempted all 45 comparison cells
and 15 references. Exactly 44 cells certified; the cold return-state failure
remains failed. An independent exact pricing DP and rational Fenchel lower
bounds support all 44 successful certificates, while physical witnesses retain
numerical replay tolerances. All 19 corruption controls pass. A prospective
logging-only repair at 78bb4c0 fixes mutable tangent snapshots; all 244 original
files remain unchanged. Results and reviews are in
`result/reuse_frontier/20260927-attempt1`.

Across 12 warm transitions, retained columns need 17 clean calls. Always paying
for a full-pricing proposal plus mandatory verification has a floor of 24 calls,
so that architecture cannot win this metric on the observed trajectory. Do not
launch a learner without a different explicit useful-work hypothesis.

Two exact extensions now have completed non-author audits. Robustness at
`bd022ac32ef680446ee17bc4400843a764acb9f6` reproduces all 16 cases: 9 positive,
6 zero and 1 infeasible. The joint reserve-1/efficiency-19/20/early-12 kW case
has gap 94249/28880 using one 30 kW terminal connector. Its 8/19 grid-kWh early
headroom supports a strict-inequality neighborhood argument. The unchanged
10 kW early hardware loses the one-bus branch under either reserve or loss;
this negative control remains central. The nominal terminal-power threshold
is 23.5 kW. All 22 corruption controls are rejected. Raw
`result/cyclic_robustness/20260927-attempt1/results.json` SHA-256 is
`3d5c20a39b2c7176b6ece22bbeb464a42ea7b3bc58498c0959e227469e25ed29`.

Replication at `ce84e9e62b8e3f33d32010d381fd845415eff458` independently passes
all 86 sizes, 6,448 continuous branch minima and 88 physical optima, preserving
both ties. Its 21 corruption controls are rejected. Along n=40k+1, gap is
169/(80n) while whole-operator own-price regret approaches 351/40; regret per
used bus and relative regret vanish. Multiples of 40 have zero gap and regret.
Demand, charging resources and supply curvature scale together. This is one
price-taking operator, not strategic behavior or independent firms. Raw
`result/cyclic_replication/20260927-attempt1/results.json` SHA-256 is
`87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a`.
Both extension folders have portable reviewers and separate review manifests;
neither raw attempt was retried or rewritten. They do not qualify a native
optimizer or demonstrate operational prevalence.

The source matrix, editable manuscript and five scientific figures are under
`paper/`. Working manuscript 0.2 is being prepared; its rendered review and
visual QA are not complete. The existing reviewed
`output/pdf/egg-journal-working-draft.pdf` and manuscript-review hash belong to
version 0.1. PR56's c0f83f0 hosted CI passed 826 tests; that historical result
does not certify later source heads. The excellent-first-draft goal remains
active and incomplete: native-model qualification, operational evidence,
economic interpretation and renewed review still need work.

## Current priorities

1. Finish preflight repairs and independent implementation review of the native
   terminal-recharge prototype. No native optimizer qualification has run.
   Preserve one common physical builder, directed movement ownership, exact
   event windows and one-connector replay; avoid terminal service markers.
   Freeze the corrected source/tests/runner/protocol before executing the
   bounded 15-control synthetic qualification. Independently audit numerical
   witnesses, bounds and backend identity before moving to an operational case.
2. Complete the local-only source-faithful GIRO microcase extraction and
   directed/time-dependent deadhead coverage audit. Preserve raw provenance
   outside Git; do not describe this subset as a complete named weekday or
   missing movements as free. A known-arc subgraph must be explicit.
3. Freeze a bounded operational microcase protocol before solving. Separate
   source service energy from modeled deadhead energy, battery/charger choices,
   operating costs and supply curvature. Start with falsification controls;
   launch scoped Unicorn jobs only when implementation and input gates pass.
4. The Parmentier companion benchmark is pinned and locally inspected. It is
   useful for independent parser/route feasibility, but its abstract units and
   source-model simplifications are not calibrated bus-operation evidence.
   Local intake is `../research-20260927/agent-notes/public-data/`; do not publish
   raw inputs while data-specific redistribution terms remain unresolved.
5. Integrate the audited replication/robustness evidence into manuscript 0.2,
   regenerate figures with `paper/make_figures.py` and
   `paper/make_extension_figures.py`, then render and review every revised page.
   Preserve tie/normalization and changed-hardware qualifications. Add verified
   operational findings when available; complete reviewer audits and CI at the
   actual published head. Keep GitHub, this file and the research document
   current at meaningful milestones without declaring an unreviewed PDF ready.

## Autonomous work loop

On each continuation, read this file, the newest research journal and active
launch receipts. Check whether a researcher already owns the same operation;
do not duplicate an active run, recovery, document write or submission. Delegate
bounded independent work where useful, using Luna Max for simple audits when
appropriate and the main model for proof/design/synthesis. Freeze hypotheses,
grid, budgets and analysis before scientific execution. Independently review
nontrivial results before advancing claims. Keep failed attempts immutable.

Commit and push meaningful reviewed milestones to the branch; use draft PRs
and passing CI for review. Never force-push or publish private source material.
Append dated meaningful findings to the Google Doc, preserving previous text
and figures. Keep the manuscript and continuation current in Git. If document
access is unavailable, save the exact pending update locally and continue
unaffected work; do not claim it was published.

## Unicorn monitoring and execution

Use `unicorn2` with BatchMode and a login shell; source
`/etc/profile.d/slurm.sh`. Read the live resource policy at
`/home/nc437/ladder-lite/SCAGLIONE_RESOURCE_POLICY.md` before submission.
One compact queue check per scheduled wake is enough. Match EGG by registered
job IDs and WorkDir/Command paths, not job name alone. Use owner/date/job-scoped
`sacct` plus output receipts to resolve jobs absent from `squeue`.

The initial 27 September 15:11 UTC snapshot had no running user jobs and no
active EGG job; 22 queue entries belonged to held ladder-lite campaigns.
Leave those and other projects' jobs untouched. Exclude `scaglione-compute-01`.
Non-checkpointable solver work uses appropriate resources and no false resume
claim. Read `doc/UNICORN_RUNBOOK.md`; published-main execution is its default.
Any use of an isolated published research commit must be explicitly documented
as a scoped implementation choice, never silently mixed with protected campaigns.
Start with bounded qualifications; size later campaigns from measured runtime,
memory, scientific value and current capacity. Do not occupy CPUs with frequent
polling or login-node optimization. Record commit, input/runtime hashes, Slurm
receipt, resources, output manifest and actual terminal status.

## Scientific and confidentiality boundaries

Keep A6, B3 factor and confirmation outcomes unscored until their existing
prospective evidence/recovery gates are valid. Broad autonomy is not a reason
to bypass holdout or provenance rules. Never retry a spent recovery claim or
touch PR45. Use fresh synthetic development designs for new work.

GIRO use is authorized for local research. Raw C1 Internal workbooks, emails,
contacts and sensitive extracts must not enter public GitHub or the shared
research document. Record raw fingerprints and translation evidence locally;
publish only appropriate methodology and non-sensitive aggregates. Treat
historical solved duties as a feasible reference, not observed optimization
objectives or independent optimality evidence.

## Decisions to flag

Flag only material changes to the paper's central claim, evidence undermining
the approach, private-data release, unusually large resource commitments, or
actions outside authorized scope. Make routine design, code, writing and backup
choices directly. Keep working on independent items while a major decision is
pending. Do not redeem reset credits without the per-credit confirmation
required by the account tool.

The hourly heartbeat continues research and monitors jobs. Stay quiet on
unchanged queue state; report meaningful findings, failures or major decisions.
After the first draft passes the completion standard, stop launching new
campaigns, report readiness and monitor only already-authorized active work.

## Latest rendering update

Working draft 0.2 is now rendered: 14 pages, five figures, PDF SHA-256
`1cf8ed050ad5b6d142353996eb299c6d9578a92d7f1f3cd320ed5c08e9af4697`.
Author all-page layout QA passed; exact extension artifacts have separate
non-author audits. This supersedes the earlier rendering-pending entry.
Operational/native scientific gates remain open, as does the research goal.

## Latest native execution update

The first frozen native CBC qualification has completed at source
`d37878392f0848d34f28921c97b6e8d8e6533a77`: 12/15 passed, three witness
extraction/replay exceptions, 23.5736 seconds. Preserve all raw files under
`result/native_recharge/20260927-attempt1` and its manifest. This supersedes the
prior unrun status. Native qualification remains **failed**, with author diagnosis
and independent review in progress. No cluster or operational solve is admitted
by partial success. Any corrected run needs a new freeze and separate output.

## Latest V2 native result (independent audit pending)

The separately frozen V2 at `997575d049a66d952a0cb8d79f974f7ba5f4ccf0`
passed all 15 controls in `result/native_recharge/20260927-attempt2`:
12 certificates, three expected infeasibilities, 30 native calls, 33.7343s.
Its 107 raw files and manifest are immutable. Independent variable/session/bound
review is in progress; do not dispatch cluster qualification before that passes.
Attempt1 remains 12/15. The cluster protocol and one-CPU/4GB/20-minute script
are prepared and reviewed but not yet submitted. Read their explicit gates.

## V2 audit gate passed; next explicit action

Independent V2 result audit passed: 27 raw incumbents/1,030 variables, all model
constraint classes, 27 saved physical witness instances and all objective/bound
checks; 16 deliberate corruptions rejected. This supersedes the pending-audit
entry and admits the separately protocolled bounded GRB qualification only.
The first native attempt remains FAILED 12/15. No operational case is admitted.
The private 17-service pair has off-depot recharge/missing movement blockers;
public Sistig/ Figshare data-only intake is underway locally. Manuscript 0.3 is
being edited; the reviewed/shareable PDF remains 0.2 until rerendered and checked.

## GRB replication completed and independently audited

Unicorn job **557318** ran from published `24c7e4ef30777700e4ea17ddfaacae2de92155ce`
in `/home/nc437/egg-journal-native-20260927`. It completed `0:0` on
`snavely-cpu-01` in 39 seconds, batch MaxRSS 74.50 MB, one CPU; reserved-node
exclusion was confirmed before launch. All 15 unchanged controls passed (12
numerical certificates and three expected infeasibilities), 30 native calls,
26.0397 seconds controller elapsed. **Do not resubmit this completed attempt.**

Independent review of the complete immutable 107-file archive passed: 27 raw
incumbents/1,030 variables, 27 independently minimized finite objectives, three
analytical infeasibilities, 62 sessions, 217 SOC events, 18 rejected corruptions
including backend substitution. Backend was GRB, not fallback. This qualifies
the tested native physics on two backends, not an operational or scaling claim.
Original CBC attempt1 remains failed 12/15. Full cluster evidence and license
stdout are retained outside Git in the local research archive; the public copy
will explicitly disclose stdout omissions without modifying numerical files.

CI also passed at execution commit `24c7e4e`, run 36332937884, including the
new frozen-evidence audit step. Next: independently review/freeze/run the separate
19-control half-minute extension gate, then review/freeze the native convex-hull
qualification. The public 37-service Hildenbrand case is data-only intake;
modeled energy assumptions and two separate one-depot variants are explicit.
No native optimizer has yet been run on those new timing/hull/public artifacts.

## Active local timing qualification

The 19-control timing gate was independently reviewed and frozen/published at
`46fd6af573a240d54abb8ea8d7cf7b79cc0af0ee`. Its first local CBC execution is
active in `result/native_halfminute/20260927-attempt1` (controller tool session
88468). Inspect `summary.json` and receipts before doing anything; do not repeat
or overwrite. The new native source retains original integer control identities
within its explicit bounded timestamp domain. Pure preflight passed 79 tests
with solver imports blocked plus independent lattice/adjacent-float checks.
Native hull source has been authored but remains under independent preflight,
with no hull solve. Public-case intake is undergoing a separate non-author
source/arithmetic review; no operational solver execution has occurred.

### Timing qualification completed; independent result review pending

The first half-minute CBC gate at `46fd6af573a240d54abb8ea8d7cf7b79cc0af0ee`
completed all 19 controls successfully (15 certificates, four expected
infeasibilities). Its raw attempt is manifested under
`result/native_halfminute/20260927-attempt1`; source hashes are unchanged.
This supersedes the active-session entry. Do not rerun. Independent artifact
review must pass before the timing extension supports a timetable result.

## Public intake admitted; compact representation under development

The complete37-service Sistig input is prepared in
`data/public/sistig_26088190_v1/hildenbrand_native_cases.json` and independently
reconstructed from the original public archive. Its two one-depot variants
preserve all mandatory services and the complete directed travel data; all
2,705 emitted modes and5,226 legs match independent source arithmetic. Separate
37-bus constructive references satisfy the single-connector/full-replenishment
policy, but are not optimized. See the protocol and independent source note
under `research-20260927/agent-notes/sistig-independent/` inside this worktree.

Do not blindly launch the vehicle-indexed model on this input: candidate charge
variables number751,914/705,294 and the builder repeatedly scans that large set.
Root is developing `src/egglab/native_pathflow.py`, an equivalent service-DAG
path formulation with20,322/19,062 charging variables. It is unqualified; no
optimizer has run. Its equivalence proof, pure tests and prospective controls
must pass before any source freeze/solve. It preserves the full declared graph
and must not claim equal LP relaxations or runtime improvement before testing.
The original physical module/source remains unchanged by this new formulation.

## Active native hull gate

The native hull module/runner/tests/design/protocol and their physical
dependencies passed independent preflight (46 pure/fake tests and targeted
corruption/arithmetic checks) and were published at
`f549100587cdf561c978e145e73e86dbadc9f27e`. The first8-control CBC run is
active under `result/native_hull/20260927-attempt1`. Inspect its supervisor
receipt/summary before any action; never duplicate or overwrite. The retained
predecessor admission bug was corrected before this first freeze/run; its failed
preflight reproducer and repair are documented. No operational solve is active.

### Native hull first execution failed qualification

The8-cell native hull attempt at `f549100587cdf561c978e145e73e86dbadc9f27e`
is complete, not active:2 cells certified,4 exhausted the64-master-call cap,
and 2 retained successor states correctly blocked after their predecessor failed.
Supervisor exit1, no outer timeout,14.2354s. Raw evidence and all failure work
are manifested in `result/native_hull/20260927-attempt1`; do not rerun or rewrite.
The physical timing gate independently passed all19 controls; this new failure
concerns the separate hull restricted-master refinement and is under diagnosis.
No timetable solver or hull scientific claim is admitted by partial success.

Independent timing review is now complete and PASS (all135 raw files and19
controls;22 corruption checks). Final derived review is packaged. The hull V1
failure is a diagnosed repeated-tangent/master precision stall; author is
preparing V2 with bounded exact pairwise simplex polishing and streamed bestUB,
while a separate reviewer audits V1. No rerun before new review/freeze.
Root compact path-flow module and 20-control gate are ready for independent
preflight, including a three-service/two-depot-visit control. No compact solve.
The public-case figure is being generated; manuscript0.3 remains unrendered.

## Compact gate passed; corrected hull gate active

The compact twenty-cell first attempt at published `ebb146e` completed with
20/20 admitted controls (16 numerical certificates and four expected
infeasibilities), 35 native calls, 24.5333 seconds. Its 142 raw files and
720,384 bytes are manifested and backed up in commit `186c987`; independent
flat-mapping result audit is active. Do not rerun or change raw files.

Hull V2 passed independent preflight after strict polishing-deadline and
phase-accounting checks were added. The published execution freeze is
`186c9876805d5096632786c5504f507847a5201f`; the corrected eight-cell run is
active at `result/native_hull/20260927-attempt2`. It retains all scientific
controls, original native oracle and existing caps/tolerances. Check the
supervisor receipt before any action. The original V1 failure remains archived.

A two-cell complete public-timetable pricing pilot is under separate preflight:
`src/experiments/sistig_pricing_pilot.py`. No public optimizer has run. Require
completed compact result audit and published pilot protocol/source freeze first.
Prospective allocation is one CPU, 8 GB, 12 minutes, reserved node excluded.
A live queue check found available default-partition capacity and only the
existing held user jobs; they remain untouched. No new EGG cluster job yet.

Participant normalization has independently passed all 88 archived optimum
records, including both ties. The alternative institution explicitly grants
one early and one terminal connector to each A/B-pair owner. Individual regret
is at most 20/n while its sum reproduces the whole-fleet regret; no general
shared-resource-game or anti-convexification claim follows. Manuscript source
0.3 incorporates this result; the rendered/reviewed PDF remains 0.2 pending
full layout verification. Google Doc has the saved public/timing/hull milestone
with prior content preserved (71,160 characters at verification).

### Both next gates completed

The compact first attempt has independent PASS (all142 raw files,31 raw
incumbents/589 values,68 sessions/252 SOC events,25 corruptions rejected).
Hull V2 attempt2 has completed8/8 certificates,36 native calls and9 exact
stored-number polishing transfers; supervisor exit0/no timeout in22.4423s.
Its62 raw files905,863 bytes are manifested; independent result audit remains
active. Do not duplicate either run. The public pilot is under source review,
with added unique-phase/identity/native-bound admission checks and explicit
cluster dependency hashes. No public job is submitted yet.

### Reviewed manuscript 0.3 checkpoint

The17-page/six-figure PDF0.3 passed independent all-page visual QA; its SHA-256
is `fac524aff668c2c1d81d027bf67a74894ad943953bf0638ca09d0ab51d035500`.
It now supersedes reviewedPDF0.2, with both prior hashes/history retained.
See `paper/MANUSCRIPT_V03_LAYOUT_REVIEW_20260927.md`. It explicitly labels the
public37-bus energy references as modeled and not optimized, and the new
reserved-pair participant result as an alternative stated institution.
This is a working draft, not submission-ready. A separate quadratic regret-radius
bound is undergoing two independent mathematical checks and is not in thisPDF.

The root public-pilot runner's five pure admission tests pass; final review
includes full240s scientificroutine deadline,255s externalchildcap, exact
backend/input identities, native-bound reconstruction and one ordered phase.
Slurm wrapper records a560soutercap supervisorreceipt. No public run yet.
The compact hull integration is separately authored with an explicit injected
oracle and distinct retained-state identity; it has no optimizer run and awaits
independent preflight. Do not confuse it with the already executed indexedV2.

## ACTIVE PUBLIC PILOT — job 557543

The independently reviewed complete public pricing pilot is now submitted,
not merely planned. Source freeze `282e00b80b6fd9457006429b089269b2a9e2be92`.
Unicorn isolated detached checkout `/home/nc437/egg-journal-public-20260927`.
Job557543, `egg-sistig-pilot`, default_partition, one CPU/8GB/12minutes,
no requeue. Effective `ExcNodeList=scaglione-compute-01` verified by scontrol.
Initial state PENDING(Priority); no user action required. Do not resubmit.
Sentinel `public-pricing-submission-20260927/{INTENT,SUBMITTED,SCONTROL}.txt`
and local outer `research-20260927/cluster/public-submission.txt` preserve
submission evidence. Expected unique result path:
`result/sistig_pricing/20260927-grb-job557543-attempt1`.

Monitor only this job with squeue/sacct and inspect result/supervisor receipts;
a queue disappearance does not prove success. After completion, manifest the
entire raw archive before transfer/audit. Keep complete license-bearing stdout
local; public copy may omit only independently identified sensitive full stdout
files with original manifest+explicit omission hashes. Do not modify numeric,
input, event or result bytes. Independent reviewer is preparing audit under
`research-20260927/agent-notes/sistig-pricing-review-preparation/` in this worktree.
No public result or economic effect is known at submission.

The new quadratic regret-radius derivation passed two independent mathematical
reviews, including PSD/null directions, arbitrary physical schedules, boundary
loads and all88 archived replication optima. It is an explanatory bound, not a
novelty claim. Keep manuscriptPDF0.3 unchanged until the next coherent scientific
revision and layout pass. GoogleDoc milestone is SavedtoDrive,73,585characters;
all previous content is preserved (only final blank-line normalization changed).

### Compact hull integration is executing

All79 pure tests and independent integration preflight passed, preserving the
original eight scientific controls and budgets. Published source freeze
`72a1f715e9e6714746f9c0638c50d2cba6bfcfdb`. First compact-hull run is now
active at `result/native_pathflow_hull/20260927-attempt1`; local supervisor
session81493. Do not duplicate or modify any of its hashed physical/compact/hull
sources until it completes and is manifested. Independent reviewer is preparing
its flat-variable audit. IndexedV2's eight certificates already passed the
complete independent audit, which is published at72a1f71;31 corruptions rejected.

Public job557543 is running, last seen6m28s. The first cell completed bounded
in186.278s: nativeFEASIBLE180.012s, lower237.14148764071234,
upper408.5331368838794, two buses,1042.665679419397 gridkWh. Do not call it
optimal; full independent result audit remains required. Second cell has no
reported outcome yet. A possible next mathematical strengthening is the
full-replenishment aggregate energy balance (service+selectedtravel=eta*grid);
this needs a separately reviewed/frozen revision, never an in-attempt change.
An exact matching relaxation for flat-price lower bounds is also under design.

## Completed public pilot and compact hull audit — 27 September 2026

This checkpoint supersedes the active-job descriptions immediately above.
There is no active EGG solver job. Public job557543 COMPLETED 0:0 in6m35s,
397140KiB peak batch RSS, oneCPU/8GB, excluded node respected. Frozen source
282e00b80b6fd9457006429b089269b2a9e2be92 was not changed or rerun.
Both full37-service cells are independently audited bounded/FEASIBLE results:
depot15 [237.14148764071234,408.5331368838794], depot16
[232.14633164554616,433.74608621721006]. Both have two-bus physical witnesses,
with1042.665679419397/1168.73042608605 gridkWh. Neither proves optimality.
The audit reconstructed42,297 raw values,41 charging sessions and 231 SOC events;
16 corruption controls were rejected. Complete17-file external archive verified.
The public copy retains15 original scientific files byte-for-byte, the unchanged
raw manifest and explicit omission hashes for two license-bearing whole stdout
files. PUBLIC_COPY_VERIFICATION.json separately verifies final assembled bytes.
No input, numerical result, event or failure is omitted or edited.

Compact hull attempt1 at frozen72a1f71 completed8/8 certificates and independently
passed:36 native calls (21 pricing/15 masters),9 exact pairwise transfers,
24 checks,45 sessions/171 SOC events,42 corruption controls. All62 original
files750,529 bytes remain unchanged. Some ideal-target differences are about
3e-14 under the disclosed native floating witness policy; not exact physical
certificates. Public study has no hull/planner/gap result yet.

Next, separately version and independently review aggregate full-replenishment
energy inequalities before20-control and8-hull-control requalification. The
band must account for stored coefficient assembly roundoff, with unchanged
physical replay and admission tolerances. An exact DAG matching relaxation for
flat prices is also under mathematical design. No V2 or matching experiment has
run. Keep first attempts intact. The broader public nonlinear study remains a
candidate design until pricing-bound quality and prospective protocol gates
are resolved. No user decision or exceptional compute authorization is needed.

Recent CI runs stopped before pytest on trailing whitespace in the generated
public SVG. Its generator now normalizes those insignificant spaces; the saved
SVG passed XML/token semantic equivalence and PNG/reviewedPDF bytes are unchanged.
A fresh branch CI will determine downstream status; do not report those earlier
runs as passing. ReviewedPDF0.3 remains the current17-page artifact; manuscript
source0.4 is in preparation.


### Exact matching attempt1 completed; energy-V2 preflight repair

Published matching freeze3014d04a043d5c6b99433fc5458271a3076d16b5 and two
independent preflight reviews preceded the first public calculation at
`result/sistig_matching/20260927-attempt1`. Both cases completed: exact ideal
stored-input lower bounds display301.3153438838777/305.6338078838777, each
with one relaxed path. No physical-feasibility claim follows. Exactly two
algorithm calls,0.204274s complete routine,0.280112s supervisor,exit0/no timeout;
all original output files manifested. Independent no-author-import result audit
is active. Do not rerun. These are separate post-pilot diagnostics, not changes
to the original native intervals. Source, protocol and reviews are backed up.

Energy V2 implementation is still in preflight. Reviewer caught a legitimate
Python-MIP zero-constant expression alias edge case; a scoped guard/normalization
repair and pure regression are being made before any V2 optimizer. All earlier
artifacts are intact. Next20+8 qualifications still require final preflight and
published source freeze. Public pilot2 is not submitted. Both existing EGG
cluster jobs are complete; no active EGG optimization.

GoogleDoc milestone saved75953characters with prior73585-character content
preserved after trailing-blank normalization; new heading appears once. Evidence
head e6ded66 passed full hosted CI run36337297088. Source manuscript0.4 now
adds both audited public outcomes, a seventh figure of returned physical
witnesses (independent figure review pending), and explicitly states flat-price
F is an exact zero-gap control. ReviewedPDF0.3 remains unchanged.


### Energy-band V2 first qualification: 19/20; downstream gates held

Final independent preflight PASS preceded published freeze
66b7054510a8b90471d6abe07d32a9f7f509182d. The local 20-control attempt2
at `result/native_pathflow/20260927-attempt2` completed with 19 passes and one
exception in joint_planner: positive charge on an unselected movement during
physical extraction after the second native call. All raw outputs, including
failed-cell events, exception and traceback, are retained and manifested.
Do not rerun or replace this attempt. Independent audit and read-only author
diagnosis are active. The eight compact-hull V2 controls and public pilot2 are
held; no cluster job submitted. No user decision needed for this technical
diagnosis. Matching attempt1 independent exact-certificate audit has passed;
the review bundle is separate and all original files are unchanged.


### Latest user preference: lower token cost and manager-led delegation

User explicitly requests Luna Max and GPT-6 Sol for easier tasks, with the
primary agent acting as manager. Use gpt-6-luna with max reasoning for routine
audit checks, documentation, layout and monitoring; gpt-6-sol for bounded
implementation and analysis. Give concise self-contained handoffs, reuse
workers, avoid redundant reviews/rereads, and reserve Astra for hard theory or
major scientific decisions. Do not automatically redeem any reset credit.
The hourly heartbeat was updated to preserve this routing preference and work
on one bounded package per wakeup; monitoring cadence and important-decision
alerts remain unchanged. Current Astra workers are finishing only their
already active bounded evidence audit and failure diagnosis, then stopping.

Source manuscript0.4 contains the method/compact-model and robust-neighborhood
appendices, an evidence table and updated abstract. CandidatePDF is
output/pdf/egg-journal-working-draft-v04-candidate.pdf; reviewedPDF0.3 remains
unchanged. A separate equation renderer refreshes nine current equations
without regenerating scientific figures. Fresh scientific/layout review is
required before promoting the candidate. Figure 7 itself passed independent
review. Sol6 should review the new method/appendices and numerical extraction
repair design; LunaMax should handle layout and status/docs.


### Audited V2 failure archived; lower-cost worker handoff

Independent energy-V2 attempt2 audit is complete: PARTIAL/FAIL, downstream
admission=false. Fifteen certified plus four expected infeasible controls
passed; joint_planner failed. All142 raw files unchanged;30 nativecalls,
26snapshots/479variables,25witnesses/54sessions/202SOCevents,37 corruption
controls checked. Reviewmanifest
b143fb9d42342b10f50c04bfa539df40a01d877cf00b3829654e30fa1350341d.
Astra reviewer finished and stopped. The other Astra author was interrupted
after read-only diagnosis. No Astra execution worker remains active.

Sol6 worker sol6_numerical_repair now owns a prospective orphan-charge policy
design and focused source0.4method/AppendixA/B scientific check; no optimizer
or implementation before independent design review. LunaMax worker
operational_data_audit finishes the one-bus structural proof review and the
candidate nonlinear budget note (the11hour envelope is a proposal, not an
admitted campaign). LunaMax worker luna_draft_record owns candidatePDFfullpage
QA, README reproduction instructions and the next GoogleDoc milestone. Root
manages publication and major decisions. Reuse these workers if available;
otherwise read their saved deliverables before dispatching bounded replacements.
Matching/figure/manuscript milestone is published at e3c3c48.


### Manager checkpoint: manuscript review and document update

Previous goal turn made progress: published matching/figure/manuscript checkpoint
e3c3c48 and independently audited failed energy-band archive b77f272; persisted
LunaMax/Sol6 routing in the hourly automation. Current worker handles confirmed
live; a fresh scoped Unicorn check found no EGG job active. No jobs restarted.

Sol6's focused review of source0.4abstract/method/evidenceTable3/AppendicesA/B
found no blocking scientific inconsistency. Its prospective orphan projection
design is written but awaits LunaMax independent review before implementation.
LunaMax visual review of the22-page candidate found no clipping/overlap/glyph
or figure defects, but references begin awkwardly acrosspages21/22. A separate
v04-r2 pagination candidate and review are now assigned; no oldPDFisreplaced.
GoogleDoc appended unique heading “Verified manuscript and qualification update
— 27 September 2026” and showed Saved to Drive. The worker verified the append
and heading; it did not capture a complete before/after document comparison,
so full-document byte/content integrity is not claimed for this UI update.
PR56 body now reflects exact matching, audited19/20failedgate, source0.4and
remaining nonlinear study.

The failed energy-V2 archival auditor was independently rerun with no optimizer
and reproduced its explicit PARTIAL/FAIL verdict and37corruption rejections;
CI now includes this archived-failure check without changing gate admission.
Sol6 may design a cardinality-constrained matching bound conditional on the
one-bus obstruction review, without execution. Repairimplementation remains
its priority once the independent design review passes. No broad11-hour
nonlinear campaign is admitted; candidate scope/resource gates still need
manager review.


### Reviewed working manuscript0.4 and next implementation ownership

The canonical PDF now contains reviewed working version0.4:22pages,7figures,
SHA256 acae4e1bc915fdf7e7a4cafcd997b91aa6941afe73a9075b37cb6b50514663ca.
Named reviewed copy and two earlier candidates remain separate; PDF0.3remains
in Git history. Source change during promotion is metadata only; other text
matches the R2candidate, pages2–22 are pixel-identical, page1was visually
checked, and all9equation PNGs are unchanged. Sourcehash
454ec4fd010ed06e5609c49e500ca4493a0cd51faf86b533c413e5c4fae3ecf5.
Focused scientific and full-page layout reviews are saved. This is a reviewed
working draft, not completion of the excellent-first-draft goal: the public
nonlinear physical/hull/regret evidence and final scope review remain open.

One-bus proof/review is published3516d45; exactminimumflow design and its
independent mathematical PASS are published2da04c8, alongside conditionalPASS
for the numerical repair design and an explicitly unadmitted candidate
sensitivity budget. Sol6_numerical_repair owns compact extractor/pure tests
and prospectiveattempt 3 protocol; LunaMax operational_data_audit reviews its
stable implementation before any sourcefreeze/optimizer. Sol6_cardinality_bound
is a separate worker implementing newexactflow modules/tests/protocol only.
No public matching calculation before independent code review and published
freeze. No oldrawdata/sourcefixture is rewritten. Current publicpilotcandidate
stillpointsfailedattempt2 and is held; only changeitsgate after a new passed
audit. No EGG clusterjob isactive. Rootownscommit/push/runadmission.


### Candidate implementation backed up; source review still required

Previous goal turn made concrete progress through published reviewedPDF0.4,
one-bus proof, source reviews and worker implementation. Current compact V3
candidate is backed up at b2a5a33; this is NOT qualification admission. Its
48compact and62unchanged indexed pure tests passed, with no optimizer call.
LunaMax operational_data_audit is reviewing the implementation at those hashes;
Sol6_numerical_repair is idle and available for targeted review fixes. Only
after independent preflightPASS should root publish the review/finalfreeze
and run the new exclusive result/native_pathflow/20260927-attempt 3 once.
Use doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_QUALIFICATION_PROTOCOL_20260927.md,
not the older V2protocol. All oldrawattempts remain immutable.
Sol6_cardinality_bound continues its separate pure exact-flow code/protocol.
LunaMax luna_draft_record is appending the reviewedPDF/onebus milestone to the
GoogleDoc with a before/after preservation check when possible.


### Implementation preflight held for focused corrections

Luna's independent review of candidate b2a5a33 passed the 48-test compact
suite but did not admit attempt 3. The shared normalizer can reject N alone
before the full N+O correction ledger is emitted. The compact helper must
record the complete failure ledger first, without changing indexed behavior.
Additional promised pure controls must cover combined interval/session excess,
materialized/replay load differences, nonzero planner objective corrections,
unavailable visits, and specifically V2-to-V3 identity invalidation. Direct
comparison of all20inputs, targets and budgets with attempt2 is still pending.
See NATIVE_PATHFLOW_ORPHAN_CHARGE_IMPLEMENTATION_REVIEW_20260927.md.

Sol6_numerical_repair is working only on these scoped corrections. No optimizer
has run and no new experiment is admitted. The native-hull coordinator still
hard-codes the indexed extraction-policy identity; this is a separate later
integration gate, with its own source manifest and controls, not part of the
current20-control patch. The failed attempt2 archive stays immutable.
Sol6_cardinality_bound continues the independent exact-flow implementation;
LunaMax document worker is completing the next GoogleDoc append.

## Archived checkpoint before GRB hull admission

### Prior checkpoint (superseded)

27 September 2026. Latest published source freeze
`62976f11ecf35c837b0573079892ae5095e846b9`; admitted CBC physical/exact-flow
checkpoint `b502e85` and CBC hull checkpoint `805887d`. Sol 6 handles implementation and analysis; Luna Max handles routine
verification, documentation and monitoring. Astra coordinates and makes major
scientific decisions. The hourly heartbeat preserves this routing. Avoid broad
rereads, redundant tests and idle polling.

- Working manuscript 0.4 remains the reviewed 22-page, seven-figure PDF.
  The first-draft goal is incomplete: matched nonlinear public physical-planner,
  full-hull and own-price-regret evidence and final scope review remain open.
- Compact physical attempt 3 independently passes all 20 CBC controls: 16
  numerical certificates and four expected infeasibilities. Its 35 calls took
  24.707 seconds. Audit covers 31 incumbents, 589 values, 31 physical witnesses
  and 25 corruption controls. Maximum whole-incumbent correction is
  1.2261e-12 kWh against the single 1e-8 ceiling. This qualifies only the
  synthetic compact policy; failed attempt2 is immutable.
- Exact cardinality-flow attempt1 independently passes both 778-arc, full
  37-service certificates, with 14 corruption/omission controls. Ideal stored-input
  lower bounds are 404.924239883878 (depot 15) and 414.394469217211 (depot 16).
  Keep these separate from native numerical upper witnesses; no exact physical
  optimum or gap is established. Both calculations took 0.358 seconds.
- Both sealed audits are in their respective attempt `review/` subtrees. Their
  manifests were verified by the lead. Reproduce auditors that require live
  frozen sources in a checkout of dd5ad16 with later evidence copied in and
  fresh report output paths; never overwrite sealed review reports.
- V3 hull-policy integration passed independent preflight (96 pure tests) and
  is published at 03d1da2f3629e722784e97891a8590060fa676ad. The same eight
  CBC controls ran once: all eight reported certified, 36 native calls,
  12.267 seconds supervised, no timeout or source drift. The original 62 files
  are sealed (manifest c3d9da88195161ddd2c054800e4d0a5944998a03b623730a771e7ce9bbb5644b).
  Independent audit passes all eight, all 21 pricing and 15 master solves,
  mixtures, retained-policy boundaries and 48 corruption controls. Review
  manifest SHA c17175c033921553a9f1d58dc5ddb083e412c2fcde3cb4c71ec639b226091166.
  This qualifies the declared CBC synthetic hull fixtures only. The fake
  fixture change is prospective and does not alter the old frozen source.
- Sol 6 has prepared the separate one-cell nonlinear runner: full depot-15
  case, fixed synthetic curvature, three matched routines, 34-minute total cap.
  Independent preflight passed (13 pure tests), including saved mixture subsets,
  useful complete budget-limited evidence, exact GRB input/budget parity and
  reserved-node exclusion. Runtime caps and inputs remain fixed. It remains
  NOT-YET-QUALIFIED until the two audited GRB stages have passed.
- Both new infrastructure preflights passed. Source is published at
  227da22074201c583dbcfa971863c8f3c41d7391. GRB physical qualification job
  **559429** completed successfully (exit 0, 49 seconds, one CPU, peak
  101884 KiB on snavely-cpu-02). All 20 controls report success in 35 native
  calls. Independent audit now PASSES all 20 controls and 26 corruption checks. The 30-minute allocation, no requeue and
  reserved-node exclusion were verified. Remote
  isolated checkout: `/home/nc437/egg-grb-physical-v3-20260927`. Submission
  sentinel: `grb-physical-submission-20260927`. Do not resubmit this attempt.
  Local submission evidence: `../research-20260927/cluster/grb-physical-559429/`.
  Physical GRB audit has passed; a newly published freeze is required for hull. Public nonlinear
  pilot remains held until both GRB gates pass. Detailed GRB review files must
  live OUTSIDE the raw attempt because its manifest requires an exact file set.
  Full transport and all 146 raw manifest entries were verified locally; raw
  and sibling .launch are installed at canonical paths. The independent review
  and protocol admission JSON are complete; the lead verified the review
  manifest and pure admission gate. Public Git preserves 126 scientific files
  unchanged and omits 20 licensing-only stdout files by declared hash. The
  full local/cluster archive remains intact and is required by admission.
  Sol completed a design proof for a stored-native two-bus cut; it remains
  unimplemented and does not change the fixed pilot. Luna prepared the future
  nonlinear figure/table plan. The broad campaign remains unadmitted.
- The old unexecuted flat-pilot2 candidate is shelved, with its exact patch
  preserved outside Git at `../research-20260927/deferred-flat-pilot2/`;
  the four tracked files were restored to published HEAD. Do not revive it
  automatically. No scientific result was removed.
- The old public checkout remains at 282e00b with its raw pilot outputs intact.
  The new qualification uses the isolated checkout above. Exclude
  scaglione-compute-01 and leave other-project held jobs alone.
- GRB hull job **559602** was submitted once at the new published freeze
  62976f11ecf35c837b0573079892ae5095e846b9, in the separate detached worktree
  `/home/nc437/egg-journal-grb-hull-20260927`. Latest scontrol: COMPLETED,
  exit 0:0, 26 seconds. All 152 physical raw/launch files matched before the
  pure physical-admission/source preflight passed. Slurm verified one CPU,
  8 GB, 15 minutes, default partition, no requeue and excluded reserved node.
  Local receipts: `../research-20260927/cluster/grb-hull-559602/`.
  A heredoc preparation error stopped before any intent/submission; the
  verified continuation submitted exactly once. No scientific retry occurred.
  **Next bounded work package:** retrieve and seal this completed hull attempt
  and sibling .launch, obtain final scoped sacct, then assign Luna an independent
  same-eight-controls result audit outside the raw attempt. Preserve licensing
  stdout locally. Do not resubmit, launch the public nonlinear pilot, or alter
  its predeclared model before the hull gate passes and evidence is published.
- Google Doc includes the verified GRB physical and CBC hull milestone. Saved
  to Drive; the 88,414-byte before export is an exact prefix of the 89,527-byte
  after export, and the new heading occurs once. After SHA256:
  1377215d64b38be24a2934aff9c1b9962bc2bce58bba58f5763654f6884aaccc.
  The PDF remains byte-identical. Verification note:
  `../research-20260927/agent-notes/google-doc-verified-grb-hull-20260927.md`.

## 2026-09-27 terminal update: nonlinear failure and exact depot-15 witness

- Job 559683 is terminal `FAILED 1:0` (00:04:22; two allocated CPUs;
  `MaxRSS=351628K`). The independent audit identifies the cause: the planner
  worker raised `TimeoutError: Scientific routine/admission cap exceeded` at
  242.315324 s, 2.315324 s beyond its 240 s routine cap. It returned at
  243.217558 s, before the 255 s child hard stop (`hard_timeout=false`). The
  frozen batch directives **exclude** `scaglione-compute-01`. Two native GRB
  calls returned; the saved planner interval is partial and solver-conditioned.
  The final assessment file is absent and `hull`/`own_price` remain unstarted.
  This attempt is failed/incomplete and **not scientifically admitted**. Its
  original 15-entry raw archive and manifest SHA
  `796a9c26b968a35a616269043708ba71f95defe1848547ce191d12ecc11f0c2d` are
  unchanged. Full-manifest reproduction requires the complete private archive;
  a public subset omitting declared licensing-only stdout files is not a valid
  input to that driver.
- The separate depot-15 exact-witness review passes for the ideal stored-input
  case only. The rationally replayed two-bus witness plus exact one-bus
  obstruction establish minimum fleet exactly two for this finite depot-15
  model. Its ideal flat synthetic-cost optimum is enclosed by the exact
  interval about `[404.924239883878, 408.5331358838777]`; the optimum itself is
  not identified. Candidate and independent review manifests are pinned in
  `doc/SISTIG_EXACT_PUBLIC_WITNESS_ADMISSION_20260927.md`. This separate result
  does not change the failed nonlinear-pilot status or supply its missing
  hull/own-price stages.
- The independent failure-review package and its SHA-256 manifest are outside
  the raw attempt under
  `research-20260927/agent-notes/nonlinear-pilot-result-review/`. Current queue
  snapshot: no active EGG or other running jobs; held/dependency-pending user
  jobs were left untouched. No new optimizer, cluster, Git, or Google Doc action
  is part of this update.
