# CF1 and fixed-topology charging contract review

24 October 2026. Narrow static review of the prospective CF1 specification and new construction/charging modules. Owned additions are this note and `src/tests/test_constructive_controls.py`. No tests, runtime imports, solver/backend, asset, fixture generation, protected data, cluster, qualified-core edit or numerical qualification occurred.

## Construction

The price-blind greedy constructor starts separate routes, orders boundaries by ALL leg minutes/ID and merges only declared chronological links. It checks SOC after each leg/service, before depot charging; optimistic grid energy is multiplied by eta, battery-capped, and terminal replenishment uses the verified pullin window. Power outside availability and connector-zero periods cannot supply energy. Fleet cap applies after greedy merging, allowing intermediate route count above the cap. Shared vehicle contention is intentionally not checked by this screen; no proposal is a physical certificate.

Merge keys implement incremental deadhead minutes, negative incremental GRID capacity, movement ID and route-first IDs. Compact operation history reconstructs deterministic LIFO undo without mutating the input; cumulative undo is at most two. A repaired route set above fleet cap remains diagnostic rather than a selected proposal. Construction and undo require absolute deadlines; future integration must authorize undo only from the charging helper's qualified initial-feasibility INFEASIBLE result.

## Charging

The helper builds the original full declared model and fixes every mapped movement binary to0/1, including unselected movements. It rejects duplicate/hidden/nonbinary mapping, unmapped discrete variables, identity/bound drift and physical-row signature drift. Remaining variables must be continuous, but retained binary types mean the helper explicitly avoids claiming native LP qualification.

It attempts zero-objective feasibility and at most two target-market tangent objectives. Capture precedes extraction; independent physical replay and exact Fraction billing precede witness publication. Minimum exact replay bill controls retention, not native solver score. A prior valid witness survives later objective/capture/replay failure. All subproblem lower bounds are labeled fixed-topology only; global lower bound remains absent. Only initial qualified INFEASIBLE with no incumbent authorizes reverse repair; unresolved/no-incumbent/timeout or objective-stage INFEASIBLE does not.

One material integration ambiguity was resolved explicitly: the caller must freeze ONCE, before initial setup/build, `completion_deadline=min(t0+.2*T, first_completion_anchor+max(2,.1*T))`, then reuse it across all repairs/rebuilds. Passing only stage end or recomputing now+6 is invalid. This conservatively caps the whole charging window, including setup/recording. The helper has no T/anchor/prior-allowance input and cannot prove that caller discipline. **The absent composite orchestrator and60-second/native integration remain unqualified**; this unit package cannot clear them.

## Focused unit scope

The new **31-case/20-function** symbolic/fake-native suite covers chronological deterministic merges and initial fleet excess; pre-depot reserve failure despite abundant later charge; successful depot charging versus an eta-induced failed merge with10 grid kWh and explicit minimum SOC; terminal eta/connector/availability limits; LIFO cumulative undo and post-undo cap; absolute expiry/nonmutation; optimistic shared-contention limitations; every binary bound, hidden discrete/mapping/identity/physical/bound drift; capture/extract/replay order; independent replay/topology rejection; exact bill differences lost by float totals; replay-based quadratic tangents; feasibility fallback retention; initial INFEASIBLE versus unresolved; and unchanged helper deadline across calls. No native model or outcome asset is loaded by the fakes. Both source owners independently read the respective fake/API alignment without finding a mismatch.

Parent provision is one solver-free check40 s including supervision, carry **1294.1180143401803 s**, ADMIN0. Planned end **1334.1180143401803 s** fits1800 hard/1620 dispatch/180 shutdown reserve, one thread/worker and5GiB. Actual complete charges and failures must be carried once. No native, model or comparison launch follows automatically.

**Final stable source/test contract gate: clear for one focused source-bound31-case solver-free check**, subject to parent freeze/review of the exact wrapper/protocol/command/inventory. No concrete blocker remains in this bounded source/unit scope. All tests and this note are source-stable at this gate; no test has been executed by this reviewer. This does not qualify the composite60-second orchestration, cumulative caller discipline, actual fixed-model native statuses/timing, physical witness performance or comparative study.
