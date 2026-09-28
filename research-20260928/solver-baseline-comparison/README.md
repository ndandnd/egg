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

Execution source `f4b342dc85799d01d9313baeaf8c9ec527759d59` passed full CI
36408897677 on attempt 2. The first attempt stopped before tests because an
unchanged plotting dependency was unavailable; the successful retry and original
failure are recorded in [CI_RECEIPT.md](CI_RECEIPT.md).

Job **575215** was submitted once at 10:25 UTC on 28 September and observed
**PENDING (Priority)**. The [submission receipt](../cluster/solver-baseline-comparison-575215.json)
records the source, request and exclusive attempt. Execution checkout:
`/home/nc437/egg-solver-baseline-comparison-20260928`; output:
`result/solver_baseline_comparison/20260928-attempt1`.
No scientific outcomes have been read. Allocation and runtime freeze remain
unconfirmed until the pending job starts.

Completed attempts remain unchanged. A later report will show every outcome
alongside bounds and paid time, and use a common-quality speed claim only when
supported by the recorded on-time evidence.
