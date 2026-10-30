# Interpretation review — necessary preterminal capacity cuts

Reviewed only this package's `stdout.txt`, selected fields of
`attempt01/receipt.json`, `PROTOCOL.md` and `REVIEW.md`. No old readout, original
data, cases, plans, source modules, replay, solver or numerical recalculation was
accessed or performed. The parent reports the once-only process closed exit 0
at 0.04 CPU/0.07 wall seconds. The receipt itself correctly keeps its
prepublication resource observation distinct from external total acceptance.

## Denominators and scope

All eight original-reference projections are available. Exactly three violate
at least one ideal necessary cut: the 45-kW references for 10006, 10009 and
10005. All other reference records have no detected violation. Of 16 planned
adaptive records, 12 have available retained-topology diagnostics and none
violates these cuts. Four 45-kW adaptive records for 10009/10005 remain
unavailable, with null cut results. They are not passing observations or
substituted prior topologies. Accepted unchanged routes remain explicitly
unchanged; available adaptive does not mean newly discovered topology.

The 24 records are grouped resource/tariff/role descriptions of four exposed
development groups, not 24 independent tests. These counts introduce neither
an available-only performance estimate nor a new scientific success gate.

## What the cut components say

The test compares each bus's minimum early grid energy needed to retain reserve
at its final return (`ell`) with its own selected preterminal windows. It also
compares the shared union capacity with the greater of summed bus requirements,
total-energy-minus-terminal-capacity, and zero. Overlapping bus windows are
unioned, not added as independent shared capacity. Thus aggregate energy and
individual battery timing can impose different restrictions.

| Reference at 45 kW | Shared union capacity | Controlling shared requirement | Reported shared margin, approximately |
|---|---:|---|---:|
| 10006 | 72 kWh | Sum of bus early requirements | −58.4333 kWh |
| 10009 | 1023/4 kWh | Sum of bus early requirements | −222.8389 kWh |
| 10005 | 357/4 kWh | Total energy shortfall after terminal capacity | −262.1944 kWh |

The approximate margins above are the parent-supplied readout; the receipt
preserves exact represented rational values. No new conversion or arithmetic
was performed for this review.

For **10006**, the reference has only a 96-minute shared preterminal union.
Its 72-kWh capacity exceeds the terminal-energy shortfall alone, but cannot
supply the summed bus reserve deficits; one bus also fails its individual cut.
Consequently, simply observing adequate aggregate daytime-plus-terminal energy
would miss the binding necessary restriction. The admitted changed adaptive
paths at 45 kW have a 194-minute shared union and capacity 291/2 kWh. All their
per-bus cuts pass, their controlling shared requirement remains the summed bus
deficits, and the shared margin is approximately **+14.5111 kWh under both
tariffs**. These records identify a concrete route-dependent charging-access
mechanism rather than an explanation based solely on a terminal recharge total.
The cuts alone do not prove that access is the unique cause of the change.

For **10009**, every reference bus fails its individual 45-kW early-energy cut.
The shared capacity also falls below both the summed bus deficits and the
terminal-energy shortfall; summed deficits impose the stronger requirement.
For **10005**, the first two bus cuts fail, while the third passes. Here the
terminal shortfall is the stronger shared condition, and even the weaker summed
deficit exceeds the shared preterminal capacity. This is a genuine difference
in the diagnostic explanation, not one common aggregate-energy story for all
three references.

The 10001 reference has zero early requirement and zero preterminal selected
capacity at both levels, so its zero margin is a passing necessary condition,
not evidence of a strict reserve of preterminal flexibility. Nonnegative
margins elsewhere likewise do not measure economic value or feasible-set size.

## What is established, and what must be conceded

Under the explicitly inherited ideal assumptions and exact represented
quantities, the three negative reference margins rule out a charging allocation
within their selected topology satisfying these necessary conditions. This is
stronger than rejection of one old timed charging schedule. It remains
conditional on the exported windows, battery/efficiency reconstruction,
common-opening assumptions and ideal divisible charging model; it is not a
tolerance-qualified floating native certificate or a new independent physical
admission. No epsilon was used to relabel a violation as physical infeasibility.

For 10006, the admitted changed topology passes the ideal cuts whereas its
reference violates them. Its operational feasibility comes from the previously
admitted witness recorded in context, not from passing this diagnostic. The
contrast supports a specific necessary-capacity account of why topology can
matter under restricted grid power. Passing does not settle earlier SOC
prefixes, battery headroom, allocation conflicts among subsets of buses, or
feasibility of another route. No accepted available endpoint violates the cuts,
but consistency on these exposed examples is not a universal validity test.

Reference cuts do not restrict the whole movement graph: alternative routes
can change consumption, bus deficits and charging windows. The four missing
adaptive diagnostics therefore remain missing, and their earlier full-graph
`INF_OR_UNBD` statuses remain unresolved. Neither these cuts nor a missing
incumbent proves global fixed-N infeasibility, unboundedness, route optimality
or absence of routing value. These classical necessary inequalities are not
ML novelty, learned-information causality or a price-value certificate.

## Scientific decision

The useful finding is now a **classical feasibility mechanism**: the examined
reference routes can lack enough appropriately timed shared charging capacity,
and a conventional routing witness can remove that necessary obstruction at the
same fleet count. A larger automatic search, cap scan or all-79 expansion is
not needed to restate this example. The unresolved full-graph cases should stay
unresolved unless a future scientific decision specifically requires resolving
them.

The next justified design step is source-only: formulate how these valid
necessary capacity checks could serve a competent conventional routing
constructor or pruning rule, and identify which omitted SOC/subset constraints
prevent sufficiency. Any later economic test must additionally begin from a
strong target-charged common incumbent with all acquisition, routing and charging
work paid inside a fresh prospective budget. The earlier bounded classical
cost composition is not yet that strong comparator; this diagnostic does not
repair its cost outcomes or manufacture the missing resource interactions.

Only after that question and comparator are defined would a separately reviewed
bounded experiment be justified. No new plan access, solver disambiguation,
automatic retry, capacity tuning, model refit, cohort expansion or reopening of
raw data is authorized by this interpretation. The existing learned-model
stopping decisions and past economic points remain unchanged.
