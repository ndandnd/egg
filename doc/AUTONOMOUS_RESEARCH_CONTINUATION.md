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
