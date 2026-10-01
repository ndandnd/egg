# Feasible-pool reuse and reserved-master pilot

**Prospective development protocol — 28 September 2026.** This design requires
independent source/harness review and a new frozen attempt before any run. It
does not alter or reinterpret the completed 32-stage screen. All four physical
cases and both Hildenbrand depot variants remain DEVELOPMENT data; the two
public variants belong to one timetable group.

## Design and comparisons

Run hull stages only: the cyclic two-service case, multivisit three-service
case, and Hildenbrand depot15/depot16, each at the same two frozen markets as
the first screen. The 24 declared cells are four cases × two markets × three
arms. No planner, own-price response, learned method, or new physical
qualification is part of this pilot.

| Arm | State 0 | State 1 | Main matched comparison |
| --- | --- | --- | --- |
| `legacy_cold_hull` | Empty pool; existing hull policy | Empty pool; existing hull policy | Baseline for reserve policy |
| `reserve_cold_hull` | Empty pool; 10-second reserve guard | Empty pool; same guard | `legacy_cold_hull` isolates the reserve policy |
| `reserve_feasible_hull` | Empty pool; same guard | Import only its own eligible state-0 feasible fleet-plan pool | `reserve_cold_hull` state 1 isolates reuse |

Every arm pays its own state-0 run. Compare `legacy_cold_hull` with
`reserve_cold_hull` by matched case and market for the reserve effect. Compare
`reserve_feasible_hull` with `reserve_cold_hull` at state 1 for the reuse effect,
while reporting state-0 preparation and both-state totals for each arm. Never count state 0 as free;
never replace an ineligible or failed reuse state with a cold result. Report
outcomes, final lower/upper bounds, calls and time together. Claim a time
advantage only at a common quality target; otherwise present descriptive final
enclosures and time without a speedup claim.
Compute a two-state total only when both state timings are recorded; if state 1
is ineligible or missing, mark the total unavailable rather than reporting the
state-0 preparation as a complete two-state cost.

The original strict certified-predecessor path remains unchanged. The new
`reserve_feasible_hull` arm uses `reuse_policy='feasible_pool'` and is separate;
do not relabel historical `retained_hull` cells or include the previous 32
cells as pilot observations.
Current hull columns are complete feasible fleet plans, not independent bus
routes or duties.

## Reserve and reuse rules

The reserve is 10 seconds **inside** the existing native stage wall target,
not additional time. Preserve the core loop order: after a pricing result, the
ordinary master step may process any new column. Before starting the *next*
pricing request, stop with `budget_exhausted` if total wall remaining is at most
10 seconds or the pricing-call cap is reached. Otherwise cap that request's
native `wall_seconds` allowance at the smaller of its existing allowance and
remaining total wall minus 10 seconds. Leave `phase_seconds` unchanged; a
non-preemptible solver step may overshoot the wall allowance and consume the
reserve. Do not append a duplicate final master outside the normal loop. The
hard child deadline remains native target plus 30 seconds.

For the two reserve arms, the frozen event/result trace must record each pricing
request's wall allowance, remaining wall and reserve, plus a distinct
reserve-prevented stop reason/event; keep existing request/master/polish counters
and stop-reason fields. Record actual elapsed time and overshoot. The
`legacy_cold_hull` arm keeps its existing event schema. If reserve-arm telemetry
cannot distinguish a reserve stop from a call cap or other termination, report
reserve engagement as unknown. Matched final bounds remain descriptive, but do
not attribute an observed difference to reserve engagement. Preserve partial
results and classify stage failures honestly.

For state-1 reuse, admit only the same arm's state-0 result with an on-time
successful receipt and complete assessment: native status `certified`,
`bounded`, `stalled_bounded`, or `budget_exhausted`, finite recorded bounds, and
complete replay evidence.
Independently validate the predecessor's physical/source/extraction identity,
unique column keys, and **every** imported complete fleet plan under the same
physical case. If any required check fails, mark reuse state 1 ineligible; do not
filter a bad column silently or substitute another arm's pool.

Import only those replayed feasible fleet-plan columns. Rebuild the target
market restricted master and compute fresh target-market pricing/global lower
bounds. Do not transfer predecessor mixture weights, duals, prices, or lower
certificates, and do not treat predecessor status as target-market evidence.
Keep predecessor source and state identity as provenance for the imported pool.
If a target-market certificate does not close, retain its literal `bounded`,
`stalled_bounded`, or `budget_exhausted` status and finite enclosure without
calling it optimal.

## Fixed computational envelope and records

Keep the physical model, objective, backend, native thread count, per-cell stage
targets, and hull call/work caps from
[`COMPUTATIONAL_SCREEN_PROTOCOL_20260928.md`](COMPUTATIONAL_SCREEN_PROTOCOL_20260928.md):

| Cases | Cells | Native target per hull stage | Sum of native targets |
| --- | ---: | ---: | ---: |
| Two synthetic cases | 12 | 60 s | 720 s |
| Two Hildenbrand depot variants | 12 | 180 s | 2,160 s |
| **Total** | **24** | — | **2,880 s** |

Retain at most 4 pricing calls and 6 master calls, 16
columns, 64 exact-polish steps, 4,096 rational bits, the 20-second aggregate
soft-polish target, epsilon `1e-4`, and pool tolerance `1e-6`. The reserve does
not raise any cap. The existing per-stage hard deadline adds at most 30 seconds
per declared cell, for at most 3,600 seconds of child deadlines before other
controller work. Keep the existing 5,400-second controller budget, 5,500-second
outer supervisor cap, and two-hour Slurm allocation. Request one CPU/8 GB, run
serially with one native thread, no requeue or retry, and exclude
`scaglione-compute-01`; leave other-project jobs untouched. Freeze once before
optimization and record actual allocated resources and full Slurm elapsed time.

Seal one row for every declared cell, including ineligible, failed, late,
timed-out and unstarted cells. Preserve receipts, raw results/events, imported
column provenance, reserve/termination details, fresh target certificates,
solver-call times and stage wall times. Missing component timing stays missing;
never infer routing time by subtracting recorded solver calls from wall time.
Keep both public depot variants grouped as one timetable and label every result
development-only. This hull-only pilot does not establish a physical-planner
gap, own-price regret, operational benefit, generalization, or learning effect.
