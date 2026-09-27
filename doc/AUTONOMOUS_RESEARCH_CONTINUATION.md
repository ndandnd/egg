# EGG journal research continuation

Updated 27 September 2026. Owner: the EGG task, acting as principal researcher
under the user's explicit authorization to continue routine research, cluster
work, GitHub backups and Google Doc updates without repeated approvals.

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
There is no active EGG solver job. Public job557543 COMPLETED0:0 in6m35s,
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
required before promoting the candidate. Figure7 itself passed independent
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
and prospectiveattempt3 protocol; LunaMax operational_data_audit reviews its
stable implementation before any sourcefreeze/optimizer. Sol6_cardinality_bound
is a separate worker implementing newexactflow modules/tests/protocol only.
No public matching calculation before independent code review and published
freeze. No oldrawdata/sourcefixture is rewritten. Current publicpilotcandidate
stillpointsfailedattempt2 and is held; only changeitsgate after a new passed
audit. No EGG clusterjob isactive. Rootownscommit/push/runadmission.
