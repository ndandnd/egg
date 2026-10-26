# DRAFT: duty commitment and economic-lens seam

26 October 2026. Parent's `evspdr_correspondence/STUDY_DECISION.md` is the
selected design. This namespace has no actual input, generation or numerical
attempt. STATIC implementation only: no fixture construction, import, test,
hash, solver, replay or execution occurred while authoring this draft.
LAUNCH remains DRAFT/PENDING with source pins/revision/command/resource adoption
unset. Owner and worker deny fixture generation and dispatch until a future
source-reviewed FROZEN/PASS launch. No GIRO, old TRAIN, sealed bank, metadata,
old outcome or saved physical plan is an input.

## Literal authority and four contexts

The only fixture authority is NEW local `adapter.py`: one literal
`duty-market-seam-v1`, eight45-minute/20-kWh services in four waves starting
60,240,420,600, with the reverse-direction service10 minutes later in each wave.
Two predetermined alternating-direction duties cover all services exactly once.
N=max_vehicles=2, battery80/reserve10kWh, efficiency.9, full initial and per-bus
full terminal SOC, terminal opening720/deadline960, hourly market edges0–960.
One depot, connector1, bus/grid60kW throughout; specified D↔A10min/2kWh,
D↔B15min/3kWh,A↔B10min/2kWh, same-place movement0. All compatible chronological
direct/depot modes are declared. Vehicle100/movement-duration0 and stationary
waiting energy0 are synthetic assumptions, not Partille equivalence or money.

The constructive reference takes the two duties via depot between consecutive
trips, with serial full refill ordered by charging-window release then duty
index. Failure of window/SOC/resource admission stops; no repair, alternative
fixture or search for a favorable case. Parent independently replays the
unchanged constructive plan in the full case before any solver dispatch.

Hourly a=.25 except zero-based4,5,12,13 at.125. U=32kWh in0–7 and64kWh in8–15.
**U is market background ONLY**. It is not additional demand on the fleet's
60-kW connection and must not be subtracted from fleet grid capacity. All lenses
use period grid kWh. Four frozen context IDs/order:

| Context | b | Optimized lens | Native quadratic coefficients |
|---|---|---|---|
| b0_all | 0 | Posted/strategic/system coincide | alpha=a,beta=0 |
| posted | 1/1024 | Posted p=a+bU | alpha=p,beta=0 |
| system | 1/1024 | Incremental integrated system cost | alpha=a+bU,beta=b |
| strategic | 1/1024 | Endogenous uniform-price fleet payment | alpha=a+bU,beta=2b |

Native objective is ops+sum(alpha L+.5 beta L²). Original a/b/U/posted and
institution labels remain in the receipt; every endpoint is valued under all
three true lenses. Report system increment and background/total system cost
separately; do not call strategic payment system procurement. The b0 row has
one set of solves with three aliases, not three independent replications.
No curvature/resource/tariff scan, retuning or empirical price-impact claim.

## Twelve workers and meaningful controls

All12 tasks are declared before fixture import/construction. For context index
i=0..3 and canonical phases[target_qp,fixed_duty,full], ordinal=3i+phase_index+1
and task ID `T{ordinal:02d}-{phase}`. Per context, target QP executes first.
Dependents are fixed_duty→full for b0_all/system and full→fixed_duty for
posted/strategic, frozen before execution. Task identity is independent of this
counterbalanced execution order.

Target QP reuses immutable warm_replication/qp_control on the constructive
movement path. Require fresh physical C/nativeOPTIMAL/intact copy/source guards
and timely admission; a fallback-only run is not a qualified common incumbent.
The common endpoint is returned retained U, possibly better old B, separately
read/replayed/valued by the parent. No caller replay of hidden C is claimed.
If this prerequisite fails, retain both dependent tasks as missing; no cold
replacement or extra solve.

Both dependent workers receive **the same target-QP U**, not the first branch's
improvement. Fixed duty uses an explicitly identified movement-subset case view:
retain all compatible direct/depot modes for consecutive trips of each duty and
the permitted first pullout/last pullin. Re-identify only for that declared
view, then restore full-case identity and independently replay/validate the
retained endpoint in the full case. Preserve ordered duties and N2. Its bound
scope remains restricted. Full uses the original declared graph/exactN. Both
reuse unchanged economic_recourse_pilot/miqp_control; no alternate decoder,
new optimizer, post-polish solve, threshold relaxation, sibling edit or retry.

Supported-status fresh physical MIQP delivery can count as strict success without
nativeOPTIMAL. Status/bounds/start processing, C/B/U, movement-path changes and
ordered-duty changes remain separate. Ordinary failure/late endpoints preserve
the qualified common operational fallback and failed-method flag. Native API,
copy, identity, configuration or resource failures stop onward. A same-movement
improvement outside the existing agreement guard is a discrepancy, not duty
reassignment value; keep its physical best point and qualification reason.

## Paid clocks and ownership

NEW total1500CPU/2400wall, dispatch1320/closure180CPU. At context start reserve
3×90CPU against dispatch1320 (thereby preserving closure180) and3×(60+3)wall plus
final90; recheck remaining workers before each stage. Preflight/source prep≤60CPU,
including source-prep10CPU/30wall. Finalization≤60CPU/90wall is inside closure,
not extra. One serial worker/native thread, hard worker90CPU, observed worker
RSS≤5GiB. Parent self RSS/thread and maximum observed worker RSS are reported;
these are observations, not instantaneous containment.

Anchor before each Popen; native cutoff52, complete parent endpoint60, owned
child TERM/KILL/reap cleanup3. Parent reads/hashes its owned plan once, replays
in full case, checks N/path/duties and exact target value inside60. Signals defer
through PID publication. Only unreaped owned child PIDs receive direct cleanup
signals; unresolved child carries90CPU reserve and stops onward.

Each logical QP→MIQP branch has two paid anchors. The context has three workers/
three anchors, executes shared QP once, and charges it once. Full context latency
includes all startup, transitions, serial branch waiting, admission and cleanup;
there is no single60-second context or equal cold-budget speedup claim. Waiting
for the other branch remains visible in context latency.

Accounting uses cumulative self+waited-child CPU+once-adopted source preparation,
not task deltas added a second time. Future `preparation_accounting` requires
external_accepted=true, charged_cpu_s≤10 and elapsed_s≤30; parent adopts
max(selfCPU,externalCPU)+.02 rounding guard after the one metered source freeze.
The actual selected tracking and numerical_resource prefixes are recorded
verbatim and need not equal historical context numbers. An already-carried prep
component is included for this package cap, not added again to global tracking.
External meter closes publication/exit tails; no old refund/reset or exact
whole-session CPU claim.

## Source freeze and outputs

Exactly14 source/control paths are required by owner preflight: nine code files
(newrun/adapter/worker, immutable oldQP/MIQP, egglab __init__/native_recharge/
native_hull/native_pathflow), local PROTOCOL/OWNER_NOTE/WORKER_NOTE, selected
STUDY_DECISION and parent-ownedprepare.py. Source map keys are absolute. The owner
hashes each consumed source once in paid runtime integrity admission; this is
not an independent reviewer proof pass. Normal immutable helper dependency
fingerprints remain their paid existing behavior, without new tree audits.

Parent source prep creates `preparation01/receipt.json` and
`LAUNCH_FROZEN_CANDIDATE.json`; it does not overwrite DRAFT authority until the
external meter has been accepted. Parent then adopts actual source-prep charge,
freezes command/source_revision/parameters/environment, commits final control and
decides whether to issue the one command. No preparation batch is launched here.

Fresh exclusive `attempt01` preserves all12 stage states and4 context states on
preflight failure, missing common, deadline, budget stop or fatal exception.
Administrative passed means complete planned ledger/accounting, not success of
every method or optimality. Record unchanged constructive, commonQP, fixed-duty
and full operational values/components/cross-valuations. Three per-context
contrasts are QP−fixedDuty,QP−full,fixedDuty−full. Missing operands stay null;
failed methods with a valid common fallback remain operational but not strict
successes. A complete4-context report is a completeness statement: **no pooled
cost/gain mean across institutions** and no available-only substitute.

The same in-memory finalization publishes READOUT.json with all4 contexts' costs,
components, contrasts,C/B/U/native status/gap/start,duty/mode changes, failures
and stage/pipeline times, then a short READOUT.md with cost/contrast and phase
attempt/qualification/status/duty/fallback/failure-count tables and prepublication
resources, then the full master receipt. Stdout prints summary/resource paths
only. This is the existing final60CPU/90wall publication, with no extra inputs,
replay, solves, formatter process or analysis phase. If interrupted, preserve
partial owned artifacts and the incomplete master; external exit/tail acceptance
is required. One base is one descriptive unit. No
statistical/equivalence claim, threshold or ML promotion rule follows; old learned
no-go results and EVSP-DR integration limits remain unchanged.
