# CF1 pure greedy construction and bounded undo

24 October 2026. New `src/egglab/constructive_control.py` only; qualified native,
replay, runner, coordinator and CA1 sources are unchanged. No runtime import,
test, solver, dataset/model access, fixture generation or execution was performed
by the construction implementation agent. This implements topology construction,
not native charging completion, a composite orchestrator or a60-second schedule.

## Interfaces

`construct_routes(case, *, deadline, clock=time.monotonic)` returns a JSON ledger
with `status` (`proposal`, `no_proposal`, `deadline`), reason, case/policy identity,
selected and diagnostic candidate movement IDs, routes, initial routes, merge
history, round diagnostics and a ledger hash. Selected IDs follow original
movement order and are empty unless status is `proposal`. Routes include ordered
trip/movement IDs and a scalar optimistic screen. Inputs are not mutated.

`undo_merges(case, ledger, count=1, *, deadline, clock=time.monotonic)` reconstructs
from initial routes and the active history prefix. It removes the last one or
two merges in reverse insertion order, at most two cumulatively across calls.
Unavailable/exhausted/invalid counts raise `ValueError`. Valid nonexpired input
requires matching policy, case identity and ledger hash. A repair can restore too
many vehicles or an optimistic-invalid route, yielding no proposal. It does not
select a repair using a bill, feasible-route label or other oracle. A future
orchestrator must call it only under its prospectively qualified repair policy.

Both interfaces require the caller's finite **absolute deadline** and use that
value directly; neither derives a new endpoint from the current time. Exact
deadline entry is closed. Checks occur before construction/undo work and within
movement, window-slice, candidate, leg and service loops, around nonpreemptive
validation/path recovery, and after ledger hashing. Metadata preparation,
reconstruction and hashing remain part of the caller's timed method. Expiration
returns a failed deadline ledger, never fresh proposal time. The ledger retains
the original construction deadline and each supplied repair deadline; future
stage/global clock allocation belongs to the caller.

## Deterministic construction

One route is initialized for each trip in `(start_min,end_min,id)` order.
Pullout/pullin choices minimize `(sum of all leg minutes,id)`. Missing individual
boundaries return a proposal failure before graph reachability validation; they
are not a global infeasibility certificate. Intermediate route count may exceed
`max_vehicles`. Initial screen failures are retained and counted: a later merge
can remove an early terminal window or expensive initial pullout and become
eligible, so no initial optimistic failure prematurely stops construction.

Single-vehicle capacities intersect the exact depot-split or verified terminal
pullin window with resource/market slices. They use grid kWh at the minimum of
per-bus and grid power, connector zero supplies no capacity, and efficiency
converts grid energy to battery energy. The route screen starts at full battery,
subtracts each individual leg/service energy, tests reserve after each subtraction,
allows charging only at the declared depot gap, caps SOC at battery capacity,
and requires enough terminal capacity to replenish fully. It uses binary64,
`math.fsum` and the existing fixed1e-6kWh ranking/screen tolerance. It ignores
shared connector/power contention, so a passing screen proves no fleet feasibility.

Each iteration examines declared direct/depot links from a route's last trip to
another route's first trip. Joined routes remain chronological and disjoint.
Only screen-passing joins are eligible. The lexicographic key is added all-leg
minutes, negative added **grid** capacity, movement ID, left first-trip ID and
right first-trip ID. Added minutes remove both replaced boundaries; added capacity
removes the old left pullin capacity (right pullouts have none). The minimum join
is inserted, then enumeration repeats until no eligible merge remains.

Only after construction ends are final optimistic screens and the vehicle cap
used to decide eligibility for `native_pathflow.recover_paths`. Structural recovery
must match the proposed paths exactly. No model is built and no optimizer is
called. A proposal is an uncharged topology requiring later fixed-topology
charging, independent fleet replay and exact billing before physical admission.

## Audit and qualification limits

History stores O(N) merge operations with route references, removed boundary IDs,
rank components and scalar screens, rather than full route-state snapshots at
every insertion. Initial and current routes each store O(N) path IDs. Round
diagnostics retain examined/eligible/rejected counts and whether enumeration
completed, including partial rounds on timeout. Frozen inputs and deterministic
policy permit reconstruction; all rejected candidate states are not duplicated.
Straight route re-screening remains within the specified conservative
O(N²MR) bound; validation and final audit costs are also charged. Working storage
and histories do not grow as O(N²) full snapshots.

No minimum-fleet, optimum, feasibility or full-bound certificate is claimed.
Independent fake tests/review and one parent-authorized source-bound check are
still required; this note claims no execution outcome. Current carry remains
1294.1180143401803s, ADMIN0, under1800/1620/180 and one thread/5GiB. Parent owns
all future execution/accounting; this package creates no numerical attempt.
