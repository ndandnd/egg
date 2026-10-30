# Next classical baseline: global fleet-first physical path flow

Prospective design,25 October2026. No solver code, imports, tests, hashes or
optimization were executed to prepare this protocol. Existing qualified sources
and all earlier attempts remain immutable. This document is not launch authority.

## Decision and question

The existing API can express this control without a broad rewrite. Build the
original full physical path-flow model and minimize **vehicle count itself**,
with every routing binary free. Do one bounded native call, extract its best
available incumbent and independently replay it. Stop implementation if this
requires altering physical rows, disabling extraction/admission checks, replacing
native hooks or introducing a new controller. Do not repair the greedy merger or
reuse its routes as a hidden initial solution.

The question is whether a conventional global physical formulation can acquire
a substantially smaller feasible fleet than the observed local greedy rule.
It is not a matched learned-versus-classical trial, a speedup experiment, proof
of optimal fleet count or qualification of the main CF1/recovery schedule.

## Frozen competence cases and fresh output

Reuse only `scale:50685:40` and `scale:50605:80`, the previously selected,
already inspected development screen cases. These outcomes are exposed; do not
describe them as fresh evaluation data. Rebuild with `claude_cases.make(key)` and
verify exact case identity/movement order against the existing
`research-20261017/local-assets-v3.json` case records. Use the original day market
for post-solve exact cost evaluation. No model inference, new timetable, protected
DEV/TEST/A6/B3/confirmation/GIRO or cluster access.

A proposed new research-only driver is
`research-20261025/classical_competence/fleet_first.py`, writing exclusively to
`research-20261025/classical_competence/fleet-first-attempt01/`. Neither exists
by virtue of this protocol; implement/review the thin driver and freeze its exact
command before dispatch. Never overwrite or resume `attempt01`.

## Exact API route

Use `egglab.native_pathflow` as `pf`, `native_recharge` as `nr`, `native_hull` as
`nh`, and the existing backend library `mip`. No monkeypatch or callback changes
to `pf.build_feasible_model`, `pf._optimize_once` or extraction are permitted.

1. **Build:** `built = pf.build_feasible_model(case, 'GRB')`
   ([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:151)).
   This retains service coverage, routing, SOC/reserve, charging/grid constraints,
   aggregate energy band and load equations. Its returned `x[j]` corresponds to
   `case.movements[j]`; `constraint_count_before_objective` identifies the original
   physical rows. Do not fix routing binaries, remove movements or loosen bounds.
2. **One physical inventory:** record case/compiled identities, the complete
   movement-to-variable map, original binary0/1 bounds, remaining variable types,
   row/column counts, backend identity and the physical row signatures ONCE.
   The existing `constructive_charging._row_signature(row,check=...)` exposes the
   row representation; stream signatures to one separate artifact rather than
   nesting copies in every event. Do not call `_inventory` repeatedly: its
   fixed-topology ledger semantics are inappropriate for free routing binaries.
   Assert that no extra physical/objective rows are added by the next step.
3. **Fleet objective:** define

   ```python
   fleet = mip.xsum(var for movement, var in zip(case.movements, built['x'])
                   if movement.kind == 'pullout')
   built['model'].objective = fleet
   ```

   This is exactly the builder's vehicle-start expression
   ([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:171));
   the model is already minimization. Use this expression rather than `built['ops']`
   so nonzero deadhead costs cannot silently change the target. Leave default
   solver seed unmodified; record default/unknown numeric value and threads1.
4. **Solve once:** call
   `pf._optimize_once(built, nr.Budget(backend='GRB',threads=1,phase_seconds=cap,wall_seconds=remaining,max_rounds=1), native_deadline)`.
   Here `cap=min(60,native_deadline-now)` and `remaining=case_end-now`, both
   strictly positive. The unchanged helper clamps native time to the absolute
   remaining deadline and reports status/incumbent/bound/backend/resources
   ([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:502)).
   Require `OPTIMAL` or `FEASIBLE`, a finite incumbent and native threads1 before
   extraction. A no-incumbent/time-limit result is unresolved, not infeasibility.
5. **Capture/extract once:** save one
   `pf.capture_incumbent(case,built)` as its own artifact; call
   `plan = pf._extract(case,built,record=stream_event,round_index=0)`
   ([capture](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:252),
   [extraction](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:352)).
   Preserve its whole-incumbent roundoff/projection/serial-decoding checks and
   internal replay. This entry performs no additional optimization. Do not call
   `solve_planner` or `complete_topology`, which would introduce other objectives,
   additional solves or repeated inventories.
6. **Independent admission:** call `replay = nr.replay_native(case,plan)` again.
   Require original identity, exact-once coverage and successful physical replay.
   Verify number of plan vehicles equals selected pullouts and the native fleet
   incumbent within the existing numeric tolerance; reject inconsistency rather
   than rounding an arbitrary incumbent into a witness. Recompute
   `Fraction(replay['ops_cost']) + nh.supply(day_market,replay['load'])` and save
   plan/replay/exact objective, projection diagnostics and all native statuses.
   Preserve all existing tolerances; no new permissive allowance.

The stored native bound belongs to this fleet-count objective and this stored
physical matrix. It is not an electricity-cost bound. An `OPTIMAL` native status
alone does not remove numerical/replay qualifications or create a full economic
certificate. A replay-valid incumbent obtained before the final cutoff remains
a useful feasible fleet even without optimality proof.

## Fleet-first is not weighted economic optimization

This first packet minimizes only `F=sum(pullouts)`. Charging retains the original
physical constraints but can be economically arbitrary; only replay-valid plans
are physically admitted. The exact post-solve integrated
system cost is reported, not claimed minimized. In contrast,
`100*F + a'L + .5*sum(bL²)` trades vehicles against electricity and need not select
minimum fleet. Adding a large unproved weight is not lexicographic optimization.

No secondary solve is included. A later lexicographic study would first establish
or explicitly qualify the best fleet count, then fix that fleet count and optimize
the secondary cost on unchanged physical rows. With a merely feasible first-stage
count, this would mean cost optimization at the best count found, not proof of a
globally lexicographic optimum. Do not quietly add this second stage here.
Because charging has no cost in this packet, numerical incumbents can still
fail the unchanged whole-incumbent projection/extraction checks. Preserve that
failure rather than relax tolerances, infer physical infeasibility or silently
add a charging refinement solve.

## Practical prospective budget and receipts

Propose a new360CPU-second package, outer wall300 seconds, one process/native
thread and observed peak RSS<=5GiB. Each case has120 seconds from before case
construction: preparation/model build/one inventory through30, native search
through90 (at most60 native seconds), capture/extraction/independent replay and
durable output through120. The60 remaining wall seconds cover shared imports,
input/source identity checks and final closure. Retain at least15 seconds of
package headroom for final records. Every actual cost, including failure and
serialization, counts; no clock reset after preparation. Parent review may shrink
the envelope prospectively, never enlarge a running frozen trial.

Use an ordinary parent-owned process cap and the simple existing offline receipt
pattern; no new timing controller or inventory framework. Start exclusive
incomplete receipts, stream events/capture/inventory separately, and retain
per-case CPU/wall/RSS, model-build/solve/extract/replay/materialization times.
Do not duplicate the full capture/history inside a nested case receipt. Native
time limits and cooperative checks are not hard preemption guarantees; late
outcomes remain late. A complete diagnostic may contain zero feasible cases.

Compare vehicle counts to the old greedy15/29 and historical graph endpoints
only as unmatched, reused-case context. Default seed, objective, allocation and
case exposure differ. No paired GNN win, speedup or population inference.

## Optional route-only bound, excluded from the first packet

For a declared chronological compatibility DAG, split each trip into left/right
copies and find maximum-cardinality bipartite matching over declared compatible
intertrip links. `N-|matching|` is the minimum path count in that route-only DAG
and a lower bound for any physically feasible fleet whose routes use those
links. Secondary deadhead cost can break ties among maximum matchings.
It ignores accumulated SOC, charger contention and replenishment, so the matching
paths themselves are not an electric-fleet witness. This optional diagnostic
requires a separately specified implementation/budget and must not add another
solver call to this first competence packet.

Proceed next only if source review confirms these exact objective/build/extract
operations work with the existing API. Otherwise record the blocker and stop;
do not broaden into a new formulation, recovery pipeline or permissive replay.

## Static implementation addendum

The parent accepted the prospective360CPU/300wall package. `fleet_first.py` is
now implemented, unexecuted and held for one static peer review. The exact
intended child command is:

```
.venv-local/bin/python research-20261025/classical_competence/fleet_first.py --root /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017 --output research-20261025/classical_competence/fleet-first-attempt01
```

The parent freezes source/command and supplies the outer stop before dispatch.
The script uses CPU hard limit360, alarm300, cooperative body345CPU/285wall and a
persistent first-stop latch. Its top receipt and case receipts begin as exclusive
incomplete placeholders and publish by replacing only their own placeholders.
Per-case `physical-inventory.jsonl`, `native-capture.json`, `events.jsonl`,
`plan.json` and `replay.json` stay separate; receipts contain paths, stats and
stage costs, without nested full captures. Unbounded continuous variable bounds
are represented as finite-value-or-null plus raw repr, following the native
capture convention; no bound is changed.

The master `accepted_within_offline120` additionally requires receipt-inclusive
elapsed<=120. A zero-exit complete diagnostic can contain unresolved cases;
inspect feasibility flags separately. Stops prevent further case dispatch.
Consumed compact context inputs and the actual small imported project-source
closure are hashed once in-process. There is no compile/test run or general
monitoring framework, and no production-source edit.
