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
intervals, all 15references complete. Cold/depleted_f20/return_base remains a
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

### First native recharge qualification — 12/15 passed, three preserved failures

The independently reviewed source, tests, runner and prospective protocol were
frozen at `d37878392f0848d34f28921c97b6e8d8e6533a77`. The first CBC execution
attempted all 15 controls in 23.5736 seconds; 12 passed and three failed during
witness extraction/replay. `cyclic_own_price` rejected a negative/nonfinite
extracted charge; `preserved_reserve_planner` and `serial_connector` rejected
simultaneous charging. Native starts/status/bounds were preserved before these
exceptions, all source hashes remain unchanged, and every later cell was still
attempted. Raw incumbent variable values preceding failed extraction were not
fully recorded; that diagnostic limitation must not be filled with a rerun
represented as the first result. The immutable raw tree has a separate manifest.

The first run therefore **does not qualify the native adapter**. The positive
analytical construction and exact independent audits are unaffected. Author
and independent reviewer are diagnosing the software/witness failures without
new optimization. Any correction requires new source/protocol freeze and a
separate attempt retaining this failure denominator. No operational or cluster
solve is yet launched. The 14-page draft and exact extension audits were backed
up at `200e0e6`; CI for that newer head remains to be checked.

### Corrected native qualification — first V2 execution passes 15/15

V2 was independently reviewed and frozen at
`997575d049a66d952a0cb8d79f974f7ba5f4ccf0`. Sixty-two pure/fake tests passed
with native imports blocked, and all 15 complete control inputs/targets were
verified identical to attempt1. The only changes are pre-decoding raw-variable
capture and explicitly bounded numerical witness conversion. Positive energies
are retained; exact cumulative proportions contain serial sessions within their
original intervals. Negative-to-zero corrections and materialized capacity
excess share a whole-incumbent `1e-8` kWh budget, followed by the unchanged
numerical replay/objective/bound admission checks.

The separate `result/native_recharge/20260927-attempt2` first execution passed
15/15 (12 certificates and three expected infeasibilities) in 33.7343 seconds,
with 30 returned native calls. Its 107 raw files total 706,562 bytes and are
manifested before independent result review. The result is numerical and
solver-conditional. Attempt1 remains 12/15, with its unavailable failed
incumbents acknowledged. No exact causes or corrected witnesses are retrofitted
into that earlier run. Independent V2 result audit is pending before the planned
single bounded Gurobi qualification on Unicorn.

The Google Doc's analytical-extension milestone was appended and verified saved
to Drive, with previous text retained and a pinned version 0.2 PDF link. A later
native/operational update will record completed gates, not predictions.

### Independent V2 audit passes; cluster qualification admitted

Independent reconstruction verified all 107 V2 raw files, 27 raw incumbents and
1,030 variable values, every declared model constraint class, 27 saved witness
instances, 60 sessions, 215 SOC events and all native objectives/bounds against
analytical/PWL fixture minima. Sixteen corruption controls were rejected.
All 12 certificate intervals enclose independently derived optima; three expected
infeasibilities agree analytically. One recorded negative-to-zero correction is
5.166411062336897e-15 kWh; maximum combined correction is
7.105427357601002e-15 kWh. These are raw floating residuals under the frozen
numerical policy, not exact physical arithmetic. Attempt1 remains FAILED.

The separate bounded Gurobi replication is now admitted under
`doc/NATIVE_RECHARGE_CLUSTER_PROTOCOL_20260927.md`. Its launcher passed a
second agent's review. No source/target/budget change is permitted between the
corrected local design and this backend replication. CI passed at published
`ba84b11bceb878a7436644ffe62048caa879e945`: 883 tests in 212.08s, run 36332111437.
The newly added solver-free audit CI commands also passed a local integration
check; later published-head CI must still run.

Further private-source admission found off-depot recharge and missing explicit
movements in the proposed 17-service pair. It is not native-model-ready and
must not be silently translated with zero travel. A CC BY 4.0 public Figshare
archive (DOI 10.6084/m9.figshare.26088190.v1) has been downloaded and matched to
its publisher checksum for data-only schema inspection; no supplied code ran.

### Gurobi replication completes; independent audit passes

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

The native milestone was appended to the existing Google Doc and verified saved
to Drive. Clipboard verification retained the entire preceding text and exactly
one new heading (68,616 total characters). It records both successful native
qualifications, the preserved first failure, public-data direction and material
decision policy. The reviewed linked PDF remains version 0.2. CI at `24c7e4e`
passed 888 tests in 172.41 seconds plus the evidence reconstruction step.

### Timing qualification completed; independent result review pending

The first half-minute CBC gate at `46fd6af573a240d54abb8ea8d7cf7b79cc0af0ee`
completed all 19 controls successfully (15 certificates, four expected
infeasibilities). Its raw attempt is manifested under
`result/native_halfminute/20260927-attempt1`; source hashes are unchanged.
This supersedes the active-session entry. Do not rerun. Independent artifact
review must pass before the timing extension supports a timetable result.

### Native hull first execution failed qualification

The8-cell native hull attempt at `f549100587cdf561c978e145e73e86dbadc9f27e`
is complete, not active:2 cells certified,4 exhausted the64-master-call cap,
and2 retained successor states correctly blocked after their predecessor failed.
Supervisor exit1, no outer timeout,14.2354s. Raw evidence and all failure work
are manifested in `result/native_hull/20260927-attempt1`; do not rerun or rewrite.
The physical timing gate independently passed all19 controls; this new failure
concerns the separate hull restricted-master refinement and is under diagnosis.
No timetable solver or hull scientific claim is admitted by partial success.

### Independent timing audit passes; hull refinement diagnosed

Independent review confirms the complete19-cell timing attempt:135 original
files,30 finite analytical/PWL minima plus4 infeasibilities,1,075 raw variables,
64 sessions and233 SOC events;22 corruption controls rejected. The coincidence
cell preserves native8.99999998 versus exact9, correctly enclosed by its fixed
guard. No residual was rounded away. The final review package supersedes the
provisional audit scripts checkpointed in the previous commit.

Both hull reviewers identify a restricted-master precision stall: near-optimal
quadratic objective values coexist with a still-open first-order pool criterion,
and identical final tangent/mixture points repeat. The nominal saved inner
mixture has true objective94.8875000067 but pool gap about0.0004944, above1e-6.
The V1 final summary also misses improved UBs seen inside an interrupted inner
master; those remain visible in raw traces. This does not certify the failed
cells. A separately reviewed/frozen V2 will use bounded exact-rational pairwise
simplex polishing and stream the best feasible UB. All original failures remain.

CI passed at hull/public-input freeze `f549100`, run36334386899. Native physical
source remains unchanged; compact path-flow code and a20-control gate are under
preflight with no solver execution. A new participant-normalization derivation
clarifies that reserved-resource small operators have vanishing individual
regret in the replication family; it is pending independent review and does not
change the already established whole-operator formula.

## Compact formulation, repaired hull and participant review

The separately frozen compact model (`ebb146e`) passed all20 synthetic controls:
16 numerical certificates and four expected infeasibilities,35 native calls,
24.5333s. Independent audit reconstructed31 raw incumbents/589 values,
68 sessions/252 SOC events and every analytical/PWL minimum;25 corruptions were
rejected. Full raw manifest and independent derived package are retained.
This establishes the small-control gate, not public-case runtime or superiority
of one formulation.

The hull's separately frozen V2 (`186c987`) returned eight certificates on the
unchanged eight-cell design,36 native calls and nine rational stored-projection
polishing transfers. Supervisor22.4423s, exit0/no timeout. Its62 raw files are
manifested before non-author review. The first attempt's2/4/2 outcomes remain
unchanged. Native physical witnesses and global lower bounds remain numerical.

A separate participant-rights derivation passed independent exact checks of all
88 archived optima. With one A/B pair and reserved early/terminal connectors per
participant, individual regret is bounded by20/n; summed regret matches the
whole-operator formula only in this explicit symmetric institution. The paper
now distinguishes these ownership and normalization choices. A focused primary
PDF check of Kerdreux et al. §§1–3 supports aggregation context, without treating
its classical summand bound as a proof of the EGG-specific incentive formulas.

The complete37-service public pricing pilot is in final preflight, with two
unchanged one-depot cases, flat synthetic price0.2 and bus cost100. Its candidate
allocation is one CPU/8GB/12minutes, reserved node excluded; live queue/policy
read found capacity and only the previously held user jobs. No public job yet.
Latest published freeze186c987 and the three earlier checkpoints all passed
GitHub CI. Manuscript0.3 has been rendered to17pages/sixfigures and is under
independent layout review; author corrected crowded public-figure labels while
retaining all37servicebars and unchanged energy totals.

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


## 2026-09-27 17:55 UTC — exact matching audited; energy-band gate held

Matching attempt1 at freeze3014d04 completed two exact calculations in0.204274s
under a0.280112s supervisor. Independent no-author-import/no-optimizer review
reconstructed both37-by74 assignment matrices,2,035 allowed-edge inequalities
and74 nonpositive column potentials per case, primal/dual equality, all modes,
coverage, runtime/source/manifest identities and12 corrupted certificates.
The exact ideal stored-input lower bounds display301.3153438838777 and
305.6338078838777; each relaxed cover is one path and is not a physical result.

Energy-band V2 final independent preflight PASS preceded published66b7054 and
the20-control attempt2. It completed19/20; joint_planner aborted extraction
after its second OPTIMAL native call because1.2214110437041203e-12 gridkWh was
assigned to an exactly unselected movement. The strict old policy correctly
refused it. All142 raw files686302bytes are immutable and manifested, SHA
dfd956c8da49d03bfec3db77a02396f8974ac4d6ba5ca3a95d713302fa33ebe3.
Independent full/failed-cell audit and author diagnosis are active;8hull/public
V2 gates are held. No automatic retry or retrospective zeroing. A durable
prospective numerical policy will be independently reviewed if needed.

NewFigure7 independent review PASS: every37servicebar per case, all41sessions,
235SOCpoints (4initial+231subsequent), ownership/captions and byte-identical
PNG regeneration checked. Manuscript source0.4 now contains a self-contained
certificate method, ideal compact model appendix, sufficient open-neighborhood
proof, evidence table, renumbered public table and explicit time-independent
deadhead scope; scientific/layout review of these changes remains.

One compact17:54UTC Unicorn check found no EGG job active, only unrelated held
jobs; all left untouched. Hosted CI succeeded for3014d04(run36338020969) and
66b7054(run36338309581). No important user decision or exceptional compute
commitment is pending. The main unresolved science remains the matched nonlinear
public physical/hull/regret comparison, not the incidental extraction exception.


## 2026-09-27 — reviewed one-bus obstruction and manuscript checkpoint

Independent exact reconstruction confirms that neither declared public graph
can cover all37services with one bus: all36chronologically forced connections
are direct, without a depot recharge opportunity, and service energy alone
is889.1175194194kWh against400kWh capacity. First16services and their forced
legs require428.6372586702kWh by14:07. This proves an ideal stored-input lower
bound of2buses. The existing audited2bus witnesses provide a numerical upper
under the declared replay policy, not exact rational physical feasibility.
The proof, diagnostic and result are preserved with a separate independent
review. Original cost intervals and matching results remain unchanged.

Sol6 reviewed newsource0.4method, abstract, evidence table andAppendicesA/B: no
blocking scientific inconsistency. LunaMax reviewed22candidatePDFpages with
no clipping/overlap/glyph defects; references pagination is being repaired in
a separately named candidate. GoogleDoc milestone “Verified manuscript and
qualification update — 27 September 2026” was appended and SavedtoDrive; only
append/currentstate were verified, without a complete pre-edit snapshot. PR56
now describes all current evidence and remaining nonlinear study accurately.

The prospective compact orphan-projection design awaits independentreview;
no optimizer has been rerun. A cardinality-constrained exact matching design
could exploit the reviewed one-bus lowerbound and is not executed. Routine
work now uses LunaMax andGPT6Sol; rootcoordinates publication/decisions.
