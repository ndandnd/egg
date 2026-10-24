# EGG current research handoff — 23 October 2026

Worktree: `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`.
Branch: `codex/ml-prediction-20261017`. User resumed research toward a long-term
FT50 aspiration. Manuscript drafting remains deferred; no publication/model
readiness claim is justified.

## Latest executable state: approved budget, failed external freeze

The human explicitly selected **“Raise total to 30 CPU minutes (Recommended)”**.
Read `RECOVERY_BUDGET_APPROVAL.json` for exact question/reply and scope. The
1800-second TOTAL ceiling, 1620-second dispatch stop and 180-second shutdown
reserve are approved and applied. Keep one local single-thread numerical worker,
5 GiB, all prior spend and unchanged original eight-task cases/clocks. Do not
ask for this approval again. Old proposal/review documents retain their historic
pending status; this direct approval is authoritative.

Exactly one newly source-bound check passed **124 tests** in
`admission-capture-checks-budget/attempt01`. It retains the previous 118 cases,
with six supervisor cases exercised against both old/new launchers. Two stale
synthetic spends now use DISPATCH_STOP-20 without weakening assertions. Parent
and independent review verified 160 source hashes, command/output/artifact
hashes, no drift/errors, all three owned groups absent and leader reaped. The
passing check carried610.9167105017234s, including the SINGLE20s administration
allowance shared across this whole approved revision. Read
`RECOVERY_APPROVED_BUDGET_CHECK_RESULTS.md`, its protocol and source review.

The subsequent **v4 external freeze failed** with an actual OS PermissionError
in legacy `checked.cleanup`, after its guarded worker/inner fixture freeze
returned zero. No native solver task launched. Source/resource/monitor gates
showed no drift or monitor failure; the legacy helper threw before returning an
ownership receipt, leaving default empty arrays. Empty arrays are not absence
proof. Exact failing signal/probe/escalation syscall is unproved. This was not
an automatic approval-review rejection.

Parent separately reconciled the sole recorded PGID37089: signal-zero absent,
successful self-including process snapshot, no matching group/leader. See
`recovery-phase1-v4/freeze-attempt01/cleanup-reconciliation.json`. No signals
were sent. This proves later absence and keeps the original freeze FAILED;
never use its generated lock to dispatch native tasks. Stop-on-first-failure was
honored: no repeated freeze, test retry or native launch followed.

Read `RECOVERY_PHASE1_V4_FREEZE_RESULTS.md` and failure review for compact evidence.
**Authoritative conservative carry is718.8639492101057s** from
`recovery-phase1-v4/accounting.json`:610.9167105017234 prior, FULL32.5 freeze
allocation replacing its nominal1.159857...,0.322777 supervisor,75.015458666
possible single-watchdog CPU allowance to later absence,0.10900304238229991
read-only reconciliation. The watchdog interval intentionally overlaps the full
allocation: conservative upper reservation, not measured utilization. No double
worker/monitor CPU charge or extra administration/audit allowance. The original
failed receipt's nominal612.3993446267449 remains unchanged. Dispatch headroom
is901.1360507898943s. Preserve all v1/v2/v3/v4 evidence, fixtures and failed spend.

No numerical worker or unfinished subagent remains. A source-only cleanup-supervisor
revision and eleven fake regressions passed independent static review; they have
NOT been executed. The old
`run_recovery_freeze.py` MUST stay immutable because historical evidence binds
its hash. The candidate `run_recovery_freeze_v2.py` uses approved runner budget
constants and reviewed bounded cleanup with absolute anchor+32.5 deadline,
retained known PGIDs/reap/group states and primary/secondary failure diagnostics.
Its new `src/tests/test_recovery_freeze_v2.py` needs source-bound execution before
any qualification claim. Final child-CPU audit failure now preserves the terminal
receipt, marks observations unknown/accounting incomplete and blocks passing.
Read `RECOVERY_FREEZE_V2_IMPLEMENTATION.md` and `RECOVERY_FREEZE_V2_REVIEW.md`.

## Next executable package

Record ONE fresh source-bound solver-free check covering the existing124 plus
eleven new fake freeze regressions (**135 expected**). Source review found no
remaining blocker, but is not an executed check. New namespace/argv/protocol must carry718.8639492101057s and
all old hashes; do not automatically add the shared20s administration again.
No execution of this new source occurred in the current failed package. Review
the terminal receipt, source/outputs, ownership and accounting before a deliberate
new external freeze. Use a fresh native-v5 destination; never resume/overwrite
v4. This is an explicitly diagnosed, reviewed new revision, not an automatic retry.

Keep original cases50997/40 and50999/80, registry
`recovery-phase1-reservations-v2.json` (50998 rejected), eight tasks, seed17/day,
nonlearned30%+top-three and original12/15/24/27/30/32.5 clocks. Preserve fault,
partial-start processing, independent physical replay/exact bill, fallback and
full-vs-restricted bound scope gates. The GRB library/hash is unchanged from v4
protocol; freeze hashes it without loading/solving. Before each dispatch reserve
complete next allocation, monitoring and shutdown against actual approved spend.
Do not lengthen cases or clocks to obtain a pass. Stop on first failure and
preserve incomplete suffixes. A pass would establish this interface only, not
learned superiority or price-support certification.

Native-v3 remains failed/incomplete5/8 with four timely40-trip tasks, an accepted
partial start and injected-fault fallback; its first80-trip task was late and
three80 tasks undispatched. The capture repair has passed fake tests but has not
yet been measured in another native80 task. V4's failed freeze does not change
that. Every later comparison must use the same complete evidence policy in all
arms.

## Scientific comparison design prepared while budget was pending

Read `RECOVERY_LEARNED_VALUE_STUDY_ADDENDUM.md` before any comparison. It
supersedes the unlaunched nine-arm factorial question/counts/retention/estimand/
resource plan. Six arms, eight fresh synthetic development bases, three seeds,
plus four-base paired scoring-price intervention:192 proposed60s decisions,
28200s planning envelope under the prospective8CPUh ceiling, at most two workers
5GiB each/10GiB aggregate. This is NOT an executable manifest; no case identities
were generated/selected. Actual monitoring overhead may force an incomplete study.

A common price-blind coverage backbone B plus each ranker's filling from F minus
B to exact K controls edge count. Rank-dependent top-three unions did not. Equal
counts do not equalize topology/search difficulty; retain zero-exposure cases.
Primary is graph recovery versus unvalidated charging-aware CA1, with direct
CatBoost/constructive CF1 secondaries, random recovery and full cold8 references.
No static arms, hence no restoration-effect estimate. CA1/CF1 need implementation
and credibility checks, not favorable-case selection on the new cohort.

Both frozen learned scorers receive linear prices a, not b; the old heuristic
is price-blind. The paired intervention holds native target tariff fixed while
changing only scorer price inputs, recomputed within both clocks. This can
separate ranking response from native charging. CA1 sees a,b, so its contrast is
between deployable methods, not matched-information proof of learning. Detailed
notes: `RECOVERY_CLASSICAL_BASELINE_SPEC.md`,
`RECOVERY_FEATURE_AND_OUTCOME_AUDIT.md`, `RECOVERY_COMPARISON_DESIGN_REVIEW.md`,
`RECOVERY_STUDY_ADVERSARIAL_CHECK.md`. Do not repeat the completed design audit.
After native qualification, implement selector/CA1 and then CF1 as justified
bounded work. No comparative launch until applicable engineering gates pass.

The priorv3 consolidated result is already posted/verified in the original
Google Doc (`recovery-phase1-v3/google-doc-update.json`). No routine engineering
or prospective-design append was made for this package. Preserve history/visuals.

The existing hourly automation was updated through the app and read back exactly:
approved1800/1620/180 persists; do not re-ask or repeat old primitive gates without
a concrete source-change need. Schedule/status/thread stayed unchanged; unrelated
paused automations untouched. Receipt: `automation-budget-approval-update.json`.

## Scientific priorities

The October17 development screen remains historical: current80-trip gains are mostly fewer vehicles. `bill-mechanism/RESULTS.md` attributes91.916% of summed paired graph-versus-one-heuristic savings to vehicle-count cost; this does not decompose the68.36% median-group gain. At40 trips matched fleet counts agree. Price-responsive learning and broad generalization remain unproved.

Prioritize reliable full-model recovery, constructive/charging-aware classical controls, matched total-budget allocation and genuinely independent timetable/regime evaluation. Then test better labels/ranking losses, ensembles/adaptive retention and justified model improvements. Generic GNN arc pruning is established prior art. Do not infer novelty, certification or a strong predictive model from fit completion, classification scores or engineering tests.

The cross-field/Scholar review is complete in `cross-field-review/CROSS_FIELD_SYNTHESIS.md` (41 core entries, explicit source-access limits). Do not repeat it routinely. Olson/Lusby/Ropke progressive restoration, Montanaro GRASP/pruning and Wu grid/EV coupling constrain novelty. The user's clarification is firm: outside-field work earns a place only through directly fitting assumptions, relevant prior art or useful methods/theory/evaluation; never force biology/chemistry/quantum analogies into the paper. No useful transfer is an acceptable search outcome.

## Operating rules

Use GPT-6.1 Sol for bounded implementation, analysis and routine tasks with short handoffs. Check active agents and exact local receipts first. Use followup_task to reactivate a completed agent; send_message alone does not start a turn. Avoid broad rereads, raw traces, repeated audits and duplicate attempts.

Work locally in `.venv-local`; leave Unicorn to v2g and do not routinely monitor/launch cluster work. Qualification uses one single-thread worker and5GiB. Freeze sources/assets before dispatch and never edit them while workers run. Count startup, scoring, search, replay, recovery, artifact finalization, failures and monitoring. Keep variants within timetable groups and selection inner-only. Keep sealed DEV/TEST/A6/B3/confirmation/GIRO closed.

Back up meaningful milestones to origin/codex/ml-prediction-20261017 with explicit per-command Nathan Cho <nathan.cho2013@gmail.com> author identity, never rewrite history. Keep old branches/bundles. Append consolidated verified scientific milestones to the original Google Doc when useful, preserving history/visuals; don't duplicate the six October1 entries. Do not duplicate routine engineering updates. No PR merge, journal submission, private-data publication or reset-credit redemption.

The hourly research automation remains useful and active; unrelated schedules stay paused. Notify only substantive results, important failures, major decisions or concrete review-ready research. Stay quiet on routine checks and passing tests. Full earlier checkpoint history is preserved in `CONTINUATION_HISTORY_THROUGH_NATIVE_V1.md`; read it only if a specific historical detail is needed.
