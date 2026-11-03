# Compact pricing no-plan repair

`native_pathflow.solve_pricing` can return `status="unresolved"` after a native
`NO_SOLUTION_FOUND` result without an incumbent or `plan`. The compact wrapper
now accepts that exact missing-plan outcome after checking top-level provenance.
A present plan still needs the compact formulation and extraction-policy tags;
`bounded` and `certified` results still require a plan.

The shared hull coordinator records a valid no-plan response as a
`pricing_unresolved` event with its full result and stats, then stops without
adding a column, global lower certificate, or physical-pricing cache evidence.
The qualification event reader admits this event. If the coordinator already
has a verified lower certificate and feasible mixture, the returned status is
`stalled_bounded` with both bounds
intact. An unresolved seed has status `unresolved` and no invented bounds.
Neither path certifies the state; cached lower evidence alone cannot satisfy
the fresh target-pricing requirement.

The ordered solver comparison accepts a `stalled_bounded` predecessor only
when its bounds and physical columns replay. Its opt-in cache event audit
still requires every `pricing_result` to have a matching `global_bound`; the
distinct unresolved event preserves that strict contract. A pure regression
checks admission of a bounded prefix followed by an unresolved tail. This
repair does not reinterpret the three historical failed comparison cells.

Pure focused validation passed 156 tests in 0.87 seconds:

```sh
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m pytest -q \
  src/tests/test_native_pathflow_hull.py \
  src/tests/test_native_pathflow_hull_policy.py \
  src/tests/test_native_hull.py \
  src/tests/test_native_hull_pricing_cache.py \
  src/tests/test_native_hull_feasible_reuse.py \
  src/tests/test_native_hull_numerical_master.py \
  src/tests/test_solver_baseline_comparison.py
```

Tests exercise first-call and late no-plan returns, a finite decoy solver
lower bound without a new certificate, cache-only evidence without fresh
certification, malformed present witnesses, and claimed success without a
witness. No native optimization sweep was run.
