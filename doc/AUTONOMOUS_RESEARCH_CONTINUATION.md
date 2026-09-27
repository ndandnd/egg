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

The 16-paper source matrix, editable manuscript and three scientific figures
are under `paper/`; the rendered review copy is
`output/pdf/egg-journal-working-draft.pdf`. This is working draft 0.1, not yet
the excellent first draft promised to the user: operational evidence and
economic interpretation still need work. Independent artifact audits and an
author-disclosed manuscript review accompany the analytical evidence.

## Current priorities

1. Complete the local-only source-faithful GIRO microcase extraction and
   directed/time-dependent deadhead coverage audit. Preserve raw provenance
   outside Git; do not describe this subset as a complete named weekday.
2. Design and independently qualify a native terminal-recharge physical adapter,
   with precise charging-window overlap and shared-capacity semantics. Avoid
   terminal service markers in a variable-fleet replenishment claim.
3. Freeze a bounded operational microcase protocol before solving. Separate
   source service energy from modeled deadhead energy, battery/charger choices,
   operating costs and supply curvature. Start with falsification controls;
   launch scoped Unicorn jobs only when implementation and input gates pass.
4. The Parmentier companion benchmark is pinned and locally inspected. It is
   useful for independent parser/route feasibility, but its abstract units and
   source-model simplifications are not calibrated bus-operation evidence.
   Local intake is `../research-20260927/agent-notes/public-data/`; do not publish
   raw inputs while data-specific redistribution terms remain unresolved.
5. Integrate verified operational findings, sensitivity analyses and useful
   figures into the manuscript; complete reviewer audits and CI. Keep GitHub,
   this file and the research document current at meaningful milestones.

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
