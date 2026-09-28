# Ordered comparison of reusable solver work

This development experiment compares four methods in order: reserve-cold hull
solving, retained feasible fleet plans, a numerical restricted master with
retained plans, and that method with checked physical pricing-bound reuse.
There are four physical cases and two markets, for 32 declared calculations.
The two public depot variants share one timetable; no held-out evaluation or
learning claim belongs to this screen.

The numerical master addresses the earlier rational-polishing stop. The bound
cache addresses the loss of useful lower bounds after market changes. Both are
implemented and reviewed; their online benefit has not yet been measured.
Every arm pays its own initial solve. Source validation, failed runs and all
work already spent remain part of the accounting.

The [prospective protocol](../../doc/SOLVER_BASELINE_COMPARISON_PROTOCOL_20260928.md)
fixes cases, order, admission rules, budgets and interpretation. Native targets
sum to 64 minutes; individual hard child deadlines sum to 80 minutes. The
controller cap is 90 minutes, the outer wrapper cap 100 minutes, and the Slurm
ceiling two hours, in one serial job requesting one CPU and 8GB. Actual
allocation and all overshoot are recorded.

Runtime preflight on 28 September confirmed the existing cluster environment:
Python 3.12.13, NumPy 1.26.4, SciPy 1.13.1, python-mip 1.17.6 and gurobipy 12.0.3,
with Gurobi selected. No optimization or environment modification occurred in
that preflight. The job's frozen environment record remains the execution
source of truth.

The runner's 12 focused pure tests passed, including own-source admission,
cache-event matching, failed-source handling, complete paid totals and partial
termination accounting. Shell syntax checks passed. Independent review is
recorded at `../agent-notes/solver-baseline-comparison/REVIEW.md`.

The comparison is prospective. Runner review, CI, committed source and an
exclusive submission receipt must precede any result claim. Completed attempts
remain unchanged. A later report will show every outcome alongside bounds and
paid time, and use a common-quality speed claim only when supported by the
recorded on-time evidence.
