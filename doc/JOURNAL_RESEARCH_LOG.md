# Journal research log

## 27 September 2026 — autonomous programme established

The user explicitly authorized continuous principal-researcher work, Unicorn
monitoring, experiments, documentation, frequent GitHub backups and Google Doc
updates, with material decisions flagged. The persistent goal is active and
hourly heartbeat `advance-egg-journal-research` was created for this task.
Routine research does not require repeated permission. Background local work
requires the computer and app to remain running.

A fresh GitHub read confirmed main7e18463 and draftPR52–55 unchanged since the
last checkpoint. New worktree `journal-research-work` and branch
`codex/journal-research-20260927` start from PR55 e2a98a2. No PR was merged.
The first network fetch needed normal sandbox escalation and then succeeded;
no approval-review rejection occurred.

Unicorn read-only snapshot at15:11UTC: no running user jobs and no active EGG
job;22queue entries are other-project held jobs, including an array range.
Live resource policy at `/home/nc437/ladder-lite/SCAGLIONE_RESOURCE_POLICY.md`
was read. Recent accounting scoped to the owner/date showed no new EGG rows.
No cluster experiment was submitted in this initial local qualification phase.
Other projects and their held jobs remain untouched.

### New reviewed analytical result

Source/protocol frozen7bf913a. The exact `cyclic_gap` driver ran once under an
external30second cap, output `result/cyclic_gap/20260927-attempt1`. All24fixed
parameter cases are recorded. Nominal physical cost97, complete-hull cost7591/80,
gap169/80. Every used bus starts/ends at20kWh and both structures buy30kWh.
Own-price regret at the physical optimum is13; at common hull prices, fleetLOC0
and supplierLOC169/80. The independent reviewer reconstructed all objectives,
physical traces, mixtures and accounting with rational arithmetic; ten
corruptions were rejected. Scope is the explicit four-period model, not a
production-adapter or operational validation. Three figures reproduce the
archived construction, price accounts and parameter grid.

### Harder reuse attempt and trace repair

Source/protocol/tests frozen7d3d764. First attempt in
`result/reuse_frontier/20260927-attempt1` finished in164.2948seconds with exit1:
all45comparison cells attempted,44certified and matched separate reference
intervals, all15references complete. Cold/depleted_f20/return_base remains a
failure because its pricing solve returnedFEASIBLE at the10second cap rather
thanOPTIMAL. No rerun, tolerance change or reclassification occurred.

Retention requires extra clean discovery calls in4of12warm transitions, five
calls beyond the mandatory twelve checks. Its17warm calls are already below
the24-call lower limit for always adding a full-pricing proposal before every
clean check. Actual analytic shifts reduce clean-call counts in none of the
transitions. Three proposals are projection-distinct in the replenished control
but do not reduce calls. No ML run is justified by this result. Matched14-key
successful comparisons use116/43/54calls for cold/retained/shift. All attempts,
including the failed cold cell's7calls and21.088seconds, remain reported.

The completed non-author audit identified aliased saved tangent lists:
a continuing iteration can log a point added after its master solve. Commit
78bb4c0 fixes future logging with a deep-copy snapshot, with a regression that
fails on the old behavior and passes on the fix. All43focused tests pass.
The original protocol and all244original files remain unchanged; audit derives
the actual solved tangent set only from the proven frozen branch, without
rewriting evidence. See `REUSE_FRONTIER_TRACE_REPAIR_20260927.md`.

### Completed independent harder-reuse audit and portable package

The review, standard-library auditor and regenerated audit output are archived
under `result/reuse_frontier/20260927-attempt1/review/`, with a separate derived
review manifest. The original MANIFEST and all 244 original files are unchanged;
the auditor verifies their hashes and frozen Git dependency objects. Latest
v2 descriptive reports are copied into `review/author-analysis/` with explicit
author attribution, separate from independent findings. Reproduction commands
and cross-host provenance limits appear in
[`review/REVIEW.md`](../result/reuse_frontier/20260927-attempt1/review/REVIEW.md).

Independent exact rational SOC dynamic programming reconstructs all 223 pricing
attempts; its continuous validity follows from integral inventory-flow
polytopes and zero-deadhead depot-arc dominance in these specific fixtures.
The maximum completed-incumbent discrepancy is 5.26e-13. Fresh rational Fenchel
lower bounds using only completed clean prices support all 44 successful cells,
with numerical upper-minus-lower widths
0.000025334433885859653–0.0009124833710245639. Physical witnesses are replayed
as stored binary64 values with 1e-7 kWh tolerances; weights/charges are not
rationalized, renormalized, snapped or repaired. Therefore this is exact
pricing/dual arithmetic plus numerical physical replay, not exact rational
physical certification. All 19 corrupted-copy controls are rejected.

The auditor reconstructs 190 final restricted masters, 189 completed certificate
iterations, 423 retained column occurrences, 222 oracle-event columns and 420 scaled
reference blocks; all 15 complete structure sets match independent enumeration.
The 145 post-solve tangent appends are removed only in in-memory audit copies by
the source-derived branch rule. Reconstructed PWL primal/dual values differ
by at most 2.14e-14. All 804 inner-master records and 1,027 wrapper records reconcile,
but independent KKT is checked only for the 190 returned master solutions.

Separate reference objectives, scaled witnesses, interval arithmetic and
overlap pass. Their native approximately 1e-5 PWL lower intervals are not
independently re-proved: independent support bounds at reference gradients
give widths 0.0019611186460863905–0.022598356017276444. This limitation does not
weaken the independently supported 44 comparison certificates. The failed
cold/depleted_f20/return_base cell is not reclassified despite an independently
optimal pricing incumbent; its FEASIBLE status still violates the frozen gate.

### Literature, data and manuscript

The focused review adds16source-verified comparisons and BibTeX in
`paper/related-work/`. TR-C is the working target conditional on a credible
transportation case; Public Transport is an alternative. The claim is physical
and economic interpretation plus evidence, not invention of convex-hull pricing.

A Luna Max agent audited the GIRO workbooks read-only and found a small uniquely
source-matched internal subset with complete service energy. Detailed hashes,
source-row identities and private records stay outside this Git worktree.
No full-day weekday mapping or real tariff calibration is inferred. The same
agent is qualifying an authors' public instance repository separately.

`paper/manuscript.md` and `output/pdf/egg-journal-working-draft.pdf` are working
draft0.1, with three figures and an explicit operational-evidence gap. They are
not yet declared the excellent first draft in the goal. A manuscript reviewer
is checking scientific wording and all rendered pages. The original Google Doc
received a dated journal-programme section, preserving prior history; final
save/integrity and audit-completion updates will be recorded below.

### Next work

1. Finish manuscript/visual review and incorporate the completed audit's scope.
2. Save reviewed results/manifests, draft PR and hosted tests; correct wording
   if audit identifies a substantive issue.
3. Finish public input semantics/provenance; freeze a minimal timetable adapter
   and run an independent physical qualification before an operational claim.
4. Establish a bounded cluster execution plan from measured needs, published
   source and live resource policy; record exact job receipts and capacity.
5. Extend the manuscript with the operational study and reviewer-driven
   sensitivity, without forcing an ML contribution or overstating novelty.
