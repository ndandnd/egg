# Resource recourse owner: static draft

`run.py` is a new, unexecuted serial owner for the direction in
`../route_resource_mechanism/STUDY_DECISION.md`. It imports no old campaign and
does not modify any existing physics, solver, scoring, or controller source.
An actual `LAUNCH.json` must declare `mode: FROZEN`,
`review_disposition: PASS`, and the exact worktree before the owner creates its
fresh `attempt01`, imports project modules, reads TRAIN tables, or starts work.
This note is not execution clearance. Parent protocol, exact command, source
review and launch binding remain required.

## Frozen design represented by this draft

The fixed order is 10001/20, 10006/20, 10009/28, 10005/28, with grid capacities
90 and 45 kW. Only the stored SOURCE0 plan supplies reference topology and fleet
N. Variant construction changes the case name and resource grid cap; bus power,
connectors, trips, movement graph, tariff definitions and other physics remain
unchanged. The ledger contains eight fresh fixed-topology acquisitions followed
by 32 active assignments (two tariffs and fixed/adaptive arms per variant).
Active arm order alternates deterministically. Nothing replaces a missing cell.

The two pinned TRAIN JSONL files are streamed once each, including whole-file
SHA256; JSON decoding for routing is transient. Nonselected groups and selected
groups' SOURCE1 plan records are discarded without semantic plan analysis.
Both full table pins must pass before four original SOURCE0 physical replays.
Cases use the actual dataclass fields/defaults and retain numeric values/order.
Original plan identity, unique selected membership, recovered canonical paths
and fleet are admitted before variant work. Eight no-solve counterfactual
reference replays preserve the original charging schedule, changing only its
case identity. Rejection under 45 kW is a reported invalid reference, never
fixed-topology infeasibility and never a fallback.

The optional fixed denominator is the original SOURCE0 witness's mean exact
electricity bill across the original two tariffs at 90 kW. It is computed before
worker outcomes, stays fixed across resource/arm comparisons, and is undefined
when nonpositive. Absolute cost components are primary; this is neither the old
four-witness Ebar nor warm-replanning E0.

After source admission, preflight imports the already-bound local `classical.py`
once by explicit file path. Each variant records its pure `opportunity` diagnostic
on original SOURCE0 paths: per-bus demand/grid energy/SOC margin, common terminal
start/capacity, selected depot windows, cheap 18–21 capacity and conditional
energy-fit quantities. This ignores the old plan's case-identity string only for
the structural diagnostic. It neither replays that plan as a fallback nor claims
an ideal capacity diagnostic certifies feasible charging or optimality.

## Worker interface and admission

The CLI is `worker.py --worker ABS_FOLDER --parent-anchor FLOAT --spec-sha256 HEX`.
The parent anchors before `Popen`; each immutable spec carries root, task ID,
phase, group/base/service/grid identity, full typed-case encoding, expected case
identity, exact reference N/selected IDs, original SOURCE0 plan hash, optional
fresh acquisition plan, tariff source/identity/a/b, and optional canonical
acquisition-plan hash, E_ref and original-reference bill. Acquisition tariff
fields are null. Only a current-variant newly acquired plan may be passed as an
active fallback. None is valid for every optional field.

Fresh acquisition admission includes child return, receipt read, one read/hash
of its owned best-plan artifact, parent NR replay, canonical fixed paths/N, and
two-tariff component reconstruction inside the parent's complete-read 60 seconds.
Late or invalid acquisitions are not cached. Fixed active work with no admitted
fresh prior is explicitly missing; adaptive exact-N full-graph routing remains
cold eligible. An accepted active physical result supplies the endpoint;
otherwise only an admitted acquired prior supplies an operational fallback.
The original timed plan is never promoted to operational fallback.

Receipt flags keep timely physical endpoint, fresh QP qualification and full
method success separate. Adaptive routing follows the worker's 17.5/35-second
cuts and admitted-new-tangent rule; one QP uses the absolute 52-second native
cut and final admission is 60 seconds. This owner does not infer optimality from
an operational fallback or from an administrative successful campaign closure.

## Source and resource closure

The upfront ten-file source set is these three new files (`run.py`, `worker.py`,
`classical.py`), unchanged `topology_charging/worker.py` consumed dynamically as
a pure-helper library, unchanged `warm_replication/qp_control.py`, and the five
`egglab` sources `__init__`, `native_recharge`, `native_hull`, `native_pathflow`,
`physical_learning_cases`. The study decision, future protocol and launch are
also bound once. Imported pure-module paths are checked; there are no models,
training calls, score assets, pool quotas, repeated source hash passes or old
campaign calls. Final review must check this source closure against actual
worker imports and bind the implementation/protocol documents prospectively.

The NEW package is 4500 CPU seconds/7200 wall seconds, dispatch at 4140 CPU,
closure reserve 360 CPU. Preflight is at most 120 parent CPU; finalization is at
most 120 parent CPU/180 wall inside the package. Each of 40 potential workers
has hard CPU 90/90, one-thread environment and observed 5 GiB scope. Funding uses
actual cumulative parent plus waited-child CPU and a 90-second unresolved-child
reserve. Per-task CPU deltas are telemetry, not added again to cumulative CPU.
Historical closed packages are separate. Remaining wall funding includes child
60, cleanup 3, and finalization 180. The external whole-process meter must cover
publication/exit tails and confirm package actuals.

Child launch defers stop-handler exceptions through `Popen` and PID publication;
the latched primary stop then takes the ordinary owned-child cleanup path.
Cleanup directly targets only the unreaped owned child PID, TERM then KILL/reap
inside three seconds, preserving failures and unresolved CPU reserve. No stale
PGID signaling or unknown-process cleanup is introduced. Final publication
rearms only the remaining finalization/total wall allowance; incomplete owned
receipts remain if publication cannot finish.

## Reporting and limits

All 40 planned records survive preflight failure, missing priors, lateness and
funding stops. Operational costs/components include period loads, fleet,
deadhead, electricity, energy and represented arithmetic residuals. For each
tariff, routing gain is fixed cost minus adaptive cost; resource interaction is
gain45 minus gain90. A group's mean requires both planned tariff interactions;
the overall mean requires all eight planned interactions. No available-only
mean rescues missing cells. Ideal ordering remains unresolved; no statistical,
model-promotion or optimality gate is created.

`passed` means administrative ledger/accounting closure without owner failures
or unresolved child CPU. It does not mean every acquisition or method qualified;
the complete ledger, attempted/qualified counts, stop reason and missing
economic denominators expose those distinctions. No solve, replay, data read,
hash, source import, test, compilation or runtime qualification was performed
while preparing these draft files.
