# EGG research journal — 28 September 2026 UTC

## Computational expansion

The user wants a substantial computational paper and suggests learning routes
to avoid repeated solving, beginning with reliable iterative optimization. This
continues the research beyond the delivered v0.5 draft. The referee-style critique
remains accepted: reduce audit prose, improve the public computational evidence,
make price-taking versus strategic behavior clear, add foundational citations,
and move the next manuscript to LaTeX. Historical results and PDFs stay intact.

Work is split by cost and purpose. GPT-6 Sol implements a bounded development
screen; Luna Max inventories public instances and primary learning literature,
prepares the next manuscript scaffold, and will independently review the screen.
Root sets the scientific comparison and resource budget. The existing hourly
research heartbeat is active again and should remain quiet on unchanged state.

The public inventory identifies 20 operator base timetables in the pinned Sistig
archive; only the 37-service Hildenbrand base is currently adapted to our model.
Its two depot variants must remain in one data-split group. The archive has
105-, 131- and 137-service candidates for expansion after input checks. Old
synthetic generator runs have a different terminal-SOC policy and cannot simply
be pooled with fully replenished NativeCase results.

The first screen is eight case–market combinations: two small synthetic cases
and both Hildenbrand depot variants, each at two posted supply-cost intercepts.
It runs a planner, two hull arms (cold and retained), and an own-price response
when a valid planner witness exists. All cases are development. The two-service
market preserves the known counterexample as a useful mechanism check; the
three-service case exercises repeated depot visits. This is a diagnostic screen,
not evidence that the method scales to many timetables.

The prospective protocol distinguishes algorithm work limits from hard complete
stage deadlines. All time, incomplete bounds and failures count. The resource
ceiling is one serial job requesting one CPU and 8 GB, with a two-hour allocation,
one native thread, no retry/requeue and the reserved node excluded. No new job
has been submitted at the time of this entry. The worker source and exact
manifest must be reviewed and published before launch.

The focused literature review distinguishes learned column selection, pricing
proposals and predict-and-repair. Our current hull columns are complete fleet
plans; route-level Dantzig–Wolfe pricing would be a different formulation.
Nearest-neighbor reconstruction and retained plans are required practical
baselines for any learned proposal. Learned feasibility, repair and global
verification must be timed separately; a predictor alone does not prove that
no better complete fleet plan exists.

An additional bounded offline probe is authorized on the old three-column
public restricted pool. It asks whether a numerical quadratic-program proposal
followed by exact simplex/replay checks can avoid growing rational arithmetic.
It uses existing saved columns and no new global pricing or cluster solver;
any improvement is only a restricted-pool result, not a new public hull bound.

The probe completed: a numerical proposal rounded to an exact simplex reduced
the three-column pool residual from approximately 0.00202 to 7.23e-8, with only
a 3.60e-8 objective decrease. Total probe function time was 0.244 s, excluding
imports and output writing; the proposal solver itself took about 0.0025 s.
The negligible objective change alongside a much smaller residual explains why
this is a promising way to unblock further global pricing, rather than a new
substantive cost result. It does not measure full-solver acceleration. Details
and reproduction are in research-20260928/computational-design/POOL_BOTTLENECK_PROBE.md.

## Next handoff

Finish the screen implementation and focused independent review, publish the
source and prospective protocol, freeze and submit once, then retain launch
receipts. Analyze stage bottlenecks and equal-quality reuse comparisons before
a larger sweep. Append one consolidated Google Doc update at a concrete launch
or result milestone. Continue the computational manuscript as new evidence arrives.

## First screen submitted

The reviewed execution source e39bc7e31ea21dae64365c31fa88a85e4b0de349 was
published and submitted once as Unicorn job 569799. At 03:26:12 UTC it was
PENDING (Priority); no allocation or frozen input existed yet. The dedicated
checkout is /home/nc437/egg-computational-screen-20260928. Nine focused harness
tests and independent implementation review passed. The current scientific
core is unchanged; outcomes are pending. The source's CI run is 36373363756.

A standalone numerical restricted-QP proposal helper is also complete with five
focused tests. It is not integrated into this baseline and makes no certificate
claim. Eberbach source-input adaptation planning proceeds independently.

At 03:28:45 UTC the job was RUNNING on snavely-cpu-01 with 1 CPU/8 GB.
Frozen input SHA-256: b36b15a5b9ac8945cff3b4cfd5e8441c705c3c536870f7a34c3d08e7f6f2dca2.
The execution commit's full CI run 36373363756 completed SUCCESS. No stage
outcomes are claimed before collection and analysis.

The Google Doc now contains one “Computational program update — 28 September
2026” append. Saved-to-Drive and exact prior-export prefix preservation were
verified; public receipt is under research-20260928/agent-notes/. Eberbach's
input-only plan confirms 105 services, 14 stops, one depot and 9 routes. Its roughly
10,000 movement choices warrant a model-size estimate before the next solve.
The optional one-trip-per-bus construction is a feasibility attempt, not a
necessary condition for the chained fleet model.

## Diagnostic reporting preparation

The 03:49 UTC follow-up made one compact queue check: job 569799 remained RUNNING
on one CPU/8 GB, with 23:10 elapsed. No additional job was submitted and no stage
outcomes were collected. The subsequent documentation/proposal source d8fc860
passed full CI (36374758707).

This follow-up prepares the completed-attempt report rather than expanding the
experiment. The report must preserve all 32 declared stages, keep execution
failures distinct from native solver status, and include each hull arm's first
and second states when comparing total work. Missing pricing/master time stays
missing; it cannot be reconstructed as routing time from a remainder. Human
tables use approximate numerical bounds while machine exports retain the reported
fraction strings. Neither representation upgrades native results to ideal-model
exact proofs. The Google Doc's launch update remains current; the next consolidated
append should describe verified findings after the run, not repeat queue status.

The reporter is complete at `src/experiments/computational_benchmark_report.py`.
Five focused tests passed, covering timeout/native-status precedence, missing times,
32-stage accounting, incomplete files and stable-manifest checks. It consumes
summary/count fields only; detailed pricing/master event timing and independent
scientific interpretation remain for result analysis. No optimization was run
and no archived scientific outcomes were read for this implementation.
Luna's independent static review confirmed the accounting and identified a
misleading overall-validity flag. Root renamed it to supervisor integrity,
clarified that stage success and scientific validity remain separate, and reran
the five focused tests successfully. No full-suite rerun was needed locally;
the standard GitHub CI gate will run on the backup commit.

## First screen collected and analyzed

The 04:50 UTC follow-up found job 569799 had completed successfully. Whole-job
elapsed was 35:57, with one CPU/8 GB. The full private archive and all manifest
files were verified; the original attempt remains unchanged. Reporter commit
6242218 passed full CI. The screen accounts for 32 stages: 10 native-certified,
10 bounded, 9 budget-exhausted and 3 ineligible, with all 29 launched stages on
time. Sol prepared the descriptive tables/figures and Luna checked the claims.

The measured public bottleneck differs from the earlier three-column probe:
about 173 of 184 seconds per hull stage was recorded native pricing time, while
polish was roughly five milliseconds. The second returned column arrived too
late for another master solve. In contrast, the shifted multivisit case hit a
rational-bit limit. Next work targets time allocation and feasible-pool reuse,
with the numerical QP addressing the separate arithmetic issue. Public bounds
remain broad; no public optimality-gap, reuse-speedup or learning claim follows.
The cyclic example alone provides a certified reuse comparison, with shifted
pricing requests reduced from three to one and preparation time included.

A closed-form two-column diagnostic uses the saved public cold pools, with no
new pricing solve. Physical-column and exact stored-number mixture replay reduce
this run's upper costs by about 37–69 units. Roughly 0.1 s per-pool processing
excludes imports, case construction and output writing; it is additional work,
not credited to the frozen run. The mixtures are convex-hull points, not individual
fleet schedules. Saved lower bounds are unchanged and stronger compatible older
bounds remain valid. This isolates a concrete improvement: reserve time for a
final mixture update when an expensive pricing call returns a new plan.

The curated public evidence ZIP contains 101 original scientific JSON files,
including frozen inputs, witnesses and receipts, with a complete selection
manifest. The full private archive also preserves the omitted logs and JSONL.

The scientific milestone is backed up at 967f603. CI found trailing whitespace
in Matplotlib SVG output; export normalization at aa7442b preserves all figure
content, and the full branch whitespace check passes. Full CI 36381206518 then
completed SUCCESS. The original Google Doc now contains one consolidated
findings/next-experiment update, with prior content preserved byte-for-byte in
the Markdown export and saved-to-Drive verified. The receipt is under
`research-20260928/agent-notes/google-doc-screen-results/`; full Doc exports stay
private. No new cluster job was launched during this analysis follow-up.

## Matched reserve and feasible-pool pilot prepared

A separate 24-cell hull pilot now isolates two changes suggested by the first
screen: preserving ten seconds inside the pricing budget for processing newly
returned fleet columns, and reusing feasible columns from a bounded predecessor.
Legacy cold, reserve cold and reserve reuse arms each pay for their own initial
solve. Only replayed physical columns cross markets; target mixtures and global
bounds are rebuilt. Strict historical reuse behavior and prior results remain
unchanged. All cells are development data, with the public depots grouped.

The core and runner passed 113 relevant focused/existing tests, without native
optimization, and a scoped independent review. Review fixed an incomplete-
evidence admission path before execution. The prospective resource envelope
remains one serial CPU, 8 GB and two hours, with no automatic retries. Source
publication and full CI precede a single frozen launch; no new result is claimed.
See doc/FEASIBLE_POOL_PILOT_PROTOCOL_20260928.md and its review.

Published execution commit 77dee963eb30ba85bca68b3efcf61d099fa33076 passed full
CI 36385045833, including the complete CBC suite and reconstruction of historical
evidence. The new pilot was submitted exactly once as job 572392 at 06:14:34 UTC,
PENDING (Priority) at its initial observation. The dedicated checkout is
/home/nc437/egg-feasible-pool-pilot-20260928. The remote exclusive intent and
submission receipt prevent an accidental second submission; the public receipt
is research-20260928/cluster/feasible-pool-pilot-572392.json. Frozen input will be
created by the wrapper at job start. No result has been inspected.

The original Google Doc now contains one “Matched computational pilot launched”
append with a functional link to the frozen prospective protocol. Luna and root
verified exact preservation of the fresh 102,111-byte Markdown baseline and one
new heading. Final Markdown is 104,024 bytes, SHA-256
2cf19c451c2edef6677f8e3090000ec05093b54a9990905f801af0c449291625. Full before/after
Markdown and PDF exports remain private; the compact receipt is under
research-20260928/agent-notes/google-doc-feasible-pilot/. PR56 remains draft and
unmerged, with its description updated for this launch.

## Matched pilot results and a stronger reuse baseline

Job 572392 completed 0:0 in 36:49. Slurm allocated two CPUs despite the one-CPU
request; native and numerical-library threads were configured to one. All
191 sealed entries and the original seal were preserved. All 24 calculations
returned on time with complete evidence: seven native-certified and seventeen
budget stops. The public reserve-cold cases processed a second fleet plan and
improved upper bounds by about 18–69 cost units. Full two-market time was about
350 seconds rather than 369 seconds for legacy cold. These final-bound/time
comparisons do not measure time to a common quality target.

Reuse closed the shifted three-service example, but public results were mixed.
It improved upper costs while weakening fresh lower bounds, narrowing depot15's
interval and widening depot16's. Both reused public runs reached the rational
polishing bit limit. Their paid time was slightly above reserved-time cold.
No public optimality closure, general acceleration or learning benefit follows.

Root identified and Luna independently verified an additional algebraic bound.
The same physical pricing problem at p=.20 supplies a reusable lower bound on
operating cost plus posted-price energy cost. Recomputing the NEW market's
Fenchel conjugate (about 2.70) gives target lower bounds 405.8331 and 420.4551.
Using this run's existing mixtures, the posthoc widths are about 64.05 and
70.21 instead of 154.12 and 161.44. This calculation uses saved evidence only,
changes no recorded outcome/time and remains numerically tolerance-qualified.
The next baseline should explicitly cache physical pricing bounds, with same-
model provenance checks and fresh target pricing, before attributing gains to
learned proposals. The numerical-QP helper is a separate remedy for arithmetic
stops. No new optimization was launched during this analysis.

Tables, two reviewed figures, compact pricing traces, a curated original-evidence
ZIP and the separate bound note are under
research-20260928/feasible-pool-pilot/results-attempt1/. The full raw archive stays
private. The new read-only reporter passed six focused tests; the independent
review replayed all saved physical columns, mixtures and target Fenchel bounds.

Analysis commit b2b160046cd56dfcab87986b961011b0041d8345 was backed up to GitHub
and passed full CI 36391559312, including the complete CBC test suite and frozen
evidence reconstruction. Draft PR56 now reflects the completed pilot and its
limits. The original Google Doc received one “Matched pilot results and next
baseline — 28 September 2026” append and showed Saved to Drive; Luna observed
the full body/link and last outline heading. Both post-edit exports were blocked
by Chrome (ERR_BLOCKED_BY_CLIENT), so exact prefix/full-export preservation
verification remains incomplete. The public receipt explicitly records this;
root verified the available before-export and append-source hashes. Do not
duplicate the append. No new cluster submission accompanied this milestone.

## Checked physical pricing-bound cache — implementation

Added a separate opt-in cache to the native hull coordinator and compact-pricing
wrapper. It preserves the source's original posted-price physical lower bounds,
checks their numerical and physical provenance, and recomputes every target
Fenchel conjugate. Bound reuse is independent of feasible-plan reuse; default
behavior and historical pilot outcomes remain unchanged. A fresh successful
target pricing call is still required before certification, and contradictory
final enclosures fail closed even on early work-limit exits.

Validation and re-evaluation count inside the target deadline. Source coordinator
and native pricing costs remain visible; child/preparation costs are unknown in
the core and must be measured by the later runner. A record digest is an integrity
check, not proof of a native solver bound; runner file/code/receipt pins remain
required. The 26 focused new-cache and feasible-reuse tests passed, and Luna's
review found no remaining admission/mathematical blocker. Root checked the review's
three final source hashes. Full CI is pending backup. No cluster submission or
new optimizer benchmark was made; numerical restricted-master integration is next.

Implementation commit 8a54521b92c518aa999c6f18a915eca2ffdc8e21 passed full CI
36396410119, including all CBC tests and frozen-evidence reconstruction. The
original Google Doc now contains one saved “Pricing-bound reuse implemented —
28 September 2026” update; Luna observed its final heading, full body and link.
Root verified the exact append-source hash. Full-export/prefix verification
remains unavailable after the earlier browser export block; no export route
was retried. The receipt records that limit. This completes the implementation
package without a new cluster job or a performance claim.

## Numerical restricted-master proposal — integration

Added an opt-in master policy using the existing SLSQP proposal helper with
fixed-denominator rounding. Its rational simplex and physical columns/mixture
are replayed, and the exact restricted-pool residual is retained. It bypasses
the native LP and repeated rational pairwise polish for that call; all default
and frozen methods remain unchanged. The full-space bound and replayed upper
still determine certification after fresh pricing, regardless of SciPy's
termination flag. Valid non-success proposals can be useful candidates.

Proposal failures retain previously verified evidence as `proposal_failed`;
physical replay failures remain hard validation errors. Time/bit limits are
budget stops and cannot silently trigger fallback. Component times, setup,
replay and maximum rational bits are accounted. Whole-child deadlines remain
necessary because an in-process SciPy call cannot be forcibly preempted. Final
focused checks, independent review and CI are pending. No cluster experiment
was launched. The next package is a new frozen ordered comparison on the four
existing development cases, with two markets and four policy arms.

The final 37 focused numerical-master/cache/reuse tests passed. Independent
review passed after checking typed import failures and hard physical replay
errors; root verified all four reviewed file hashes, including the unchanged
proposal helper. Full CI is pending this implementation backup. No solver
benchmark or cluster action accompanied the tests.

Implementation dc5e01480996ae97adb08821e9fb518cba43492b was backed up and passed
full CI 36402944039, including the complete CBC test suite and frozen-evidence
reconstruction. The original Google Doc received one saved numerical-master
implementation update; Luna observed its final heading, full body and review
link, and root verified the append-source bytes/hash. Full-export preservation
verification remains unavailable after the earlier browser block. The compact
receipt records that limit; no export retry or cluster job accompanied this
completed implementation package. Next is the prospective 32-cell ordered
comparison, with source/caps/accounting frozen before launch.
