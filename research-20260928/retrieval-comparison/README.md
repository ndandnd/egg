# Bounded whole-fleet retrieval comparison

This development experiment compares cold iterative solving with all retained
fleet columns, nearest-source-price retrieval, and exact cheapest-current-bill
selection from the same admitted pool. Direct proposal quality and feasibility
are reported separately from the cost of obtaining fresh global bounds.

The fixed sample contains five new full-replenishment synthetic cases (8, 16
and 24 services across three development seed groups) and the 105-service
Eberbach timetable. No reserved train/test groups are opened. Each case pays for
two source-market solves. All target methods use the same nonlinear market and
verification settings, with no inherited lower-bound cache or native MIP start.
The protocol also includes a target physical planner and its own-price response.

[Prospective protocol](../../doc/RETRIEVAL_COMPARISON_PROTOCOL_20260928.md).

The five synthetic cases pass physical replay and three focused pure tests.
The service-only grid-energy lower bound implies approximately 33.59–234.34 kWh of unavoidable charging
outside a four-hour cheap window in the 16/24-service cases. The 8-service
witness fits within that window and remains in the fixed sample. These are
model-derived input properties, not optimized fleet counts or costs.
[Generator and input table](GENERATOR.md). Runner implementation and independent
[review](REVIEW.md) are complete: eight focused pure tests, Python compilation
and shell syntax checks pass. No optimization outcome is claimed by this package. All attempted work, failed
sources and unavailable comparisons will be preserved. The single serial
attempt has a two-hour ceiling, one CPU and 8 GB, with no retry or requeue.
After its result review, the evidence is consolidated into the LaTeX draft;
ML training is optional for that first draft.
