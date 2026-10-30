# Selected bounded pricing workload — source-only decision

This is a prospective development design, not a data-generation or numerical
launch. It asks whether actual classical column discovery is costly and finds
useful alternatives beyond a paid retained bank. It does not test a neural
model, nonlinear market iteration or an unrestricted EVSP certificate.

## Cohort and physical problem

Adopt SYNTHETIC_SPEC.md's exact deterministic recipe: base seeds 61001–61004,
four prescribed duties, nested 12/24-trip variants (three/six waves), 45-minute
40-kWh trips, 180-minute waves, offsets 0/10/20/30, source-defined 0/5/10-minute
common-wave jitter. Preserve the declared transfer table, two active stations,
60/120 kW, one plug, battery80/reserve10, SOC step10, event block30, horizon1560,
and aggregate grid/physical terminal requirement160. Keep source BUS100000 and
fee0. All resources and four-bus cap are unchanged between sizes. The two quotes
are flat0.20 and the existing source_shape; no price/curvature/resource scan.

The four simultaneous trips provide an outcome-independent fleet lower bound4.
With the native fleet cap<=4, a valid selected fleet has exactly4 buses; no new
equality row is asserted. For individually valid columns, each covers at most
one trip of that simultaneous clique, so partition coverage also fixes total
route weight4 in the master. The operations term is then constant, matching
the source's fleet-first integer policy without changing it. If this declared
property fails in generated inputs or column admission, stop with a contract
failure; do not relax fleet or redefine the objective.

This does not prove four-bus charging feasibility. Use a paid flat-quote oracle
acquisition, not an unimplemented hand-built charging witness or outcome-based
case eligibility filter. No successful reference is assumed. Freeze all full
descriptors before outcomes; verify prefix/overlap/domain/terminal contracts.
Compare canonical physical descriptors excluding seed labels for cross-group
aliases. Retain collisions and union their group membership, never replace
seeds. If fewer than four distinct group clusters remain, the continuation
screen is inconclusive. All variants, quotes, traces and later labels from a
group/alias cluster remain together. Four groups are development, not final
independent generalization evidence.

## Forty-eight assigned stages, separate banks

There are 4 bases × 2 sizes × 2 restrictions =16 sequences. Each sequence has
three assigned stages, giving48 total states:

1. A0: one fresh flat-quote capacity-oracle acquisition, with its own complete
   exported bank and independently admitted selected fleet.
2. F1: one fresh source_shape target-quote oracle search under the same
   restriction. It uses a freshly built target network and seeds=().
3. C1: retained-bank selection from that sequence's own A0 bank only, repriced
   under source_shape, with no new pricing.

Fixed-duty A0/F1 and full A0/F1 are independent discoveries. Never seed a fixed
arm from the full bank, or combine banks before endpoints close. A0 bank
membership is complete; no favorable subset, trip-set dedup, random downsample
or best-outcome truncation is allowed. Bank size/resource failure is retained.

A valid A0 selected fleet is independently repriced/admitted as an external
target incumbent for both F1/C1. It is not a claimed native processed start.
Missing A0 leaves C1 explicitly unattempted/missing; F1 remains eligible cold.
If A0 has a valid endpoint but its complete bank cannot be admitted, preserve
the endpoint for F1 and mark C1 unavailable. No new reference solver, alternate
seed, repair or automatic retry follows. A source/configuration/identity fault
or unresolved child stops onward dispatch; ordinary no-incumbent/resource
outcomes retain all planned states under the selected budget.

Use ascending base order; size order 12/24 for odd base ordinal and24/12 for
even ordinal. Restriction order fixed/full for odd ordinal and full/fixed for
even. Within each sequence A0 precedes both targets; F1/C1 order alternates
by parity of (base ordinal + size ordinal + restriction ordinal). Store the
complete ordered sequence before generation. No concurrency or outcome-based
reordering. Counterbalancing is not a timing significance test.

## Actual cache interface and matching semantics

Nonuniform power rejects the source runner's nonempty seed path. Preserve
60/120kW; do not pretend C1 is warm CG, change to uniform power or assign
net.prices in place. C1 uses existing original admission/realization APIs and
realized_costs(..., station_prices=q_target) to revalue fixed grid stops while
preserving power/visits/times. Keep old stored cost as old-quote telemetry; use
the recomputed grid cost/loads for the target. All cache records must be
admitted under original source physics; no invalid-column dropping or repair.

Use existing bank_master.build by reference, mode binary, representation grid,
institution posted, zero portfolio prices/curvature, target station-hour quotes
as adders, fleet_cap4, partition coverage and counted plugs. Native terminal
arguments are grid160 and realized0: the latter is an inactive nonnegativity
row for admitted columns, preserving the source oracle's grid-terminal native
scope. Independently require BOTH grid and realized selected-fleet terminal
energy>=160 at physical admission, just as for F1. Do not call the additional
physical screen a grid-LP certificate. A rejected candidate stays rejected;
there is no completion/refinement solve or alternative-selection retry.

The overlap argument fixes fleet quantity for valid columns, so the combined
BUS-plus-grid-electricity objective has the same cost ordering as the source's
fleet-first/then-electricity policy here. C1 gets one binary solve, the same
external common fallback, original joint physical admission and no price oracle.
Native OPTIMAL and physical admission are separate. No new continuous refiner
or copied sibling solver is needed.

## Inclusive clocks and proposed envelope

Select a future NEW7200 CPU /10800 wall-second maximum, dispatch6600/closure600,
one serial native thread and observed worker RSS<=5GiB; parent separately
measured. This is a proposed resource decision, not a frozen launch. Preflight
and deterministic construction120CPU/180wall and final publication120CPU/180wall
are INSIDE totals. Forty-eight possible workers have hard120CPU/180wall each;
48×120=5760 plus preflight and closure fits7200. Owned cleanup3 seconds and
unresolved-child120CPU reserves remain inside total; stop dispatch if funding
for a whole next stage plus closure is absent. Adopt source preparation once.

Each stage clock starts before Popen and covers cold imports, generation or
load, graph construction, all search, bank IO/admission, replay and publication.
F1/A0 use existing runner options: batch_size30, max_iters100000, rc_eps1e-6,
viol_tol1e-6, smoothing0, no dive/partial/directional/integer-pricing, partition
true, seeds=(). Nominal CG50s/MIP50s are clipped to remaining paid native budget
ending at parent+150; complete endpoint/packet by180. The source's CG deadline
can trigger a later LP resolve, so these internal allowances are NOT hard total
limits; unchanged outer CPU/wall ownership remains decisive. Record truncated
work and missing timing rather than calling it solved. No patched controller.

C1 also has the same120CPU/180wall external allocation, one binary call with
at most100 native seconds clipped to parent+150 after paid revaluation/build.
No mandatory relaxation call is added to manufacture work. Report actual spend
and remaining resources, not assumed equal consumption. Source/native settings
and exact residual-time formulas still need review with the thin implementation
before freezing any executable manifest.

Report A0 acquisition separately and the uninterrupted A0→target latency.
For the second target, that uninterrupted elapsed time includes the intervening
competing branch and is scheduling telemetry, not its standalone pipeline cost.
For the two branches report total A0+F1 and A0+C1, including acquisition once in
each counterfactual pipeline total, while charging it ONCE in the physical
campaign account. These are a fixed one-use target horizon, not free-cache or
post-hoc amortization claims. No speedup from raw solver time or summed overlapping
child meters. A later neural comparison must pay the same full pipeline costs.

## Outcomes, telemetry and predeclared investment screens

Use existing stage clocks, oracle summary, iterations and complete columns.
Pricing-event wall includes reconstruction/nearby work; it is not pure DP CPU.
Incomplete event histories do not establish exact call counts, full dual vectors
or per-column reduced-cost labels. Do not invent them. Initial diagnostic uses
these existing whole-run outputs only; any later query-label instrumentation
needs its own proposal. Keep artificial mass, LP/pricing stop scope, native
statuses, bounds, completed history coverage and physical admission distinct.

Report raw and unique physical witness counts separately. Canonical identity
must include ordered service, station visits, charging stops/energy, not just
trip sets; include original IDs/provenance and charge the calculation. Report
all grid and continuous costs/loads/terminal inventories separately. Lower
energy with a different terminal inventory is not automatically efficiency.
Observed economic gain from F1 over an optimal own-bank C1 supports valuable
discovery in this finite bank comparison; it is not global regret or neural
information value. Missing individual reduced-cost provenance stays UNKNOWN.

All16 A0,16 F1,16 C1 planned states remain explicit. The investment screen is
eligible only with complete accounting/source admission, four distinct group
clusters, all16 valid acquisitions, all16 strict F1 deliveries and all16 timely
physically valid native-OPTIMAL C1 controls. Strict F1 means the actual target
oracle returned a timely new native candidate that passes physical admission;
it may equal an earlier plan and need not be a novel topology. Merely retaining
A0 after failed/no-result/late target work is operational fallback only and
cannot satisfy this condition. If a valid new candidate is worse than A0, retain
the better admitted endpoint while reporting candidate and retained values
separately. F1 native gaps/certificates remain separate from timely delivery.
Any failed/missing/late required method makes readiness
inconclusive, with operational results still reported and no available-only
rescue. A negative complete screen is a scoped stop, not zero-effect proof.

Freeze two DIFFERENT decision scopes; do not choose a model family after results:

- Primary full-route discovery: on its8 F1 cells, cumulative pricing-event wall
  must have group medians>=5s AND median share>=25% of complete paid F1 elapsed
  in at least3/4 groups. For value, compare F1 against BOTH its own C1 and the
  independent fixed-duty F1 endpoint at matching base/size. For each contrast,
  require positive complete group medians in>=3/4 groups and the full8 mean of
  paired ratios >.01. Explicitly, d[g,n,control] =
  (cost(control[g,n])-cost(full_F1[g,n])) / E(full_A0[g,n],target), with the
  positive denominator the common full A0 fleet's target GRID-electricity cost.
  Compute sum(d)/8 separately for each control, never a ratio of means. Each
  group's median uses its two sizes, not independent edge samples.
- Secondary fixed-duty column discovery: apply the same effort thresholds to
  its8 F1 cells, and the same value rule against its own C1, using its own A0
  target grid-electricity denominator: d_fixed[g,n] =
  (cost(fixed_C1[g,n])-cost(fixed_F1[g,n])) / E(fixed_A0[g,n],target), and
  sum(d_fixed)/8 >.01, never a ratio of means. This concerns charging/visit-column
  discovery within committed service sequences; it cannot rescue or promote
  the primary duty-reassignment hypothesis.

These thresholds are prospective practical investment rules, not calibrated
money, significance tests or publication claims. All comparisons and stratum
results are reported regardless of the screen. Pairwise controls receive the
same stage budget; do not invent a free best-of-control portfolio or pool the
two scopes. If effort/value is absent, stop that scope without increasing
scarcity, curvature, fleet, size or quote variants after outcomes. A pass only
justifies a separately scoped query/provenance/valuable-alternative target audit;
it does NOT authorize fitting, architecture searches or a broader benchmark.

## What must exist before execution

A minimal EGG-local synthetic constructor and thin caller using these existing
APIs; exact literal cohort/order/fields/version/import/parameter manifests;
consistent grid quote repricing and independent physical admission; source and
resource/command freeze; and one focused implementation review. No new monitoring
framework, repeated old engineering matrix or private-data import. No actual
case, bank, raw row, price trace, model or solver input was created/read by this
design package. The registered sibling stays read-only. Current studies remain
development; all previous failures, accounting, no-go decisions and closed
namespaces are preserved.
