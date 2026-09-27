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


### Implementation preflight held for focused corrections

Luna's independent review of candidate b2a5a33 passed the 48-test compact
suite but did not admit attempt3. The shared normalizer can reject N alone
before the full N+O correction ledger is emitted. The compact helper must
record the complete failure ledger first, without changing indexed behavior.
Additional promised pure controls must cover combined interval/session excess,
materialized/replay load differences, nonzero planner objective corrections,
unavailable visits, and specifically V2-to-V3 identity invalidation. Direct
comparison of all20inputs, targets and budgets with attempt2 is still pending.
See NATIVE_PATHFLOW_ORPHAN_CHARGE_IMPLEMENTATION_REVIEW_20260927.md.

Sol6_numerical_repair is working only on these scoped corrections. No optimizer
has run and no new experiment is admitted. The native-hull coordinator still
hard-codes the indexed extraction-policy identity; this is a separate later
integration gate, with its own source manifest and controls, not part of the
current20-control patch. The failed attempt2 archive stays immutable.
Sol6_cardinality_bound continues the independent exact-flow implementation;
LunaMax document worker is completing the next GoogleDoc append.

### Reviewed freeze and two bounded local runs

Published `dd5ad1659248b93d53f7f1515282d9530343567f` after independent
implementation preflight passed both scoped changes. Compact attempt3 ran
once: runner20/20,35native calls,24.706728seconds,source hashes unchanged.
Original142files total1,309,561bytes; raw manifest SHA256
c855d220a34b931804cf43c7aedf89d432aae41746c4169f3b87888120b2081a.
The repaired joint-planner cell passed the same frozen target. This is still
pending independent result admission; failed attempt2 remains unchanged.

Exact cardinality-flow attempt1 ran once under its supervisor: two public
calculations in0.358seconds, supervised0.569seconds,exit0,no timeout,no drift.
The exact certificates and unchanged source receipts are sealed. Separate
Luna Max reviewers are auditing each result without author implementation
imports. No result is admitted solely from author-written checks.

Latest Unicorn queue check found no active EGG job; other-project held jobs
were left untouched. The manager delegated a smaller nonlinear-pilot design
to Sol6. The large sensitivity campaign and publicpilot2 remain held. The
current routing uses Sol6/LunaMax for bounded worker tasks to control token
cost; the hourly heartbeat already preserves that preference. CI on the
preceding db2bf93 and b2a5a33 heads passed; dd5ad16 CI was still running.

### Independent admission of both bounded results

Both Luna Max result audits pass. Compact attempt3 preserves142original files,
accounts for35calls/31incumbents/589variables, replays31witnesses/69sessions/
253SOC events, and rejects25corrupted copies. The sole projected positive
orphan is1.2214e-12kWh; largest complete correction1.2261e-12 is below the
single1e-8budget. All16numerical certificates and4expectedinfeasibilities pass.
This admits the synthetic compact policy only, not its hull integration.

The exact flow audit reconstructs778arcs per full37service depot case,
including both direct and depot modes, verifies exact primal-dual equality,
35realconnections and2unmatched paths. New ideal stored-input lower bounds
are404.924239883878 and414.394469217211, versus prior301.315343883878 and
305.633807883878. Separate native numerical upper witnesses remain408.5331369
and433.7460862; no exact physical gap/optimum is claimed. Twelve certificate
corruptions plus two direct-only omission checks are rejected. The reviewer
initially omitted depot parallel modes; the lead identified this and the
reviewer corrected its own code. No author source or raw result was changed.

Sealed independent review manifest hashes: compact
a73c1870fe0243c5b11baf7856efab861277df7852c5386972c604858500d895;
cardinality08912d142a4026e28bd6e4ec0f0fb4876fe58cfc7dcea0e18ddc68b325d34f73.
Sourcefreeze dd5ad16 CI passed. Raw evidence backup is5d7f256. Sol6 now owns
prospective hull-policy integration; LunaMax independently reviews before any
8-control execution. The selected next nonlinear pilot is one predetermined
depot15case with34-minute complete cap after qualification and preflight.
The large sensitivity campaign remains unadmitted.

### Shared document and next work package

The Google Doc append “Verified compact qualification and stronger ideal fleet
bounds — 27 September 2026” is saved. Its 85,964-byte pre-append Markdown is
an exact prefix of the 88,414-byte final export; the heading occurs once and
all six published links are present. The first insertion landed before two
existing paragraphs; prefix verification caught it, undo restored the original
exactly, and the corrected append passed preservation checks. The current PDF
is unchanged. After-export SHA256:
d5569b56b61e2e44b45228fb422e88741968c780ee917cb9284a5af926a7a809.

The lead shelved its own unexecuted flat-pilot2 candidate to focus on the
selected nonlinear question. All four tracked files were restored to HEAD;
the exact 15,386-byte patch remains at the outer research directory
`deferred-flat-pilot2/unexecuted-candidate.patch`, SHA256
913392f0fe8a8b4bffc89fa250535bbd48516a689f47811ca77c2ebca041aba0.
No attempt or scientific result was removed. Sol 6 is implementing the new
nonlinear runner in separate files while Luna Max reviews the final small
hull-policy correction. The old cluster public checkout and its raw outputs
remain untouched; future cluster work will use an isolated checkout.

### V3 hull qualification executed; independent result audit pending

Published source 03d1da2f3629e722784e97891a8590060fa676ad after Luna's
independent preflight passed 96 scoped pure tests. The same eight frozen CBC
controls ran once in the exclusive compact-hull attempt2: runner 8/8 certified,
36 native calls (21 pricing, 15 master), nine exact-polish transfers and
24 checks, 12.1265-second controller / 12.267-second supervisor. No timeout or
source drift. Its 62 original files total 1,284,737 bytes; raw manifest SHA256
c3d9da88195161ddd2c054800e4d0a5944998a03b623730a771e7ce9bbb5644b.
The independent no-author-import result audit is underway; runner success alone
does not admit downstream use. Sol 6 separately prepares the small nonlinear
public orchestrator; Luna Max prepares a short same-source Gurobi qualification
plan. No cluster qualification or nonlinear public run has been launched.

### Prospective cross-suite metadata assertion repair

The lead found that the older energy-band equality test excluded oracle and
state identities but not the newly declared extraction-policy metadata. Its
comparison failed despite identical scientific controls. Before editing, all
19 current hull source files were verified against the frozen 03d1da2 hashes.
The test now excludes that expected metadata difference and separately asserts
the new policy identity for every control. All six related pure suites pass:
195 tests in 0.69 seconds. No native algorithm or archived result changed and
no optimizer was rerun. Future source checks should read the pinned Git blobs,
not require a working checkout to remain permanently at an old revision.

### V3 CBC hull result admitted

Luna's independent no-author-import audit passes all eight compact-hull cells:
21 complete-branch pricing minima and global Fenchel checks, 15 exact stored-
number PWL master minima, physical replay, mixtures, polishing, retained-state
policy checks and full accounting. All 48 deliberately corrupted copies reject.
The original 62 files are unchanged. Frozen source blobs and the completed-run
source-unchanged receipt are checked separately, so later source evolution does
not invalidate reproducibility. The lead verified every review-manifest entry;
REVIEW_MANIFEST.json SHA256 is
c17175c033921553a9f1d58dc5ddb083e412c2fcde3cb4c71ec639b226091166.
This admits the declared CBC synthetic hull fixtures, not GRB or operational
results. Latest published compatibility-fix head db7458e passed hosted CI.

The prospective nonlinear pilot permits complete, validated hull evidence
returned with budget_exhausted status to continue through the already budgeted
own-price stage; it preserves that status and does not call it optimal. Missing
evidence or hard timeout still stops the attempt. This is a prelaunch protocol
revision, with unchanged caps, inputs and native call limits. Independent
preflight is closing saved-column subset/order handling and exact 20+8 GRB
qualification parity. GRB qualification wrappers are separately under review;
no new cluster job has been submitted.

### GRB physical qualification submitted once

Both new implementation preflights passed. The complete source freeze is
227da22074201c583dbcfa971863c8f3c41d7391. A thin Git bundle transferred all
new public research commits since 282e00b; local and remote bundle SHA256 both
fc450be0a6e0081d4cc1eab775d6a7893e515801b9b5032b25a370db9986e337.
A fresh detached worktree at /home/nc437/egg-grb-physical-v3-20260927 preserves
the old public checkout and raw outputs.

Slurm job559429 is the sole GRB physical20 submission. The initial receipt is
PENDING/Priority, one CPU,8GB,30minutes,Requeue=0, and
ExcNodeList=scaglione-compute-01. Its exclusive submission sentinel and copied
local receipts prevent accidental resubmission. A shell initialization attempt
first stopped on the site Slurm script's unset INCLUDE variable, before any
intent or job existed; loading that site script before enabling nounset fixed
the invocation. No scientific execution was repeated. The physical result
requires independent audit before any separate GRB hull submission. The
public nonlinear pilot remains gated.

### GRB physical run retrieved; independent audit pending

Job559429 completed with exit 0 in 49 seconds, one CPU, peak RSS101884 KiB
on snavely-cpu-02. The runner reports all20 controls passed,35 native calls
and36.142 seconds; these remain unaudited result claims. No retry occurred.
The full transport archive SHA256 is
d3939c50cef80925139e605b903ab21ac79e18a318583e75084e163b65a72b91.
The original146-file manifest SHA256 is
14ce0b4c04eeaeb6b8bafe72f252a9de7f92a723023b11f2c4a82dab83f06adf.
The lead verified transport, exact raw file set, all byte counts and hashes,
then exclusively installed the full raw attempt and sibling launch receipts
in the local canonical paths. Full archive and final Slurm accounting remain
under the outer research-20260927/cluster/grb-physical-559429 directory.
Luna is independently auditing science and reviewing a public copy separately.
Full license-bearing stdout is preserved locally and remotely; nothing inside
the raw attempt is rewritten. The next hull stage remains gated on admission.

Sol also completed a prospective exact stored-row argument for a native
two-bus cut in the two named public cases. It is a design note, without model
changes, optimizer calls or changes to the fixed nonlinear pilot. Luna's
prospective figure/table plan preserves signed gap and regret intervals and
distinguishes physical schedules from convex-mixture means.

### GRB physical qualification independently admitted

Luna's solver-free audit passes all20 fixed controls:16 certified and4 expected
infeasibilities,35 calls,31 physical witnesses and26 rejected corruptions.
Maximum whole-incumbent correction is97/4503599627370496 kWh, below1e-8.
The auditor verified exact stored matrix/objective/bound reconstruction,
physical replay, exact CBC parity except backend,15 source pins, source-stable
receipts, runtime and Slurm provenance. Signed-zero representation is preserved;
a1e-12 tangent-formula comparison allowance is explicitly separated from exact
reconstruction using actual stored coefficients, with a1e-9 corruption rejected.
The lead verified the independent review manifest and the solver-free physical
admission gate. This admits only the declared physical GRB synthetic controls.
The public copy retains126 original science files plus unchanged manifest and
all5 launch files;20 whole license-only stdout files are omitted by declared
hash. Full local/cluster originals remain intact for the full audit/gate.
The next step is a new published source freeze and one separate hull job.
The nonlinear public pilot remains held until that result is independently
qualified. Hosted CI passed for source227da220.

### Published admission and separate GRB hull launch

The admitted physical checkpoint was published as
62976f11ecf35c837b0573079892ae5095e846b9 and PR56 updated, still draft/unmerged.
Source-bundle SHA2560411ebb6e217a4f868a869b4f20c780172b6c62ec874feb4f546c705d10485fb
matched locally and on Unicorn. Sol owns the sole hull submission, job559602,
in /home/nc437/egg-journal-grb-hull-20260927. A preparation heredoc error
stopped before any intent/job; read-only checks established no submission,
and the corrected continuation filled only20 missing license stdout files.
All152 physical raw/launch files then matched and the pure admission/source
preflight passed. No scientific retry occurred. Latest saved scontrol reports
COMPLETED, exit0:0, runtime26seconds; one CPU,8GB,15minutes,no requeue,
default partition and reserved-node exclusion, WorkDir/Command all verified.
Local intent, submitted receipt and scontrol are saved under the outer
research-20260927/cluster/grb-hull-559602 directory. Results remain unaudited.
The next hourly work package is retrieval, final accounting and independent
hull audit; the public nonlinear pilot remains held.

Luna appended the verified physical-GRB/CBC-hull milestone to the original
Google Doc. Before88,414bytes SHAd5569b56b61e2e44b45228fb422e88741968c780ee917cb9284a5af926a7a809
is an exact prefix of after89,527bytes SHA1377215d64b38be24a2934aff9c1b9962bc2bce58bba58f5763654f6884aaccc;
the new heading occurs once and Saved to Drive was observed. PDF0.4 unchanged.
This bounded work cycle ends with a precise hourly handoff, preserving the
user's cheaper-model preference and avoiding idle Astra queue monitoring.

### Independent GRB hull admission and nonlinear release preparation

The prior goal turn was progress, with published physical admission and a
completed hull job. This turn retrieves/seals job 559602 and independently
admits all 8 GRB hull controls: 36 calls (21 pricing/15 master), 9 polish transfers,
24 checks, 44 replayed charging sessions, 48 corruptions rejected. Raw 66-file
manifest SHA a8e1a883f03c5f8e1d6a710ec70500836f950404b3158331a2ffe668c753acf4
and review-manifest SHA bc81789519f1f2bb737b7a8f864043f9f58744328805f9f8a64e768bf75538b5
were verified by the lead. Every control's exact stored-coefficient master,
global Fenchel bound, retained state, physical replay and target enclosure
passed. The original bytes and all failed earlier attempts remain intact.

The lead passed the actual pure nonlinear 20+8 admission gate with the pinned
physical/hull audits. No attempt or optimizer was created by that check. The
implementation review required a bold-delimiter-only fix for the literal PASS
marker; no science/code/budget changed. New source publication is required
before the separate fixed 34-minute pilot. Public hull records omit only 8
whole licensing-only stdout files, named and hashed outside the raw attempt.
The full 66-file archive remains local/cluster.

Luna prepared concise manuscript insertions, corrected to keep exact ideal
bounds and numerical witnesses separate and preserve the original pilot
intervals. Sol is exploring an exact fixed-route/timing rational repair of one
archived two-bus witness outside the repo, without changing the fixed pilot.
Neither that candidate nor the pending nonlinear result is admitted evidence.

### Fixed nonlinear public pilot launched once; result pending

The independently qualified GRB physical and hull gates admitted the fixed one-cell depot-15 nonlinear pilot. Source commit 80eb69544f568a7ed346f0d603004a10f61c481a was published. Two initial SSH transport calls failed locally before remote execution; their receipts remain in two outer `research-20260927/cluster/nonlinear-dispatch-ambiguous*` folders. Root then used fresh escalated-network `squeue`/`sacct` checks and confirmed the attempt and submission sentinel were absent before making exactly one `sbatch` submission. Local SSH with `ControlMaster=no ControlPath=none` succeeded. There was no scientific retry.

The resulting job is 559683, currently RUNNING in `/home/nc437/egg-sistig-nonlinear-20260927`, with remote exclusive sentinel `nonlinear-submission-20260927`. Local submission evidence is under `../research-20260927/cluster/nonlinear-559683/submission`. Live `scontrol` reports ReqTRES cpu=1/mem=8G, CPUsPerTask=1, ALLOCATED cpu=2/mem=8G, node snavely-cpu-16, 36-minute limit, no requeue, and exclusion of scaglione-compute-01. The actual allocation must not be described as one CPU. No stage result has yet been observed. Next steps are authoritative queue/accounting for this job, transport sealing once terminal, independent nonlinear result audit, and post-run verification of native thread 1. Observation failures must not trigger restart or resubmission.

The separate exact rational depot-15 two-bus witness is packaged as a candidate at `result/sistig_exact_witness/20260927-depot15-attempt1/`; Luna is independently reviewing it. It is not yet an admitted exact physical feasibility result and does not change the pilot or establish cost optimality.

### Nonlinear pilot terminal failure preserved

Fresh scoped sacct at 21:30 UTC reports job 559683 FAILED 1:0 after 4 minutes
22 seconds; batch peak RSS 351628K, allocated CPUs 2. Full private transport
SHA 69491c8695119eed650b42dcb1c8ead7efc347d20f3f53223d29d4d15fb3c4f3
was verified locally. The lead checked all 15 manifest entries and the exact
file set plus MANIFEST and the declared later Slurm wrapper receipt; raw
manifest SHA 796a9c26b968a35a616269043708ba71f95defe1848547ce191d12ecc11f0c2d.
Canonical raw was installed exclusively, without editing any original output.
The summary reports planner failure with returncode 2, elapsed 243.2176 seconds,
complete accounting of two starts/two returns, no hard timeout and unchanged
sources. Hull and own-price were unstarted. No cause or scientific conclusion
is inferred until independent audit; no retry or resumed stage is authorized
by this status. A separately frozen prospective amendment may be considered
only after diagnosis. The original failed attempt remains immutable.

### 2026-09-27 — independent nonlinear failure audit and depot-15 witness admission

The independent review at `research-20260927/agent-notes/nonlinear-pilot-result-review/REVIEW.md` verifies the sealed failure archive without reading stdout/stderr contents. The worker raised `TimeoutError: Scientific routine/admission cap exceeded` at 242.315324 seconds, 2.315324 seconds past the 240-second planner routine cap. The child returned at 243.217558 seconds before its 255-second hard stop; the saved receipt has `hard_timeout=false`. Job 559683 ended `FAILED 1:0` after 00:04:22, with two CPUs allocated and 351628K peak RSS. The archived batch directives exclude `scaglione-compute-01`. Two GRB calls returned and the planner raw result preserves a partial solver-conditioned interval, but the final assessment package is absent; hull and own-price were unstarted. The scientific pilot is **failed/incomplete and not admitted**, with no full-pilot gap or regret result. The 15-entry original manifest SHA remains `796a9c26b968a35a616269043708ba71f95defe1848547ce191d12ecc11f0c2d`.

The separate depot-15 rational candidate now has independent PASS for exact ideal stored-input feasibility. Its two routes cover all 37 services and its exact replay supports a two-bus feasible schedule; the reviewed one-bus obstruction gives the matching lower bound. Thus minimum fleet is exactly two only for this declared depot-15 ideal case. The ideal flat synthetic-cost optimum is enclosed by the exact stored-input interval `[404.924239883878…, 408.5331358838777…]`; it is not identified. Candidate package manifest SHA is `18614a45e1506398cf05665a88b4c717ca7bc76e5eaeb3a48639ef60d4828b70`; independent-review manifest SHA is `ba09db351651c6ce9d7cf8cd85460745f377f8772c0cd98f8f23e533077b5af3`. See `doc/SISTIG_EXACT_PUBLIC_WITNESS_ADMISSION_20260927.md`. This distinct witness does not cure or upgrade the failed nonlinear pilot. The portable failure review requires the complete private archive; a publication subset that omits declared licensing-only stdout files cannot be replayed by its full-manifest driver. No Git, cluster, or Google Doc action was taken in this update.

### Exact nonlinear enclosure and prospective v2 timing review

The independently checked uniform-price/Fenchel certificate gives ideal depot-15 CH lower 424.365880667204…; independently evaluating the rational feasible witness gives CH≤D≤512.7694256264009…. These exact analytic bounds do not come from the failed pilot and establish neither optimum nor a positive gap. The lead verified the three candidate and three review entries against manifests e4729fcffca456729d7464861228f1f6530b572a3b352fe5abbd63ebd25ec30f and fc7ebbe2d1b5636a430855083b817bc3baf3373f68041ab599c2bc22318a8b19. See SISTIG_EXACT_NONLINEAR_ENCLOSURE_20260927.md.

Sol implemented only a prospective timing allocation change: native 225/1380/225 seconds inside unchanged routine 240/1440/240, with v2/attempt2 identity. Luna's independent review passed; sixteen author pure tests, six reviewer focused checks and batch syntax checks passed. Root ran the actual same-source GRB 20+8 admission gate successfully over 41 source pins, with no optimizer or attempt creation. All native model/replay cores remain byte-identical. Root authorizes one new attempt2 after publication, with one freeze inside sbatch and all original caps/resources/exclusions preserved. A repeated failure must not trigger automatic attempt3, a budget increase or model changes. The first failed attempt and raw outputs remain immutable.
