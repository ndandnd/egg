# Bounded v2 source review

Reviewed the v2 protocol, pool builder, model, worker, Slurm wrapper, and focused tests for grouped selection leakage, weighting/preprocessing, stopping, outcome separation, ranking, and failure receipts. No model was fit, and no development/test outcomes or physical plans were opened.

The grouped design is coherent on source inspection: each base group and both source fleets stay together; the frozen 20-fit/4-inner/8-outer partitions are disjoint; preprocessing, prevalence, kind rates, and fleet weights use fit groups only; MLP and tree choices use whole inner groups; the MLP serializes its best inner checkpoint; and sklearn row-level tree early stopping is disabled. Outer prediction labels are used for retrospective scoring after the models and stopping choices are fixed. Ranking budget `k` is derived from input trip count, not held-out positives. The label remains observed source-incumbent movement selection, not edge feasibility or optimality.

The two launch-blocking issues found in the first pass are resolved in the final files:

1. `_metrics` now records fixed-0.5 positive and negative recall, class counts and weights, and null recall when a class is absent, alongside the separately defined input-trip-count top-k recall.
2. The worker now writes a minimal launch marker before source-identity collection, and the guarded path covers commit/hash collection. A synthetic commit-lookup failure test checks that typed failure and receipt artifacts are retained.

The implementation owner reports seven focused tests passing, plus `py_compile`, wrapper `bash -n`, and `git diff --check`. I inspected the changed metric and failure-receipt paths but did not rerun those checks. No model was fit and no development/test data or physical plans were opened. **Disposition: no remaining blocker in the reviewed scope.**
