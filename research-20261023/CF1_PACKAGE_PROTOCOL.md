# CF1 construction and fixed-route charging source package

24 October 2026. This package implements the next candidate classical control
after the common selector and CA1 unit gate. It uses the frozen
`RECOVERY_CLASSICAL_BASELINE_SPEC.md`, with the clarifications below established
before any outcomes. No dataset, timetable generator, learned model, native
solver, comparison, cluster job or 60-second coordinator is run in this package.
The qualified native/coordinator/replay sources remain unchanged.

## Bounded source scope

New `constructive_control.py` constructs a price-blind route topology from
declared movements. Start one route per trip, selecting shortest declared
boundaries by all-leg minutes and movement ID. Initial route count may exceed
the fleet cap, and an initial optimistic SOC failure may be repaired by a later
merge with a different terminal window. Do not stop solely for those reasons.
Missing declared boundaries are construction failure, not global infeasibility.

Greedy merges use exact declared last-to-first direct/depot connections,
chronology and unique service coverage. Screen the entire proposed route with
full initial battery, per-leg and service consumption, reserve at every stage,
eta times individual grid charging capacity only in declared windows, and enough
terminal capacity to reach full battery. Connector zero contributes no charging.
Use the frozen binary64/fsum/tau convention. Shared fleet contention is omitted
here intentionally; this optimistic screen certifies neither actual feasibility
nor impossibility. Merge keys are added deadhead, negative added charging
capacity, movement ID and route first-trip IDs, exactly as specified. Keep
original inputs immutable and deterministic identities/history. Reverse at most
two inserted merges for later repairs; never use a feasible reference oracle.
Check an absolute construction deadline during enumeration and evaluation.

New `constructive_charging.py` accepts a topology without incumbent variable
values. Recover paths, build the ORIGINAL full compact path-flow physical model,
validate movement-binary inventory and fix every movement bound to its proposed
0/1 value. No physical row is removed or replaced. Reject hidden/unmapped discrete
variables or any unfixed noncontinuous variable; retain an inventory and actual
fixed/unfixed types. Fixed typed binaries need not disappear from num_int, so do
not claim a native LP or zero integer count merely from fixed bounds.

Attempt charging feasibility and then at most two target-market tangent solves:
first slopes a/intercepts0; after that objective's valid replay add tangents
(a+b*L,-b*L*L/2). Independently extract/replay each candidate and compute exact
quadratic bill. Retain the cheapest replay-valid feasibility/objective candidate
through a later timeout, unresolved status or extraction failure. Raw model
captures precede extraction. Fixed-route bounds/statuses are never unrestricted
bounds or full-model optimality certificates. Only a qualified INITIAL charging
feasibility INFEASIBLE may permit topology repair; objective infeasibility,
no incumbent, invalid replay and timeout do not. The supplied absolute deadline
is shared by all phases and later repairs; no helper-created fresh6-second clock.
The future caller must compute it ONCE, before the initial setup/build, as
min(t0+0.2*T, first_completion_anchor+max(2,0.1*T)), and reuse it across every
repair/rebuild. Passing only t0+0.2*T can exceed the common completion allowance
when construction finishes early. Recomputing now+6 for a repair is invalid.
The helper-only API cannot independently enforce that absent caller policy;
its unit gate must not be presented as doing so. Setup, build, inventory,
native calls, extraction, replay, repairs and records count inside that window.

This source package does not yet orchestrate durable fallback/start submission,
repairs across helper calls or the 60-second full-search schedule. Those require
separate affected-path review and a prospective native preflight. Do not call the
whole CF1 arm qualified from a pure/fake test pass.

## One focused solver-free gate

After all new source, tests and independent notes are stable, freeze exact hashes
and argv in `constructive-controls-checks/command.json`. The parent alone may run
one fresh `attempt01` check executing only `test_constructive_controls.py`.
Use handwritten symbolic cases and fake native hooks, guarded against actual
backend imports. Test physical counterexamples, merging/undo identities,
nonmutation/deadlines, fixed-binary/row/type inventories, replay-based candidate
retention and status/bound-scope distinctions. Qualified historical tests in the
hash closure remain explicitly unexecuted dependencies. No broad/native matrix
is repeated.

Carry **1294.1180143401803 s** from
`classical-controls-checks/accounting.json`, including every prior failure and
conservative charge. ADMIN0; the single shared20s is already inherited. The
approved hard1800/dispatch1620/shutdown180 limits, one single-thread worker and
5GiB owned RSS persist. Prospectively reserve40s including supervision for one
check:30s work,32.5s outer cleanup plus7.5s provision, ending1334.1180143401803s
under the planning allowance. Actual complete charges count. No automatic retry
or cap reset. Sampling, ownership, cleanup and accounting helper bodies remain
unchanged from the reviewed prior wrapper. No numerical dispatch follows a pass.

The one parent command, only after source/metadata freeze, is:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 \
.venv-local/bin/python research-20261023/run_constructive_controls_checks.py
```

Review complete receipts and preserve failures/spend. A source/unit milestone is
not ML performance, generalization, novelty or publication readiness. Update the
research handoff and GitHub backup; no routine Google Doc append is warranted.
