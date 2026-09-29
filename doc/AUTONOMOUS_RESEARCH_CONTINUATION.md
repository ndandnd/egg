# EGG journal research continuation

Updated 29 September 2026 UTC. Owner: the EGG task, acting as principal researcher
under the user's standing authorization. Computational journal paper; iterative
optimization first, then retrieval/learned proposals. The v0.5 draft is historical.
Use GPT-6 Sol for implementation/analysis and Luna Max for supporting work; root
manages. Hourly `advance-egg-journal-research` remains ACTIVE, quiet when unchanged.

## Latest checkpoint — public sensitivity job 600028 running

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
  with this launch receipt. Full source CI 36511357899 was in progress at launch;
  check its final result once next continuation. Earlier backup CI 36510140256
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
and2 retained successor states correctly blocked after their predecessor failed.
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
Root compact path-flow module and20-control gate are ready for independent
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
The audit reconstructed42,297 raw values,41 charging sessions and231 SOC events;
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
