# Native recharge qualification: prospective protocol

27 September 2026. Protocol `native-recharge-qualification-20260927-v1`.
This is an isolated synthetic qualification of a new research feasible set.
No production behavior, historical result, protected campaign, or private source
is modified. The source, tests, runner, and this protocol must be committed by
the principal researcher before the first scientific optimizer execution.
Pure replay, fake-oracle tests, and analytical fixture construction may precede
that freeze. At protocol preparation, **no native qualification has run**.

## Scope and interfaces

`egglab.native_recharge.NativeCase` contains mandatory service trips, directed
movement modes, homogeneous battery/reserve/constant efficiency, resource
periods, market periods, the depot, fleet cap and intrinsic costs. Every movement
has explicit timestamped directed legs with nonnegative known energy. The model
never manufactures a missing/reverse movement or treats an unknown energy as
zero. A mode is a pull-out, direct inter-trip movement, a depot inter-trip movement
with an explicit inbound/outbound split, or a pull-in. Multiple travel legs are
preserved. All possible visits and travel times are fixed input alternatives;
the solver chooses among the declared alternatives. The source adapter, its
provenance, and justification of alternatives remain outside this module.

Every used bus covers at least one real service, starts at full battery, and must
finish full after charging. A pull-in creates a native recharge visit from the
later of actual return and `terminal_open_min` to the common deadline. No service
marker or empty vehicle represents terminal recharge. The visit owner is the
selected pull-in movement; inter-trip visits belong to the selected depot mode.
Movement cost is explicitly proportional to the sum of leg travel durations,
not waiting time. Battery consumption is monotone within each service/travel leg;
regeneration, tapering, self-discharge, multidepot travel and variable trip energy
are outside V1.

`build_feasible_model` is the sole fleet feasible-set builder. `solve_pricing`
attaches intrinsic cost plus grid-energy expenditure at an arbitrary finite
price vector. `solve_planner` uses the same builder and a separable convex supply
cost `sum(a[t]*L[t] + b[t]*L[t]^2/2)`, with `b >= 0`, in a tangent outer
approximation. Pricing is over a complete feasible fleet, including shared
charging resources. No column generation, learned prices, historical cache or
convex-hull solver is included in this gate. The controls with known hull prices
test the linear oracle at those prices; they do not themselves compute a hull.

## Exact interval semantics and physical witness

Event intervals split at every candidate recharge arrival/departure, resource
boundary, market boundary and terminal-opening time. Available vehicles and
charging limits are constant throughout each interval. V1 supports zero or one
finite homogeneous connector; an input with more connectors is rejected.
For interval duration `delta` hours, charge energy is nonnegative, bounded by
mode selection, and the fleet sum is at most
`min(per_bus_kw, grid_kw)*delta` if one connector is available. A vehicle selects
at most one available visit in an interval. These are exact preemptive,
zero-switching-time semantics for this single-connector model: any admitted
energies can be scheduled consecutively at that common rate within the interval.
The decoder actually emits those consecutive sessions, with owner, connector,
start/end time and grid energy. It never treats average hourly energy as proof
of simultaneous resource feasibility.

Battery gain is `efficiency * grid_kwh`; load, price expenditure and supply cost
all use grid kWh. SOC conservation and reserve/capacity hold before/after every
service and depot visit. Between such events energy is monotone, so the endpoint
constraints suffice. The independent `replay_native` walks selected directed
paths, checks exact coverage, derives visit windows from ownership again, checks
travel/service overlap, sweeps actual sessions against resource changes, and
rebuilds period loads and intrinsic cost. It independently reconstructs SOC and
full replenishment. Sweep membership uses strictly positive interval overlap,
not a floating midpoint that can round to an adjacent endpoint. Charge completion
precedes a simultaneous instantaneous
outbound leg; an incoming leg cannot end at the end of a positive-duration
owned session because the arrival is its earliest start.

Floating solver/witness checks use `1e-6` kWh and `1e-7` minute tolerances. This is
a solver-conditional numerical certificate, not rational verification. No small
positive charge is silently discarded. Each finite session is represented,
including partial market/resource windows. Failed physical decoding/replay is a
failed cell, with its native status already preserved.

## Frozen synthetic controls and analytical expectations

All fixtures and their complete inputs live in the runner. Monetary quantities
are synthetic objective units. The table fixes targets before scientific runs.

| Control | Objective | Prospective result |
|---|---|---:|
| `single_linear` | Grid price 1, one 15-kWh service, full recharge | 22 |
| `efficiency_linear` | Same service, efficiency 19/20 | 433/19 |
| `cyclic_flat` | Complete nominal cyclic fleet, all prices 1 | 37 |
| `cyclic_own_price` | Prices [0,6,0,4] | 134 |
| `cyclic_hull_price` | Prices [0,5.35,0,4.65] | 153.5 |
| `cyclic_planner` | Nominal physical supply-cost planner | 97 |
| `preserved_reserve_planner` | Capacity 21, reserve 1 | 97 |
| `joint_flat` | Capacity 20, reserve 1, efficiency 19/20, early 12 kW | 733/19 |
| `joint_planner` | Same joint physics, physical supply-cost planner | 38527/361 |
| `fixed_reserve_planner` | Capacity 20, reserve 1, early 10 kW | 99 |
| `fixed_reserve_one_bus` | Same fixed reserve but fleet cap 1 | Infeasible |
| `terminal_capacity_failure` | 15-kWh demand, only 10-kWh native capacity | Infeasible |
| `partial_overlap_failure` | Two 5-kWh returns at minute 30, deadline 60, one 10-kW connector | Infeasible |
| `serial_connector` | Same returns, deadline 90 | 24 |
| `directed_multileg` | Explicit multileg pull-out/return, 14-kWh total, travel cost 15 | 36 |

The nominal cyclic case has two 15-kWh trips at minutes 0–60 and 120–180,
battery 20, reserve 0, vehicle cost 7, resource windows 60–120 at 10 kW and
180–240 at 30 kW. Both use one connector. The early/late supply functions are
`4*x + x*x/10` and `y*y/10`. One bus must use grid load (10,20), with cost 97.
Two buses permit the entire family `(x,30-x), 0 <= x <= 10`; its physical minimum
is at `x=5`, cost 99. Crucially, native `terminal_open_min=0`: an A-only bus may
buy early energy after its final service. Native ownership and fixed resource
windows are distinct. Setting terminal opening to 180 would remove valid members
of this two-bus family and change its minimum to 104.

Capacity 21/reserve 1 preserves usable capacity and nominal loads. Holding
capacity 20 and introducing reserve 1 removes the one-bus solution under early
10-kW charging, so the complete two-bus minimum is 99. Under joint reserve 1,
efficiency 19/20 and early 12 kW, the one-bus SOC path is
`20 -> 5 -> 16 -> 1 -> 20`; its early/late grid energies are `220/19` and 20.
Its physical objective is `38527/361`, the proposed control value. These are
analytical expected values, not solver observations; disagreement must be
reported and investigated, never repaired by redefining a target after the run.

The overlap failure has only 5 kWh of *available* capacity between return and
deadline despite 10 kWh of full-hour grid capacity. The serial positive variant
admits two consecutive half-hour sessions. The multileg control counts both
inbound and outbound legs and separately accounts for driving cost and energy.

## Native solve and evidence policy

CBC is the first local backend; a later explicit GRB replication uses the exact
same frozen runner and targets after local qualification. Backend selection is
explicit. The model's solver name and loaded implementation module must match
the request; a mismatch or fallback fails. Receipts record Python, Python-MIP,
requested/actual backend, solver class, available native-library path/hash,
model dimensions and the constraint count before objective attachment. A missing
resolvable library hash is recorded as missing, never guessed. No credentials
or environment-variable inventory is written.

Each cell runs in a fresh process, one solver thread, at most 10 seconds per native
solve, 45 seconds for its solve routine and a 60-second external process timeout.
The planner allows at most 48 tangent rounds. There is no separate unbounded
LP-first solve. The whole 15-cell campaign is sequential and bounded by 15
minutes of external per-cell caps plus small controller overhead. This is a
qualification budget, not a performance benchmark or claim of 30-trip scalability.

A pricing result needs a physically replayed incumbent and a finite native global
lower bound. Either native `OPTIMAL` or `FEASIBLE` may supply them; the raw status
is always preserved. Each bound is widened outward by `1e-6`; certification
requires resulting absolute width at most `1e-4`. Thus a time-limited `FEASIBLE`
result may certify only when its actual enclosure is sufficiently narrow. A
wide gap remains `bounded`; a missing/reversed bound or corrupted witness fails.
For linear pricing, the finite native incumbent must agree with the independently
replayed linear objective within `1e-6` objective units, and the global lower
bound cannot exceed either. A native status alone cannot override inconsistency.
Native `INFEASIBLE` is reported as solver-conditional infeasibility. Other statuses
remain unresolved. This prospective admission policy does not reclassify any
historical run or prior protocol failure.

Planner lower bounds come from the native global bound of the tangent
underestimator; upper bounds are true costs of independently replayed physical
plans. Tangents are exact for the supplied quadratic. Each round saves an
immutable snapshot of its solved tangent set. The best lower/upper bounds across
rounds form the enclosure. A target cell passes only if its expected status is
met, its enclosure/value agrees with the analytical target within `2e-4`, and
its witness replays. This analytical agreement tolerance is distinct from and
does not replace the `1e-4` numerical certificate width.
The independently evaluated *saved current* PWL envelope at the extracted load
must be at least the native lower bound and at most the true cost, allowing the
stated numerical guard. The finite native incumbent must be at least that
envelope and at least its global bound. A legitimate time-limited epigraph
incumbent may contain nonnegative slack above the minimal envelope; that slack
is recorded rather than incorrectly requiring equality to the envelope.

## Attempt preservation, execution and next gate

The controller creates a new directory exclusively; it never resumes/overwrites
an attempt. Before any child solve it writes all case inputs, targets, budgets,
source SHA256 values and the declared committed freeze label. Each worker checks
those source hashes again. For every declared control it saves input and launch
receipts, stdout/stderr, native-call start/status events, round witnesses,
result/assessment or exception traceback, and a controller receipt. Native status
is flushed before decoding/replay so a witness failure cannot erase the solve.
A hard timeout preserves whatever events were flushed. A truncated event or
result file remains unmodified: the controller records parse issues, retains
the valid event prefix, marks accounting incomplete and the cell failed, and
continues the campaign. All subsequent controls
are attempted even after a failed cell. Summary counts distinguish calls started,
calls returned, native solve time and total process time. Failed cells are kept
in reporting; there is no retry, cap extension or solver switch inside an attempt.

After the principal researcher commits all four files, the intended local command
from the research worktree is:

```sh
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m experiments.native_recharge_qualification --output result/native_recharge/20260927-attempt1 --freeze-label COMMIT_ID --backend CBC
```

`COMMIT_ID` must be replaced by the actual source commit. The runner is not an
approval system; the principal researcher verifies source freeze before dispatch.
Any source correction requires a new commit, new prospectively declared attempt,
and disclosure of the original failure. Qualification success supports a later
independent model/witness audit and explicit cross-backend replication. It does
not authorize publication of private inputs, prove unrestricted source-graph
coverage, or establish operational/economic generality. Private microcases must
declare their prevalidated known/historical-arcs graph and retain source evidence
outside public output. No 30-trip operational optimization is part of this first
synthetic gate.
