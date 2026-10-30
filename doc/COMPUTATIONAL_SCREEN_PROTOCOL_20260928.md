# First computational development screen — prospective protocol

28 September 2026 UTC. This is a bounded diagnostic experiment under the user's
request for computational examples and possible learned route proposals. It is
not a replacement for either historical nonlinear attempt, an ML test set or a
claim of scalability. Freeze the complete case/market/budget/source manifest
before optimization, using a published execution commit and a new attempt path.

## Cases, markets and comparisons

Use the existing cyclic two-service and multivisit three-service builders, and
both full 37-service Hildenbrand single-depot variants from the pinned public
payload. The two public variants share the same base-timetable group. All four
cases and both market states are DEVELOPMENT. No random sampling is involved.

Each market has separable cost `F(L) = sum(a[t]*L[t] + b[t]*L[t]^2/2)`.
The machine manifest records the full vectors and their actual binary floating
point values; the following decimals specify their construction.

| Physical case | Initial intercept a | Second intercept a | Curvature b, both states |
| --- | --- | --- | --- |
| Two-service cyclic, 4 periods | (0, 4, 0, 0) | (0, 3.8, 0, 0.2) | (0, 0.2, 0, 0.2) |
| Three-service multivisit, 4 periods | (0.2, 0.2, 0.2, 0.2) | (0.18, 0.18, 0.22, 0.22) | 0.2 in each period |
| Hildenbrand depot 15, 30 periods | 0.2 in each period | 0.18 for first 15, 0.22 for last 15 | 1/900 in each period |
| Hildenbrand depot 16, 30 periods | same as depot 15 | same as depot 15 | same as depot 15 |

For each case and state compute a common physical planner result, cold hull,
retained hull, and price-taking response at the planner incumbent's own marginal
price. A missing valid planner witness makes its response ineligible; it does
not prevent the hull stages from running. There are eight case–market groups and
up to 32 stage runs. Keep every declared stage in the final table, including
ineligible, failed, timed-out and bounded outcomes.

The current hull columns are **complete feasible fleet plans**. They are not
independent bus duties or a service-cover route master. Retention is between
market states of the same exact physical case. Each arm pays for its own initial
state from an empty pool. The second retained state can import only its certified
retained predecessor with matching case, source and state identity, using the
existing native import checks; otherwise report it ineligible. Do not replace a
failed retained chain with a cold success. Report state-transition time and the
sum over both states, so first-state preparation is visible.

## Budgets and execution

One serial Slurm job; request 1 CPU and 8 GB, one native thread, at most 2 hours,
no requeue or automatic retry, exclude `scaglione-compute-01`. Leave other-project
jobs and held jobs untouched. Record actual allocation if it exceeds the request.
Use the existing GRB backend and unchanged physical/hull core; the experiment
adds a supervisor and trace exports, not a new mathematical formulation.

| Stage | Synthetic native wall target | Public native wall target |
| --- | ---: | ---: |
| Planner | 60 s | 180 s |
| Cold hull | 60 s | 180 s |
| Retained hull | 60 s | 180 s |
| Own-price response | 30 s | 60 s |

Each stage runs in a separate process with a hard deadline equal to its native
wall target plus 30 seconds. This includes initialization, solving and export.
The controller has a 5,400-second execution budget. An outer 5,500-second hard
supervisor cap covers the supervisor invocation: its source/design precheck,
controller execution, cleanup and sealing. Job environment setup and the one-time
freeze precede this invocation and are covered by the separate two-hour Slurm
allocation. Record supervisor elapsed time and Slurm's complete job elapsed time
so that setup is not free work; the 5,400-second controller allowance is not a
full-supervisor or whole-job timing claim.
Native targets are stopping rules, not promises that a non-preemptible native or
exact-arithmetic step ends at that instant. Record every actual elapsed time and
overshoot. A result finishing after its hard deadline is not an on-time success.
Preserve partial raw events/results and termination receipts after a timeout.
Do not repeatedly launch a cell until it succeeds.

After an interrupted controller, account for every declared stage as completed,
failed, aborted, ineligible or unstarted as supported by its receipts. Before
sealing, confirm that terminated workers cannot continue writing. If cleanup
cannot be confirmed, report that failure and do not claim a stable sealed result.

Planner: at most 6 synthetic or 8 public rounds, per-call target at most 45 or
160 seconds respectively and always capped by remaining native wall allowance.
Response: at most one pricing solve, target at most 30 or 60 seconds respectively.
Hull: at most 4 pricing calls, 6 master calls, 16 columns, 64 exact polishing
steps, 4,096 rational bits; aggregate polishing target 20 seconds, global
epsilon 1e-4 and restricted-pool tolerance 1e-6. All runtime budgets are recorded
in the freeze. Reaching a polishing work limit can return useful valid bounds;
it does not create a certificate when the pool or global residual stays open.
The old 5-second strict-cap failure remains unchanged.

## Evidence and decisions

Save complete case and market features, selected service connections/routes,
physical fleet witnesses, charging/SOC/load data, hourly prices, hull columns,
all native calls and iterative states, valid lower/upper bounds, status and
end-to-end time. Keep source identity with every label intended for later ML.
An incumbent from a time-limited solve is a feasible candidate, not an optimal
training label. Native/tolerance-qualified results must not be presented as
exact ideal-model proofs.

The first analysis asks: which stages dominate time, which stop with open bounds,
whether retention saves work on eligible matched transitions, and whether larger
cases need restricted-master improvement before route-proposal experiments.
Separate pricing time, master/polishing time and other overhead; compare both
final enclosure quality and time. Report regret only for the particular replayed
planner incumbent and valid response bounds, not for an unknown planner optimum.
Show conditional gap intervals only when both contributing bounds refer to the
same declared model and market.

No learning efficacy claim follows from this screen. Subsequent work adapts
independent public timetables and scalable synthetic families, compares retained
plans and nearest-neighbor reconstruction/repair, then evaluates learned
proposals if they address a measured source of cost. All variants of a base
timetable remain in the same train/development/test group. See the research
roadmap and learned-route review for this broader design.
