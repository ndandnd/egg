# Current handoff — 25 October2026: GNN diagnostic passed; strengthen charging control

Worktree:/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017
Branch:codex/ml-prediction-20261017. Read this checkpoint then relevant compact
results/protocols only. Check actual agents and workers; no duplicate attempted
or running tasks. Manage bounded GPT-6.1 Sol handoffs.

## Completed warm study — do not rerun

warm_replanning/attempt01 completed ONCE. Main exec72031 CLOSED exit0; finalizer
33404 CLOSED exit0. All8 priors valid,168/168 decisions accepted within60s,
167method_success. One CatBoost80-trip seed41 run kept its valid round2 improvement
after round3 timeout; preserved as method_success=false. No late/config/invalid
admissions. Frozen finalizer and archive checks passed; all8 baseline captures
losslessly archived, originals local. No active numerical workers.

Read warm_replanning/RESULTS.md, COMPACT_RESULTS.json (small primary sections,
not non-successful-cell selection arrays), POST_RESULT_CRITIQUE.md and
RESOURCE_RECEIPT.json. Four base groups50600–50603,40/80 nested variants with
size-scaled180/270kW resources and seeds17/41/73: FOUR group units, not24 independent
samples. Warm day->late, same original physics, fixed active-fleet count, known
prior protected inside same K for every restricted arm, all costs paid. Both
classical controls remain. No refit or outcome-selected group/model replacement.

Frozen d=(controlCost-learnedCost)/priorLateElectricity E0:
- GNN vsCoverCA1 mean d=.012318882,group medians positive4/4.
- GNN vsfour-round fixed_route mean d=.120116748,positive4/4.
- GNN exploratory continuation TRUE under the original rule.
- CatBoost vsCover mean d=-.010282453,positive2/4; gate FALSE.
These are fractions of PRIOR electricity cost, not relative reductions versus
control's own bill. Fleet cost fixed/deadhead0, so differences here are electricity
cost; energy-demand vs charging-time mechanisms not isolated. GNN–Cover margin is
small/heterogeneous. No significance, SOTA, price-information causality, cold
speedup, model promotion or unrestricted certificate. Current models use a not b.

## Immediate next package — direct fixed-route convex QP

DO NOT dispatch the prepared384-cell warm_replication yet. Its8newgroup metadata
and cloned driver/scoring/finalizer are STATIC/unreviewed/pending. Fixed IDs50604,
50606–50612,old7arms+GNN_day,3seeds;8CPUh/10wallh direction only. Parent retains all
comparators instead of critic's smaller128-cell proposal; that critique remains
preserved. No source/command binding or numerical launch yet.

A subsequent two-file static triage found four-round fixed_route charging stops
with unused time and finite-envelope gap. Read warm_replanning/
FIXED_ROUTE_CONTROL_TRIAGE.md and PARENT_RESEARCH_DECISION.md. Do not silently
call it a converged convex optimizer or replace its recorded outcomes. This does
not explain away12%E0 or alterGNN–Cover, but motivates a stronger cheap control.

Fixed_route_qp attempt01 ran ONCE after source/protocol commitd4cd4ab1 was pushed.
It FAILED the combined bound/index/type copy check on first50600/40 BEFORE any
native optimize call; zero native calls/attempts, seven later cases undispatched,
PID22815 reaped. Preserve every receipt, v1source and failure. External0.72CPU/
0.92elapsed is nonrefundable. This is not physical infeasibility. See
ATTEMPT01_FAILURE_AND_V2_DECISION.md. The old combined error did not identify the
offender; semantic infinity mismatch is a STATIC diagnosis, not yet confirmed.

Parent recorded a deliberate narrow v2 correction: documented side-specific
LB<=-1e20 / UB>=1e20 infinity semantics; every other finite bound/index/type/row/
objective/replay guard unchanged. qp_control_v2.py and run_v2.py are separate
sources, fresh attempt02 ONLY. PROTOCOL_V2.md,RESOURCE_DECISION_V2.md,LAUNCH_V2.json
bind the continuing SAME1800CPU/2700wall cap including0.72/0.92carry. One focused
static delta review must pass before one command; never resume attempt01.
Inherited unchanged source/prior digests remain frozen; hash predecessorpreflight
once plus only five freshv2files, no duplicate oldasset/prior audits. V2 was
launched ONCE after reviewed source/protocol commit82e2535f was pushed. Exec82477
CLOSED exit0:8/8 native calls and accepted operational endpoints,7/8 physicalQP
successes. Last50603/80 returned nativeOPTIMAL but unchanged extraction rejected
an unrepresentable positive-charge session; it retained the valid prior. Never
report that raw optimum as a physically feasible bill. No retries/source edits
occurred during execution. Check actual receipts and agents before action.

Scope: ALL8 already saved prior topologies, native seed17, original full physical
matrix, all original routing choices fixed, direct convex integrated-cost QP via
public installedgurobipy12.0.1. Existing hull QP is SLSQP column-mixture, not this
physical charging problem. Original Python-MIP matrix cloned by storedfloat
bounds/rows/senses/RHS, no LP/MPSroundtrip/privateCFFI. Fixed binaries can be
continuous singletonbounds. Add .5*b*L², not atomicpayment. Narrow solution-value
facade into unchanged pf._extract + independent full-case replay; retain valid
prior on failure. OneQPcall/thread/observed5GiB,60s inclusive/native52. No extra
feasibilityLP, seed or automatic retry. Copy/identity contract failure stops later
dispatch; unsupported dualbounds null, no unrestricted/exactcertificateclaim.

Selected newQPbudget1800CPU/2700wall TOTAL,dispatch1620/reserve180,analysis60CPU/
90wall inside total; workerCPUhard90,cleanup<=3s. No budget answer pending under
human practical routine authority. Bind source/input/priorfiles once in metered
preflight, no learnedassets or rawcaptureaudit. Compare stronger charging witness
with saved capped-control result; do not claim isolated backend timing gain.
If QP materially strengthens baseline, add it prospectively before replication.
No model training yet. GNN_day contrast later tests inference conditioning only;
comparably selected tariff-blind TRAIN fit still required for information value.

## Accounting, documentation and boundaries

Closed warm package:6796.46CPU/6952.21wall main;1.54CPU/1.64wall frozenreadout;
.04CPU/.12wall compactexport. Total6798.04CPU,elapsed-sum6953.97s. Priorreset206.31CPU/
223.25elapsed -> warm CLOSED cumulative7004.35CPU/7177.22elapsed-sum. QPattempt01
adds0.72CPU/0.92elapsed -> CLOSED cumulative7005.07CPU/7178.14elapsed-sum BEFOREv2.
V2 external48.08CPU/49.61elapsed -> CLOSED cumulative7053.15CPU/7227.75elapsed-sum
BEFORE compactanalysis. SharedQPpackage spent48.80CPU/50.53elapsed beforeanalysis,
including attempt01. These overlapping views must NOT be summed wholesale.
Not exact sessionCPU.
Separate legacy conditionalguard2546.091499549272s remains; historical actualreview
CPU UNKNOWN. Never reset/relabel it or restored old-cap compliance. FutureQPspend
added separately from actual meters. No duplicate unmetered hash audits.

Original Google Doc now has verified warm-result/capped-control section
[235331,238074),all8images retained; exact full-string match and heading verified.
See warm_replanning/GOOGLE_DOC_APPEND.md. DO NOT duplicate it, older25October or
sixOctober1 entries. Sourcewarmcommit0c77fa6a, runningpreflightae119f15 and
completedscienceb2c02aac were pushed; new QP failure/v2 sources require backup with
explicit AUTHOR AND COMMITTER Nathan Cho <nathan.cho2013@gmail.com>. Never rewrite
history. Five old untracked responsive-component files stay separate/deferred;
no old namespace revival, engineering matrices or routine experiment repeats.

No cluster access/monitoring/jobs; leave Unicorn to v2g. Sealed
DEV/TEST/A6/B3/confirmation/GIRO closed. No PR merge, submission, private publication
or reset credits. Manuscript deferred. Group all variants, inner-only selection,
independent final tests untouched. Keep unrelated paused schedules paused. Notify
substantive science/failures/major decisions; routine preparation remains quiet.
