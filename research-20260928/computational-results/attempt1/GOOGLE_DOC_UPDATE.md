First computational screen — findings and next experiment (28 September 2026)

The first computational screen completed in 35 minutes 57 seconds on one CPU. It covered eight case–market combinations and accounted for all 32 stages: 10 reached their numerical certification target, 10 returned bounded results, nine stopped at algorithm budgets, and three reuse stages were ineligible. All 29 launched stages returned within their hard deadlines. The two public depot variants share one underlying Hildenbrand timetable.

The cyclic example reproduced the expected price-support failure. Reusing its initial pool reduced the next market's pricing calls from three to one. This is a small development example; it is not evidence of public-data scalability or a learning advantage. Public planner and hull bounds remain wide, and the current experiment does not resolve their gap.

The public hull runs spent about 173 of 184 seconds in native pricing solves, with only about five milliseconds polishing mixtures. The last pricing solve returned a second fleet plan, but left no time to combine the two plans. A separate closed-form calculation using those saved plans reduced this run's convex-hull upper bounds by about 37–69 cost units. Physical-column and mixture replay took roughly a tenth of a second per case, excluding imports, case construction and report writing. This postprocessing is additional work, not part of the original run's timing, and a convex mixture is not one executable fleet schedule. It does not supersede stronger compatible historical bounds or establish global optimality.

The next experiment will reserve time to process returned plans and test a separate reuse mode that accepts physically verified pools even when the preceding solve has an open optimality gap. It must recompute target-market weights, prices and global bounds, count preparation and checking time, and preserve the original certified-predecessor comparison. The shifted three-service example hit a separate rational-arithmetic limit; the numerical mixture proposal remains relevant there. Retrieval baselines and these solver improvements come before learned route proposals.

The result tables, two diagnostic figures and a compact package of replayable scientific evidence are backed up with the research code. No ML advantage or public reuse speedup is claimed. Hourly research follow-ups continue.

Tables, figures and scientific evidence: https://github.com/ndandnd/egg/blob/967f603059467fdf3af25ef61634f9253e9a7c5b/research-20260928/computational-results/attempt1/README.md
