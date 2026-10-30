# Fixed-physics reuse qualification, frozen before execution

This is a small engineering check of continuous charging and fresh-state
column reuse. It allocates no random seeds, accesses no training/test data,
and launches no cluster jobs. It does not execute or amend the PR53 pilot.
No learned model, protected holdout, shared-capacity claim, or performance
generalization follows from passing this qualification.

## Physical fixture and trajectory

The hand-authored fixture has one bus, two depot-to-depot trips at minutes
0–60 and 180–240, each consuming 15 kWh. Battery/initial energy is 20 kWh;
SOC and terminal floors are zero. Charging power is 10 kW, with two one-hour
windows between trips; fleet cost is 10 and deadhead cost is zero. The bus
must charge at least 10 kWh. Charging remains continuous; this is not a
finite menu of preselected charge quantities. This fixture has no shared
charger/grid capacity: the separate physical qualification covers that
explicit extension.

There are four states, a three-state tariff trajectory with an inserted
zero-change control: `a=a0`, `a=a0`, `a=a0+0.2*v`, `a=a0-0.2*v`, where
`a0=(0.3,0.3,0.3,0.3)` and `v=(0,1,-1,0)`. All states have `b=0.2`, `U=0`.
The complete feasible set and all intrinsic costs stay fixed.

Positive marginal energy cost implies exactly 10 kWh at optimum. Writing
the slot-1 load as x gives slot-2 load 10-x, with 0<=x<=10. Independently,
`x=(a2-a1+2)/0.4` clipped to [0,10]. Expected optimal loads are (5,5),
(5,5), (4,6), (6,4) in charging slots, with objectives 18,18,17.8,17.8.
This charging segment is already convex, so its physical and CH optima agree.
This analytic solution is used only to audit completed results, not to seed
columns, prices, tangents or lower bounds.

## Arms, isolation and certificate

Run cold clean CG, retained columns, and retained columns plus one analytic
price proposal. Each arm independently pays for a cold state-zero solve.
Later cold states also start cold. Reuse arms import only their own immediately
preceding certified pool. Every imported column is replayed from its physical
schedule and charge events; instance identity, coverage, charge ownership,
window power, SOC, loads, intrinsic operating costs and column keys are checked.
Stored replay flags alone are insufficient. Never fold a market charge into
`ops_cost`.

The analytic arm issues exactly one complete pricing solve per transition at
`q_previous + a_new-a_previous`, using its own previous final **clean** RMP
price. Admit a replay-valid novel column; count duplicate and unsuccessful
proposals in time and call budgets. The unchanged-market control still pays
for this proposal. No fallback predictor or repeated proposal is allowed.

Every new state resets tangent points, duals, lower/upper history, retry state
and solve records. No production checkpoint identity is edited or bypassed.
The standalone adapter calls `b2a2.solve_rmp`, `solve_taker`,
`canonicalize_pricing_solution`, `column_from_solution` and
`pricing_incumbent`. It uses the same clean-master certificate as A2:

`LB = z_model + min(0, pricing_lower_bound - sigma)`;
`UB = intrinsic weighted cost + exact quadratic system cost`.

Only full pricing at a freshly solved clean-master price `q=-pi` contributes
to LB. Old and proposal bounds do not. The final interval must have width
<=0.01, with tangent slack <=0.001; it must enclose the independently derived
optimum. Duplicate improving pricing, invalid replay/bounds or unresolved
solver status fails the state. All arms retain every novel generated column,
including terminal pricing columns. The common pool cap is 96, the maximum
number of pricing calls over a four-state trajectory. No eviction should be
needed; exceeding the cap fails rather than silently changing the policy.

## Fixed local bounds and observations

Only CBC, one thread, sequential state subprocesses. Twelve state-arm cells,
24 pricing calls/state including seed/proposal, 10 seconds per native solve,
40 seconds per state subprocess, 300 seconds total solve-admission budget.
The supervisor kills a state process group at its deadline; solver model time
limits also cap the LP-first phase. Subsequent reuse states are skipped after
an unresolved predecessor. There are no automatic retries or result-driven
expansions. Output roots are created exclusively and cannot be overwritten.

Record fresh master objectives, tangents, all LP/MIP solver statistics,
prices, certified pricing bounds, proposal novelty, reduced-cost bounds,
full column evidence, replay cost, worker CPU, solver time, and complete
subprocess time including interpreter/import/input/output overhead. The latter
is the primary complete-time measure. Running tiny cells in separate processes
is conservative and noisy; no speedup claim or ML go decision is allowed.
The fixed execution order is state-major, then cold/retained/retained_shift.

Successful qualification establishes physical/identity/bound correctness of
this adapter on this fixture. It does not establish utility on larger fleets,
multiple network structures, harder pricing or shared-capacity changes. A
later reuse workload must be separately frozen before outcomes, then show
avoidable discovery work before an ML campaign is justified.

## Invocation

After the source and this protocol have been frozen in a commit, run the
repaired, recorded interpreter with:

```sh
python -B src/experiments/reuse_qualification.py --output NEW_EXCLUSIVE_DIRECTORY
```

The supervisor records the exact source hashes, commit, interpreter,
configuration and mip/cbcbox/numpy versions. Each worker records the actual
selected CBC library path/hash after native initialization under the watchdog;
`worker-runtimes.json` consolidates those records. The output directory holds
each state, stderr/stdout, provenance and a summary. Partial failures remain
evidence and must not be relabeled as
certified time-to-solution observations.
