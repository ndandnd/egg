# Prospective synthetic frontier for retained charging columns — 27 September 2026

This source, protocol and fake-oracle tests must be committed before the first
scientific solve. The driver refuses to start when any tracked dependency it
records differs from HEAD, or when its source/protocol/tests are untracked.
No pilot solve, result-selected tariff, protected data, confirmation seed,
learning run or cluster submission belongs to this experiment. Failed cells
remain part of the report. This is a bounded discovery-work diagnostic, not
an operational benchmark or population-level performance comparison.

## Question and fixed instances

Does the useful work beyond retained columns survive when physical schedules
have competing fleet structures and more than two charging opportunities?
Can a single shifted-price proposal reduce the *total* work including its own
pricing solve, under the same final clean certificate? A null or adverse
proposal result is informative and must not be redesigned away.

All fixtures are hand-authored, seed-free, depot-to-depot, and have three real
services at [0,60], [180,240] and [360,420] minutes. Each consumes 15 kWh.
Initial energy and battery capacity are 20 kWh; the minimum SOC is zero,
charging power is 10 kW, slots last one hour, and at most two buses are allowed.
There are no deadheads, shared-power constraints, plug-count constraints or
partial-slot windows. Charging decisions are continuous. A one-bus schedule
has four hourly charging opportunities: slots 1, 2, 4 and 5. Two-bus structures
can also charge while the other bus serves the middle trip. Every allowed
partition and direct/depot arc choice is available to pricing.

| Fixture | Fixed cost per bus | Terminal floor | Horizon | Meaning |
|---|---:|---:|---:|---|
| depleted_f20 | 20 | 0 kWh | 7 h | One/two-bus competition, depletion permitted |
| depleted_f26 | 26 | 0 kWh | 7 h | Same physics, higher fleet cost sensitivity |
| replenished_two_bus | 10 | 20 kWh | 11 h | Fixed two-bus fully replenished control |

The replenished fixture adds **two simultaneous zero-energy terminal markers**
at [600,660]. They are explicit modeled events, not service demand. Their
simultaneity, complete coverage and the two-bus limit force exactly two chains;
each chain ends at one marker. Every used bus therefore has a final recharge
window and finishes full. A bus may serve only its terminal marker. This is
a fixed two-bus inventory control, not a claim about optimal fleet size or a
production overnight-charging feature. Its charging must sum to exactly
45 kWh in every physical column and convex combination. Depleted cases allow
the extra bus to provide extra initial stored energy; that is a stated policy
assumption, not evidence of a cyclic-fleet gap. No positive cyclic gap is
hypothesized by this experiment.

## Fixed tariff path

For every fixture use five states: base, unchanged, early-cheap, late-cheap,
return-to-base. In all slots, b=0.2 and external load U=0. The intercept is
`a_t=0.3+d*v_t`, where `d=[0,0,0.25,-0.25,0]`, and `v_t=-1` for slots 1–3,
`v_t=+1` for slots >=4, and zero for slot 0. The entire feasible set, intrinsic
cost, supply slope and external load remain fixed across a trajectory.
All marginal energy prices remain positive. The identity and return states
are included regardless of results. The same frozen path is used by all arms.

There are 3 fixtures × 5 states × 3 arms = **45 comparison cells**, plus 15
complete-structure reference cells. Execute fixture-major then state-major;
rotate the arm order by `(fixture_index+state_index) mod 3` from the fixed
base order cold, retained, retained_shift. This balances positions imperfectly
and does not replace repetitions or make tiny timings generalizable.

## Arms and certificate contract

Each arm independently pays for a cold state-zero solve. The cold arm also
reinitializes every later state. Reuse arms import only their own immediately
preceding certified pool for the same fixture, config, instance and market
identity. They replay original trip coverage, chain/arc ownership, charge
windows and power, battery trajectory, terminal SOC, aggregate loads, intrinsic
cost, oracle metadata and column keys. Stored success flags are insufficient.
No pool crosses a fixture or arm. All retained columns are copied; old bounds,
prices other than the proposal input, tangents, duals and retry state are reset.

The shifted arm issues exactly one full pricing solve per transition at
`q_previous_clean + a_new-a_previous`. It pays even on an identity state or
when the proposal is a duplicate. The shift is a proposal, not a prediction
with a guaranteed improvement and not a certificate. Every newly generated
replay-valid key, including terminal clean-pricing columns, is retained in all
arms. No eviction is allowed. A projection-level novelty flag separately checks
load and intrinsic cost within 1e-7, so roundoff keys are not reported as useful
new discovery. This diagnostic flag does not alter column admission.

Every state runs fresh clean `b2a2.solve_rmp` and complete `solve_taker` pricing,
with production reconstruction/canonicalization. The only accepted lower bound
is accumulated within that state from:

`LB = z_model + min(0, clean_pricing_lower_bound - sigma)`.

The upper bound is the physically replayed convex combination of intrinsic
cost plus the exact quadratic system cost. Replay verifies the returned master
weights, aggregate load and objective; replenished masters additionally check
45 kWh energy conservation. Stop only when UB−bestLB <=0.01 with master tangent
slack <=0.001. Only clean pricing may update LB. No proposal or previous-state
bound participates. Unresolved status, nonfinite/reversed pricing bound,
replay failure, exhausted cap or duplicate improving pricing fails the state.
Bounds are numerical, conditional on CBC and replay tolerances, not formal
exact-arithmetic certificates.

## Independent formulation and audit evidence

After **all comparison arms have finished**, run the separate continuous
complete-structure formulation from `physical_qualification.solve`. It
enumerates every structure, uses its own lambda-scaled SOC/charging polytope,
replays every scaled witness and refines tangents to <=1e-5 cost slack. It is
independent of the restricted-column iteration, but shares the enumeration
helper, basic instance/market code and CBC backend. It is not independent
software or exact arithmetic, and a non-author audit is still required.

A completed comparison must agree with the matching reference: its certificate
and the reference's guarded lower/upper interval must overlap within 1e-6.
The raw state records say reference validation is pending; only the final
summary's `reference_check` establishes that this second phase succeeded.
A disjoint interval, identity mismatch or missing reference makes the aggregate
run incomplete. References never seed a price, column, tangent or stopping
rule. Save every enumerated structure and its charging/weight witness, the
reference native optimization records, and all comparison prices, bounds,
master weights, column-key snapshots, generated columns and charge events so
an external reviewer can reconstruct each claimed certificate.

## Budgets, failure handling and interpretation

CBC only, one thread, sequential subprocesses; no Gurobi initialization. Caps:
48 pricing attempts per state (including seeds/proposals), 240 retained keys,
10 seconds per optimizer wrapper/native model phase, 60 seconds per state or
reference process, 256 enumerated structures per reference, and 900 seconds
of total solve admission. The separate qualification reference retains its
fixed 160-refinement and 10-second native-call caps. Hard subprocess deadlines
kill the entire process group. No automatic retries, hidden replacement
instances or post-outcome expansion. A failed predecessor prevents later reuse
cells; independent cold cells and references may continue within the budget.

An output root is created exclusively. Store the frozen config, canonical
fixtures, commit, all driver/helper/production dependency hashes, interpreter,
package versions and actually selected CBC library hash. Persist pending
pricing and optimizer-wrapper attempts before running them, and record
completed or exceptional attempts afterwards. Preserve traceback, subprocess
exit status, timeout, stdout/stderr and partial JSON. Failed/timeout cells are
not certified time-to-solution observations. A killed reference can have an
incomplete final native-call list; its process timeout and partial state remain
explicit, with no imputed successful cost.

Primary work measures are total pricing calls (seed, clean, proposal separately)
and complete subprocess wall time, including imports, replay, file persistence
and proposal overhead. Also report optimizer-wrapper calls, clean-master LP
calls, reported solver wall time, wrapper elapsed time, worker CPU and initial
replay time. Wrapper records can include an LP-first phase and are **not** a
count of individual native optimize invocations. Accounting/persistence adds
overhead symmetrically. Retained clean calls beyond the first mandatory final
verification show unresolved work on this diagnostic, not a proof that ML can
remove it. Compare all cells and retain failures in tables. Do not infer a
runtime speedup distribution from this single small fixed grid.

A learning campaign remains gated on reproducible useful discovery work beyond
reuse and on a separately frozen train/evaluation design. Regardless of outcome,
this grid may justify a larger diagnostic or an algorithmic comparison; it
does not itself establish learning efficacy, external validity, operational
charging feasibility beyond its stated assumptions, or journal readiness.

## Invocation after root freezes source

```sh
../.research-venv-repaired-1176/bin/python -B src/experiments/reuse_frontier.py --output NEW_EXCLUSIVE_DIRECTORY
```

Fake-oracle tests may be run before source freeze. They do not optimize any
scientific instance. Run no scientific experiment until root explicitly
confirms the source/protocol commit is frozen.
