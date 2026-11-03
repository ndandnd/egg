# Fixed-duty composition by reference: source contract and remaining seam

Source-only inspection of the registered sibling checkout
`/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001`,
at the parent-named revision `3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c`.
No import, Git/hash query, input, fixture, plan, outcome, test, replay or solver
was run. Sibling source is not copied or edited. This note is not a numerical
manifest or runtime-compatibility qualification.

## Actual fixed-duty entry point

`src/run_fixed_duty_terminal.py:1–9` fixes passenger-trip sequences but frees
charging times **and stations**. Its `main()` is data/CLI coupled: data directory,
GIRO CSV, tariff file and output directory are required (`:56–75`), then it
builds a `TerminalEnergyNetwork` with hardcoded240-kWh/350-kW/zero-reserve
settings (`:77–79`). Do not invoke that CLI for synthetic in-memory work.

The reusable lower-level call graph is:

1. Validate an ordered duty list partitioning `problem.trips`. The existing
   GIRO-specific reconstruction wrapper checks exact coverage and time order
   (`run_fixed_duty_terminal.py:39–53`); a synthetic caller supplies its own
   literal duties rather than calling that data reader.
2. `terminal_duplicate_cleanup.frontier(net,trips)` walks only successive trips
   of a given sequence, keeping the cheapest predecessor per graph state, then
   cost/terminal-energy nondominated sink records (`:20–45`). It delegates record
   construction and physical audit; it is not a copied independent solver.
3. `validate_terminal_pool_partition.solve(routes,trips,*,target,cap,seconds,
   log_dir,threads=1)` selects exact-once service, fleet≤cap and aggregate return
   energy≥target, first minimizing fleet and then charging cost (`:16–59`).
   When the supplied duties partition service, each frontier option covers an
   entire duty, and the selected pool contains no other routes, exact-once service
   picks one option per duty. The CLI checks that duty-ID correspondence
   (`run_fixed_duty_terminal.py:115–118`).

That master has **no plug-capacity rows**. The frontier's cost/state and
cost/return-energy dominance do not preserve distinct occupancy profiles needed
under future plug duals. Attaching plug constraints after generating that
frontier cannot be called a complete capacity-aware fixed-duty optimization.
Passing a capacity network object into the old frontier does not repair the
frontier recurrence's static dominance or make its retained pool exhaustive.

## Capacity-aware route-changing callable

The existing common callable is:

`run_capacity_terminal_cg.run(net,out,*,target,fleet_cap,cg_seconds,mip_seconds,
batch_size=30,seeds=(),max_iters=100000,rc_eps=1e-6,viol_tol=1e-6,
smoothing=0.,dive_seconds=0.,dive_theta=.7,partial_pricing=None,
directional=False,dive_mode='simple',dive_options=None,
integer_pricing_seconds=0.,integer_pricing_options=None,partition=False)`
(`src/run_capacity_terminal_cg.py:46–57`). It accepts an already built network;
there is no need to invoke `main()`/`build_problem` or read GIRO files.

- `partition=True` makes trip rows exactly1; default is covering≥1. Aggregate
  terminal energy is≥target and fleet is≤cap (`:67–70`). This is not exact N.
- Plug rows are station-minute occupancy constraints (`:118–133`), not a shared
  transformer-kW limit. Existing capacity-aware pricing re-costs alternatives
  under current duals. The final integer pool includes all touched potentially
  binding plug rows (`:330–332`).
- Integer optimization is **fleet first, then charging under the attained fleet
  cap** (`:334–363`); it is not a fixed-N charging objective by parameter name.
  `partition=True` cannot be combined with integer-aware pricing
  (`:50–53`). For the minimal seam leave those optional heuristics off.
- Existing seed records are refused with a nonuniform station-power map
  (`:136–141`). Start with `seeds=()`; do not import/relabel old columns.
- `cg_seconds` is not an end-to-end bound. The expiry/iteration closure can
  call a300-second re-solve (`:275–281`), and graph build/import plus later
  integer stages are separate. A future experiment needs an externally paid
  process deadline, preserving late/unresolved results rather than overriding
  the sibling scheduler or claiming one native-call budget.

The record and source-declared pricing certificate concern the conservative
event graph/capacity LP when pricing and row separation finish. The integer MIP
proof concerns only its generated pool (`:284–299`). Neither is an unrestricted
continuous EVSP or new EGG physical certificate.

## Smallest capacity-aware fixed-duty seam

Use the **same capacity pricer and master by reference**, with an EGG-local
subclass returned by `make_fixed_duty_network_type(base_type,duties)`, receiving
the caller's already loaded `CapacityTerminalNetwork` class. No new importer,
copied pricing/DP, station aggregation or sibling edit is needed.

Before the parent constructor builds any graph, validate nonempty ordered duties
forming a unique exact partition of `problem.trips`, and form first/next/last
maps. Override only these inherited generators and delegate all numerical work:

| Method and source | Actual yielded tuple | Allowed transition |
|---|---|---|
| `_source_candidates()` (`event_pricer_network.py:412–422`) | node,cost,trip,action | trip is a duty's first |
| `_direct_candidates(trip,soc_exit,depart)` (`:439–472`) | target,cost,successor,action | successor is that trip's prescribed next; None only at its duty's last |
| `_charge_candidates(trip,soc_exit,depart)` (`:480–551`) | target,cost,successor,action | same successor rule, leaving station/time/energy alternatives untouched |

Filter before inherited `_add` and alternative packing
(`capacity_event_pricer.py:89–140`). Thus direct paths, charging paths, terminal
options and capacity-dual re-costing share the same sequence restriction.
`CapacityTerminalNetwork` already retains/re-costs capacitated alternatives;
the subclass must not replace its capacity algorithm or prune on one realized
window's cost. `fixed_sequence_index=True` by itself is only an indexing option,
not this restriction (`event_pricer_network.py:607–626`).

Two tempting shortcuts are unsafe:

- Restricting raw `ProblemData.adjacency` alone loses the previous-trip context
  through shared station→trip arcs (`event_pricer_network.py:252–273,480–499`).
- Restricting only `_add` leaves a seeding bypass. The master directly calls
  `net._source_candidates()` and builds direct terminal seed records
  (`run_capacity_terminal_cg.py:144–150`). Filtering that generator too prevents
  a suffix singleton from bypassing the fixed-duty graph. Prefix termination
  is excluded by the None-only-at-last rule. Do not post-filter a generated pool
  and call omitted duty routes complete.

With these first/next/last rules, every source-to-sink path is a whole assigned
duty. `partition=True` plus cap equal to the number of duties then forces one
complete path per duty, assuming a feasible selection exists. Assert the actual
returned trip sequences and coverage independently of that construction. There
must be no proper subsequence, skipped-trip route, early terminal shortcut or
cross-duty link. The new factory is still source-only until its exact
implementation and runtime interfaces are admitted; the old frontier's proof
scope is not transferred to it.

## Physical and accounting interface

`EventExpandedNetwork._record(actions)` builds records from the original
problem, calls `realize_expanded_path` and the injected-route validator, and
returns physical/cost metadata (`event_pricer_network.py:733–845`).
`run_terminal_energy_cg.audit_energy(net,record)` separately checks the expanded
terminal-energy mapping (`:61–74`). The capacity master uses an optional
`audit_column`/`column_occupancy` hook or its existing defaults (`:83–90`).

`realize_expanded_path(problem,record,*,g_kwh,charge_kw,reserve_kwh,soc_step,
block_min,arc_map=None,time_model='uniform')` returns realized record or None
plus classified detail (`expanded_path_realization.py:88–106`). Event mode
accepts irregular windows; it preserves trip/station/time choices and may reduce
kWh for conservative grid realization. Its mapping explicitly distinguishes
continuous and expanded-grid terminal SOC, and does not certify continuous-cost
pricing (`:459–503`). `realized_costs(record,mapping,*,station_prices)` preserves
that distinction (`:741–747`).

Keep grid master cost/charging records/terminal energy, continuously realized
cost/energy and physical validation separate. Plug occupancy uses the expanded
grid charging stops preferentially and conservative whole-minute ranges
(`capacity_event_pricer.py:43–59`), not a newly invented occupancy calculation
from continuous load. Validate selected-fleet shared occupancy in addition to
each individual route; one route replay alone is insufficient.

Import order is part of the remaining execution seam: runner modules set
`config.CHARGE_START_COST` at import, and cost modules capture it
(`run_capacity_terminal_cg.py:21–40`). Direct `run(...)` bypasses `main()`'s
captured-fee consistency check (`:460–463`). The existing caller boundary must
load the registered modules in a fresh paid process with prospective zero fee
and validate captured values. Do not mutate already imported globals after the
fact. Preserve sibling `BUS_COST_KX=1e5`; under an independently forced common
fleet it is a common surrogate, not EGG's vehicle100 calibration. No actual
import/order/backend behavior was tested here.
