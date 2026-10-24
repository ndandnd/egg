# EGG current research handoff — 24 October 2026, CF1 source gate passed

Worktree `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`, branch
`codex/ml-prediction-20261017`. User seeks rigorous research toward a long-term
FT50 aspiration; manuscript drafting remains deferred. Manage short bounded
GPT-6.1 Sol subagent tasks; avoid full-history/STATE_MAP rereads and repeated audits.

## Newest state: CF1 construction and charging helper passed a source gate

New `constructive_control.py` implements price-blind greedy routing, optimistic
per-leg SOC/terminal screening and cumulative at-most-two LIFO undo. New
`constructive_charging.py` accepts an uncharged topology, audits/fixes all movement
binaries in the original full compact model, preserves physical rows, checks all
remaining variables continuous, and retains the minimum independently replayed
exact bill through later objective failures. Fixed-typed binaries remain binary;
no native LP or unrestricted bound is claimed.

The single source-bound `constructive-controls-checks/attempt01` check passed
**31 symbolic/fake-native tests in 0.08 s**. Read `RECOVERY_CF1_RESULTS.md`, the
construction/charging implementation notes, independent contract review and
`constructive-controls-checks/{command.json,attempt01/result.json,accounting.json}`.
No failure, source drift or cleanup/accounting issue in that check. PGID72796 is
absent and reaped; no active numerical worker or subagent remains. A stdlib-only
metadata-preparation NameError was corrected before command freeze/any attempt
and retained in metadata; there was no failed/retried numerical check.

**CF1 is not yet a qualified composite arm.** No native solver, timetable generator,
learned inference/training, protected asset or comparison ran. Qualified core,
models and historical evidence are unchanged. The source-only helper does not
persist a fallback, submit a start or orchestrate repairs/full search.

Next bounded source package: integrate CF1 with durable fallback admission,
conditional repairs and the explicit 60-second shared clock. Only a qualified
INITIAL fixed-topology feasibility INFEASIBLE may trigger undo, never objective
infeasibility, timeout/no incumbent or invalid replay. The caller must compute
ONCE, before initial setup/build,
`completion_deadline=min(t0+0.2*T, first_completion_anchor+max(2,0.1*T))`, then
reuse it across all phases/repairs/rebuilds. Passing only t0+0.2*T can exceed the
allowance after fast construction; renewing now+6 is invalid. The helper has no
T/anchor input and cannot independently enforce that absent caller policy.
Preserve at most two repairs and common finalization/full-search budgets.
After focused source checks, freeze an affected-path native preflight prospectively;
do not repeat the old full matrix without a diagnosed need.

## Inherited state: common selection and CA1 passed their unit gate

`src/egglab/classical_controls.py` now implements the common exact-cardinality
selector, one `restrict_case` application helper and the CA1 charging/cost proxy.
The single source-bound `classical-controls-checks/attempt01` check passed **31
symbolic tests in 0.07 s**. No native/core, trained model or frozen asset changed.
Only the new focused tests ran; historical qualified tests in the hash closure
were dependencies, not rerun tests. The independent static review included a
nontrivial incoming/outgoing coverage union and K-expansion regression.

Read `RECOVERY_CLASSICAL_CONTROLS_RESULTS.md`, the implementation/review notes and
`classical-controls-checks/{command.json,attempt01/result.json,accounting.json}`
for this package. No failure, source drift, unknown accounting or cleanup error.
Owned PGID68267 is absent and reaped. No timetable generation, model inference/training, native solve or
comparison followed. This is a pure control-unit gate, not a replacement native
qualification or evidence of a strong classical control or learned advantage.

CF1 source and fake-interface checks now follow above. Its composite/native
integration remains pending; do not infer it from either pure unit gate.

## Inherited state: original eight native paths passed

Read `RECOVERY_PHASE1_V7_RESULTS.md` and current compact receipts first.
**V7 passed8/8 engineering tasks**, on two synthetic timetables (50999/80,
50997/40), seed17/day/nonlearned30%+top-three. Both sizes independently showed
accepted/processed normal partial starts and valid fallback through injected
setter failure. Eight timely replay-valid outputs, zero invalid witnesses,
mapping/bound-scope violations or censoring. All eight native owned groups are
absent and their owner marker is removed. No native retry or extra example followed.

Qualified source commit **d49e0b15**. V7 source-bound213-case software check and
supervised freeze passed before dispatch; original fixture bytes/identities,
market/movement order/library/task IDs unchanged,80-first. Lock now records
`anytime-hard-admission-v1` and planned headroom. Planner/native targets13/25
are diagnostic; hard physical/durable admission15/27 and output30/outer32.5
remain. Native planned10/22, original12/24 upper caps, cumulative completion3s
unchanged. This prospectively changed the v6 contract: all earlier failures
remain failed and fully charged. Do not retroactively use their late witnesses.

80recovery genuinely passed admission after target misses: prefix durable13.659<15;
full independent lift26.671 and subsequent checks before26.868<27; output27.522<30
is a separate endpoint. It improved its own restricted bill3642.53→3628.91 with
27 vehicles. Cold full solving was cheaper3386.20 with24 vehicles. At40 recovery
retained its original658.68/4-vehicle fallback; cold658.71/4. **No learned scorer
was used**, and these two engineering cases/one seed establish no ML/recovery
advantage or generalization. None certified optimality;80warm lower−1e100 is
uninformative. Keep physical validity, native processing and useful full bounds
separate. Do not report restricted/fixed-route bounds as full certificates.

Current evidence:
- `RECOVERY_PHASE1_V7_PROTOCOL.md`, anytime implementation/check/contract notes.
- `anytime-admission-checks/{command.json,attempt01,accounting.json}`:213 passed.
- `RECOVERY_PHASE1_V7_FREEZE_REVIEW.md`, result review and interpretation.
- `recovery-phase1-v7/{lock.json,native-launch.json,parent-freeze-review.json,
  gates.json,compact-summary.json,runs/ledger.jsonl,accounting.json}`.
- `raw-diagnostics-index.json`: native/license logs stay local hash-indexed;
  complete public synthetic capture JSON/plans/receipts retained in Git.

## Authoritative qualification budget

Carry **1295.1392203401801 charged seconds** from
`constructive-controls-checks/accounting.json`. Recorded-field decimal sum is
1295.1392203401801603. Latest check adds1.0212059999999998 s (allocation0.412408
plus supervisor0.608798) to1294.1180143401803. Monitor-child0.207502 s is already
in observed children/allocation; do not add it again. Previous CA1 check adds
1.005529 s to native V7's1293.1124853401802. Every earlier failed/conservative
charge remains inherited. V7 includes its final analysis tail; its gates alone
omit.002147 s. The shared20s administrative provision is already inherited.

Approved1800 hard /1620 dispatch /180 shutdown reserve, one local single-thread
numerical worker and5GiB remain. **ADMIN0**: shared20s already carried. Remaining
dispatch headroom324.86077965981985. Do not ask again for this approved cap.
Any further native qualification/preflight remains charged here unless an
explicitly applicable later budget exists; a new label cannot reset qualification
spend. No new resource commitment was made. Do not repeat historical passed gates
without a diagnosed affected source/path change. Preserve every failed revision.

## Next bounded package: composite CF1 and 60-second clock

Advance source integration rather than another broad qualification campaign.
Use `CF1_PACKAGE_PROTOCOL.md`, `RECOVERY_CLASSICAL_BASELINE_SPEC.md` and relevant
study addendum only as needed. Source control helpers are implemented, not yet
credible performance baselines. No trained asset needs editing or inference for
the integration task. Keep model and original native/replay sources unchanged
where possible; new wrappers must reuse the qualified start and physical lift.

Use the existing common price-blind top-three incoming/outgoing backbone B and
exact flexible K=min(M,max(ceil(.30*M),|B|)); preserve boundaries, original order,
zero exposure and identities. Equal counts do not equalize topology/search effort.
CA1 sees a,b while current learners see a only. CF1 is price-blind construction
followed by target-market charging, so its bill response is not learned response.
Neither control is a feasibility/optimality certificate before physical replay.

The comparison is proposed at **60 s**, but `recovery_coordinator.Schedule` still
requires exactly30 s. Freeze explicit construction/charging/prefix/full-search/
admission/finalization allocations and affected-path tests before using60 s.
Preserve the qualified30 s behavior rather than silently scaling constants or
claiming its gate covers60 s. Common clock begins before imports/loading/scoring;
all construction, rebuilds, replay, exact billing, capture and durable writes count.
A one-time charging-window deadline must enforce cumulative completion across
repairs as stated above. Durably admit a replay-valid fallback before warm start,
retain it through rejection/later failures, and report actual native processing
and full unrestricted bound certification separately. No60 s launch manifest,
new cohort registry, inference or training run exists yet.

Current unlaunched study: six arms (graph-v8/CatBoost/CA1/random recovery,
cold full and CF1), eight fresh development bases, three seeds, plus four-base
paired scoring-price intervention:192 proposed60s decisions;28200s planning
under a prospective8CPUh ceiling, at most two workers5GiB each/10GiB aggregate.
A study proposal is not dispatch authorization without frozen manifest/assets/
clock/protocol and applicable gates. Include startup, preprocessing, inference,
search, repair/replay, recovery and final artifacts in the shared clock. Keep
scorer-only price intervention distinct from native target market. Both frozen
learned scorers currently see a,not b; CA1 sees a,b, so contrast is between usable
methods rather than matched-information proof of learning. Completed feature/
design audits need no routine repeat.

Engineering bases50997/50999 have now been inspected and must not appear as fresh
held-out comparison evidence. Keep all timetable variants/source plans in one
group, selection inner-only, independent cohort registry frozen prospectively.
Keep sealed DEV/TEST/A6/B3/confirmation/GIRO closed. No new case replacement or
unreceipted/interrupted attempt may be retried automatically.

## Scientific priorities and operations

October17 outcomes remain development. `bill-mechanism/RESULTS.md` attributes
91.916% of summed paired graph-versus-one-heuristic savings to vehicle count;
that is not the decomposition of68.36% median-group gain. No tariff-responsive
learned advantage established. Generic GNN arc pruning has direct prior art.
Prioritize classical/constructive controls, matched budgets and independent
regime evaluation before justified model/label/ranking improvements. Fit/AP,
accepted starts and engineering passes do not establish novelty or FT50 readiness.

The completed41-entry Scholar/cross-field synthesis is
`cross-field-review/CROSS_FIELD_SYNTHESIS.md`; do not repeat routinely. Borrow
outside-field work only through directly fitting assumptions/useful methods;
never force biology/chemistry/quantum analogies. Work locally in `.venv-local`;
leave Unicorn to v2g with no routine monitoring/launches. No PR merge, paper
submission, private-data publication, reset-credit redemption or history rewrite.

Back up milestones on this branch with explicit Nathan Cho
<nathan.cho2013@gmail.com> author/committer. Original Google Doc now contains ONE
consolidated v7 milestone headed “24 October 2026: local replay and recovery
pipeline qualified”; exact append/prior structure verified in
`recovery-phase1-v7/google-doc-update.json`. Do not duplicate it, v5 or the six
October1 entries; preserve visuals/history. Read fresh revision before later edits.

Hourly automation remains useful/active; unrelated paused schedules stay paused.
Notify only substantive findings, important failures/decisions or review-ready
research, not routine checks/preparation/passing unit tests. Continue one bounded
useful package per wake under standing authorization.
