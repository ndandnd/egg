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

### Reviewed working draft and hosted verification

The manuscript review is complete, including all 11 PDF pages and three
figures. The reviewed PDF SHA-256 is
`a5b4c9c9754d5a5620704ee8622cea26ca5eef25fdf0c6359677b086615e699a`.
It remains working draft 0.1 pending operational evidence. Review corrections
include the global supply domain, explicit two-period cost, endpoint handling,
complete-fleet terminology, mathematical typesetting and matched work totals.
The report declares its author's involvement in the reuse implementation;
the separate result audits are non-author checks.

The milestone was committed and pushed as `c0f83f0`, with draft
[PR56](https://github.com/ndandnd/egg/pull/56) stacked on PR55. Hosted
[CI36330227545](https://github.com/ndandnd/egg/actions/runs/36330227545)
passed **826 tests in 205.28 seconds**, with whitespace and shell checks also
passing at that exact head. Later heads must receive their own CI assessment.
No merge or journal submission occurred.

The Google Doc's “Verified manuscript milestone — 27 September 2026” section
records the completed audit and links PR56, the reviewed PDF and the ledger.
Saved-to-Drive was verified. A complete text comparison preserved the original
55,398-character history prefix and found exactly one new milestone heading;
the document then contained 62,461 characters. The cyclic result table was
kept together on a fresh page.

### Additional exact verification runs — execution checkpoint

The original example is on a binding early-power boundary. A positive reserve
or charging loss with unchanged hardware removes its one-bus option. The new
analytical design records that negative result and a modified positive example
with reserve 1 kWh, efficiency 19/20, early power 12 kW and one 30 kW terminal
connector. Source/design/protocol were frozen at `bd022ac` before the first run.
All 16 declared cases completed in 0.0054 seconds: nine positive gaps, six zero
gaps and one infeasible case, matching the prior algebraic predictions. The
joint example's gap is 94249/28880. All cases, endpoint schedules and connector
sessions are preserved in `result/cyclic_robustness/20260927-attempt1`.
Its raw JSON SHA-256 is
`3d5c20a39b2c7176b6ece22bbeb464a42ea7b3bc58498c0959e227469e25ed29`.
Post-result independent review was pending at this execution checkpoint and is
completed below; these are not native solver results.

A separately frozen replication check at `ce84e9e` scales service demand,
charging resources and supply curvature together. The first run completed all
86 declared sizes and 6,448 continuous branch minima in 0.139 seconds, retaining
both physical optima at ties. Along n=40k+1, the exact cost gap is 169/(80n)
while whole-operator own-price regret approaches 8.775; per-bus regret vanishes.
At multiples of 40 both quantities are zero. This is a single operator's
price-taking deviation and is not a per-bus or independent-firm result.
The raw result in `result/cyclic_replication/20260927-attempt1` has SHA-256
`87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a`.
A non-author audit was in progress before manuscript integration; its completed
findings are recorded below.

The native recharge design is now documented, and an isolated prototype is in
development. It will use one common physical feasible-set builder, explicit
directed movements, exact charging event intervals, one finite connector and
independent replay. Synthetic source/protocol must be committed before its
first optimizer qualification. Private microcase extraction is still local;
sparse deadhead coverage may restrict the first case to a declared known-arc
graph. No operational solver job has been launched.

### Completed independent replication and robustness reviews

The robustness review is archived under
`result/cyclic_robustness/20260927-attempt1/review/`. Its non-author standard-library
auditor imports no experiment implementation and runs no optimizer. Frozen source,
design and protocol are pinned to `bd022ac32ef680446ee17bc4400843a764acb9f6`;
the raw result remains SHA-256
`3d5c20a39b2c7176b6ece22bbeb464a42ea7b3bc58498c0959e227469e25ed29`.
All 16 cases reproduce exactly: 9 positive gaps, 6 zero gaps, 1 infeasible.
The canonical `independent-audit-v2.json` reconstructs 32 branch intervals,
46 endpoint witnesses, 100 saved schedules, 161 individual bus/session replays,
805 SOC events, 26 price/LOC accounts and 3,301 rational/display pairs. All
22 corruption controls are rejected, including overlapping terminal sessions
whose energy integrals remain valid. Initial derived audit history is preserved;
the review manifest is separate from the unchanged raw manifest.

Independent battery-side elimination proves completeness of the one-/two-bus
intervals, and minimizing every endpoint-pair chord verifies the full projected
hull without importing the driver's hull implementation. Every used bus is fully
replenished; efficiency 19/20 requires 600/19 gross grid kWh. Each positive-weight
component obeys one-connector occupancy before convexification. The joint case
has physical optimum 38527/361, hull optimum 2987911/28880 and gap 94249/28880.
Its own-price regret is 307/19; at the common hull price fleet LOC is zero and
supply LOC equals the gap. The sufficient positive-gap inequalities are strict,
with 8/19 grid-kWh early headroom and fleet-cost threshold 440/19 greater than 7.
The neighborhood is within the admissible hardware model; fixing vehicle
acceptance at 30 kW does not authorize terminal power above 30.

The negative controls remain scientifically material. With the original 10 kW
early charger and fixed 20 kWh battery, either reserve or charging loss removes
the one-bus branch; the modified joint example explicitly raises both individual
and shared early power. The separate nominal terminal-power calculation proves
infeasibility below 20 kW, zero gap through 23.5 kW and a positive gap above
23.5 through 30 kW. The 24 kW gap is 5/64. Constant efficiency, zero switching
time, flexible power and no taper remain declared assumptions. These deterministic
cases demonstrate existence and sensitivity, not prevalence or field calibration.
The reviewer visually checked the robustness figure and found faithful values
and labels; synthetic units and physical assumptions must remain in its caption.

The replication review is archived under
`result/cyclic_replication/20260927-attempt1/review/`, pinned to source/protocol
`ce84e9e62b8e3f33d32010d381fd845415eff458` and unchanged raw SHA-256
`87523bcad8cdb8a3a3383391a6db42566e83498a85da547a184b8218b69cfb1a`.
The independent solver-free auditor reconstructs all 86 sizes, 6,448 continuous
branch minima, 88 physical optima, 19,604 grouped physical templates and 288,890
group-level SOC events. All 17,076 rational/display pairs agree, and all 21
corruption controls are rejected. Group multiplicities are checked as such;
they are not reported as millions of individually materialized bus traces.

Its complete projected hull is a triangle; the stored `hull_vertices` field is
only its lower boundary. The review completes the nearest-integer proof by
excluding branches below n/2, with n=1 and n=2 evaluated separately. This yields
gap 20*delta^2/n <= 5/n. Along n=40k+1, gap is 169/(80n) and whole-operator
own-price regret is 351/40+169/(40n). Per-actual-used-bus and relative regrets
vanish; multiples of 40 have exactly zero gap and regret. Both planner optima at
the tested tie sizes 20 and 60 remain recorded, with their different own-price
regrets. There is no nonzero regret limit over all integer sizes. Supply capacity,
resources and curvature scale with demand, and the deviation is a single
whole-fleet price-taking response, not an independent firm's or strategic gain.

`paper/make_extension_figures.py` regenerates the two extension figures from
the archived JSON without scientific solves, saving PNG/SVG/PDF and
`paper/figures/extension_provenance.json`. Robustness shows all 16 fixed cases;
replication displays the first 80 of 86 declared sizes and retains both tie
regrets. The editable manuscript 0.2 is being prepared. The previous reviewed
11-page PDF/hash remains version 0.1; no rendered version 0.2 is declared ready.

### Current execution gates after the exact reviews

The native recharge prototype is under preflight repair. **No native optimizer
qualification has run.** Complete repair and independent model review, then
commit the corrected source, tests, runner and prospective protocol before
the bounded 15-control qualification. Preserve native status, failed cells,
immutable tangent snapshots, backend identity and independent physical replay.
This prospective protocol's numerical admission rules do not reclassify the
earlier reuse frontier's failed FEASIBLE cell.

Next gates are synthetic native qualification, independent witness/bound review,
an explicit source-faithful known-arc operational adapter and a bounded microcase
protocol before any operational solve. Private GIRO raw sources, row identities
and fingerprints remain local; neither the exact extensions nor public benchmark
intake relax that boundary. Renewed source-head CI and all-page manuscript/figure
review are still required. No new cluster execution, merge, publication or
journal submission is established by these documentation updates. The research
goal remains active and incomplete.

### Working draft 0.2 rendering and current backup validation

The exact extensions are now incorporated into a 14-page working manuscript
with five scientific figures and all original failed outcomes retained.
Principal-researcher all-page layout inspection passed after keeping the small
reuse table with its caption. PDF SHA-256 is
`1cf8ed050ad5b6d142353996eb299c6d9578a92d7f1f3cd320ed5c08e9af4697`.
This supersedes the preceding in-preparation status for version 0.2, not the
remaining scientific gates. The version 0.1 PDF remains retrievable from its
published Git commit. CI also passed at published head
`4a8e2e52740537c4177906e32d585ad2f064246e` in run 36330964697;
this does not assert CI success for subsequent edits.
