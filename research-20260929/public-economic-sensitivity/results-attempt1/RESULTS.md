# Eight-cell public economic sensitivity: unresolved native gap

All 24 declared stages of job `600028` returned on time with complete admitted
stage evidence. Each of the eight physical planners ended **bounded**, and
each cold QP hull ended **budget_exhausted** when its 10-second pricing reserve
prevented another request. Three fixed-price responses certified; five ended
bounded. The sealed manifest, source and receipt gates pass. These are two
depot variants of one public 37-service timetable under four synthetic
economic settings, not eight independent timetables.

| Depot | Fee | Curvature | Native (D) | Native (CH) | Native (D-CH) | Own-incumbent regret |
| --- | ---: | ---: | --- | --- | --- | --- |
| 15 | 100 | 1 | [408.53, 514.53] | [408.53, 446.16] | [0, 105.993177] | [211.986348, 211.986351] |
| 16 | 100 | 1 | [423.15, 530.66] | [423.15, 494.65] | [0, 107.503778] | [204.416594, 232.212972] |
| 15 | 40 | 1 | [288.53, 424.07] | [288.53, 329.59] | [0, 135.533104] | [271.066201, 271.066204] |
| 16 | 40 | 1 | [303.15, 440.69] | [303.15, 388.62] | [0, 137.533928] | [273.237556, 275.451216] |
| 15 | 20 | 1 | [248.53, 366.86] | [248.53, 305.34] | [0, 118.325912] | [236.651818, 245.183330] |
| 16 | 20 | 1 | [263.15, 377.24] | [263.15, 315.74] | [0, 114.076183] | [226.322066, 238.840416] |
| 15 | 40 | 2 | [288.53, 570.13] | [288.53, 396.98] | [0, 281.590006] | [563.180006, 563.180009] |
| 16 | 40 | 2 | [303.15, 568.15] | [303.15, 411.37] | [0, 264.989717] | [516.884900, 536.251507] |

Displayed lower endpoints are rounded down and upper endpoints up; the
[compact JSON](compactrows.json), [CSV](compactrows.csv) and
[full eight-row table](TABLE.md) preserve the tighter outward values, exact
endpoint hashes, all 24 statuses, paid times and source controls. Every
native gap interval contains zero. Their upper widths range from about 106
to 282 cost units, so this run establishes neither a positive public gap nor
its absence. The physically replayed planner incumbents and own-price
responses each use two buses. The 24 whole-fleet hull columns also use two;
none of these observations identifies the optimal fleet count or a
two-to-three-bus crossover.

The large regret intervals apply to **named bounded planner incumbents**.
Planner uncertainty alone is 106–282 units. Regret can include incumbent
suboptimality as well as a physical-versus-hull gap and a price-dual term; it
is not evidence that an optimal public dispatch lacks price support. The
separately reported analytical availability/cardinality floors, roughly
256–441 across these settings, are exact lower bounds for the ideal
stored-input model. They are never substituted into the native enclosures or
the fixed-price responses. No ideal-model upper witness was newly certified,
so the curator leaves mixed ideal-gap bounds null.

The original depot-15 f=100 exact ideal witness gives a separate previously
reviewed upper bound 512.769426, stronger than this run's native planner
upper 514.526312. The f=100 sensitivity case changes only the case name and
retains its physical and economic inputs; the two numbers still have
different exact-ideal versus native-tolerance provenance and are not merged
in this table. The saved hull pool contains a replayed whole-fleet column at
native cost about 504.643749 for that cell. The separate
[pool replay](pool_candidates.json) admits it as a tolerance-qualified native
upper of 504.643750 after the native objective guard; two other cells also
obtain better native uppers. Their original stage enclosures remain in the
table above; the post hoc caps are in [DIAGNOSIS.md](DIAGNOSIS.md). A convex
hull **mixture** is not a physical fleet, and its cheaper upper cost cannot
be used as a physical upper witness.

Planner children consumed 1469.95 s, hull children 1402.01 s and response
children 357.64 s. These sum to 3229.61 s of serial paid child time; the
supervisor reports 3233.90 s and wrapper 3247 s including their different
boundaries and setup. Slurm elapsed was 54 min 9 s. No speedup or ML claim
follows. The specific stop and component diagnosis is in [DIAGNOSIS.md](DIAGNOSIS.md).
