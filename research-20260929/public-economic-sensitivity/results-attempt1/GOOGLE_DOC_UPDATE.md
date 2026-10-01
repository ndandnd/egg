# Public sensitivity results and solver bottleneck — 29 September 2026

The eight-case public bus-fee/curvature study completed in 54 min 9 s on one
CPU, with all 24 declared stages returned on time. Every physical-versus-hull
cost-gap interval includes zero. Their upper endpoints range from about 106
to 282 cost units, so the study neither establishes a positive public gap nor
shows that the gap is absent. These are economic/depot variants of one public
37-service timetable, not eight independent networks.

The large own-price regrets, about 204–563 units, belong to the schedules
returned by bounded planner solves. Those schedules are not certified optimal.
Their regret cannot answer whether an optimal public dispatch lacks price
support. All incomplete outcomes and paid time are retained alongside the
separate exact analytical floors. No ideal-model upper witness is newly
certified.

The planner bottleneck is expensive native MIP rounds. Recorded native solver
time accounts for about 96% of planner child time. Across all eight
hull solves, the charging-master proposal and replay counters total only
9.48 s; none stopped on its arithmetic or master-call limit. Increasing those
limits would miss the observed bottleneck; the remaining hull time includes
global route pricing, model construction and other work not timed separately.
Three saved individual fleet plans
offer modest physical-upper improvements without new optimization. They are
not hull mixtures and do not inherit the original planner's regret measurement.

The next useful target is to check whether a proved cardinality/energy
inequality adds anything beyond the existing aggregate energy-balance rows,
before considering a bounded native-solver experiment. A larger parameter
sweep and ML training are premature while these certificates remain wide.
No new cluster job is submitted. With this result package complete and no
concrete next launch under implementation, scheduled checks are paused under
the latest operating preference.

The reviewed result table, figure and diagnosis are saved separately from the
readable v0.8 manuscript, which predates this experiment. Historical document
entries and manuscript versions remain available.

- [Complete result table](https://github.com/ndandnd/egg/blob/codex/journal-research-20260927/research-20260929/public-economic-sensitivity/results-attempt1/TABLE.md)
- [Interval figure](https://github.com/ndandnd/egg/blob/codex/journal-research-20260927/research-20260929/public-economic-sensitivity/results-attempt1/public_economic_intervals.png)
- [Solver diagnosis](https://github.com/ndandnd/egg/blob/codex/journal-research-20260927/research-20260929/public-economic-sensitivity/results-attempt1/DIAGNOSIS.md)
