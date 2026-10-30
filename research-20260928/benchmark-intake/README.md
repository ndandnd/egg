# Independent timetable benchmark intake

This package adds the next development input and declares future evaluation
boundaries before learning. It does not contain an optimization comparison.
Eberbach's 105-service base is independent of the existing Hildenbrand source
operator; its actual model size and feasibility checks are recorded separately.
The two Hildenbrand depots remain variants of one base, not two public networks.

The pure Eberbach preflight found 105 services, 14 stops and 196 directed
source travel arcs. Its derived graph has 10,359 movement choices. A conservative
one-service-per-bus schedule physically replays with full replenishment before
20:00, within the declared 30:00 horizon. Its 105 buses establish feasibility
only; this is not a minimum-fleet or optimized cost result. The largest modeled
service energy is 35.37 kWh, below the declared 400 kWh usable battery.

The pre-solve compact-formulation estimate is 291,637 variables and about 312,316
constraints over 186 resource intervals. No native solver model was allocated.
This is a size estimate, not a memory or runtime guarantee. The first bounded
solve must account for model construction within its complete-call limit.
The adapter passed 11 focused intake/regression tests. Regenerating the existing
Hildenbrand input produced identical bytes. See the [intake note](EBERBACH_INTAKE.md)
and [preflight receipt](EBERBACH_PREFLIGHT.json); final independent review is
recorded in the [adapter review](EBERBACH_ADAPTER_REVIEW.md).

The source timetable and directed travel fields remain separate from EGG energy,
charger and terminal-inventory assumptions. Source-study deadhead inputs include
estimates, so they should not be described as measured operator telemetry.
[Source interpretation](SOURCE_CONTEXT.md).

The metadata-only reservation contains 20 public base groups: 10 prospective
training, 4 development and 6 test groups. Hildenbrand and Eberbach are fixed
development. All variants of one base inherit its split. Exact duplicate
fingerprints are grouped; byte differences do not establish semantic independence.
Any test group later found to overlap an exposed base loses its clean-test status.
The [reservation](GROUPED_RESERVATION.json) and [grouping design](GROUPED_DESIGN.md)
record the deterministic rule. These are reservations, not a commitment to adapt
or solve every large network. The [synthetic design](SYNTHETIC_SCALING_DESIGN.md)
uses full terminal replenishment and grouped seeds; no new synthetic instances
have yet been generated or solved.

This prepares the remaining computational evidence for the expanded first draft.
[The completion plan](../../doc/DRAFT_COMPLETION_PLAN_20260928.md) limits the next
work to a bounded cold/reuse/retrieval comparison followed by consolidation into
LaTeX. A learned model is optional, and unfavorable or unresolved experiments do
not delay writing indefinitely. All existing cases remain development data.

For price-only changes with an unchanged physical instance, every checked stored
fleet remains feasible and its current bill can be evaluated directly. The
nearest-neighbor comparison must therefore include the cheapest current bill
over the same stored pool as a strong simple baseline. A nearest-price lookup
alone is not sufficient evidence for learning. Transferring routes to a different
timetable requires explicit trip correspondence and physical repair.
