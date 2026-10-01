## Public bus-cost and curvature study launched — 29 September 2026

Unicorn job 600028 is running the declared eight-case public sensitivity study: depot 15 and depot 16, each at bus cost and curvature multiplier (100,1), (40,1), (20,1) and (40,2). The linear intercept remains 0.20 and the base quadratic coefficient is 1/900. The original nonlinear scenario is retained as a control.

Every case receives fresh physical planning, a cold whole-fleet hull calculation, and an eligible own-price response tied to its returned planner schedule. Changing the bus fee changes the objective identity; no old objective value or native bound is imported. Analytical availability/cardinality bounds are reported separately. All declared outcomes, incomplete stages and spent time will be retained.

The implementation passed four focused tests and an independent source review. The job uses one CPU, 8 GB and one native thread, with a 100-minute ceiling and no retry or requeue. The queue check confirmed it running and its eight-case, 24-stage design frozen. Full hosted CI was still in progress when submitted.

Both depots are variants of one public timetable, not independent networks. No new economic conclusion is available yet. The next step is to review all cost, hull and incumbent-regret intervals together before expanding the study or starting machine learning.

[Prospective design](https://github.com/ndandnd/egg/blob/codex/journal-research-20260927/research-20260929/public-economic-sensitivity/DESIGN.md) · [Independent launch review](https://github.com/ndandnd/egg/blob/codex/journal-research-20260927/research-20260929/public-economic-sensitivity/REVIEW.md)
