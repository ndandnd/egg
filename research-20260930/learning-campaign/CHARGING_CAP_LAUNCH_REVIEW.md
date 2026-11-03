# Charging-cap pilot launch review

The completed energy-aware attempt returned four optimal relaxed covers but no
physically chargeable fleet. Independent arithmetic identifies insufficient
individual charging windows in 12 of 14 selected routes, before shared charging
competition. This justifies one new four-cell development pilot with per-visit
charge-energy caps and terminal refill limits. It does not establish that every
fleet at those bus counts is infeasible.

Root reviewed the conditional SOC inequalities, terminal refill bound, shared
profile orchestration, failure/fallback handling and prospective resource budget.
GPT-6 Sol implemented and checked the cover and harness; Luna reviewed result
reporting. The aggregate affected suite passed 33 tests and 4 subtests. Wrapper
syntax, deterministic charging diagnosis, frozen design and 39 unique source
pins, and diff checks passed. Small local HiGHS fixtures and archived physical
SOC witnesses were used; no local GRB fleet optimization was performed.

The new constraints are necessary, not sufficient: they ignore competition
between buses. Native fixed-route charging and independent replay remain the
feasibility gates. Any failed repair retains its evidence and timing and replays
the archived fallback without another redundant hull solve. New feasible repairs
receive a fresh bounded hull check. No refit, reserved test access, retry, second
cover or added-bus repair is authorized by this protocol.

Execution is limited to one serial job requesting one CPU, 8 GB, 30 minutes,
one native thread, no requeue, excluding scaglione-compute-01. The launch helper
requires a reviewed commit, no active EGG job, and a fresh execution checkout.
Root found no launch blocker. The exact execution commit and job ID will be
recorded in the separate launch receipt after submission.
