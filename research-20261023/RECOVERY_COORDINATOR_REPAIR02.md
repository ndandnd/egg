# Prospective coordinator solver-free repair 02

23 October 2026. This is the reason and scope for the second, separately charged
solver-free check permitted by `RECOVERY_COORDINATOR_CHECK_PROTOCOL.md`. It does
not authorize a native backend call, numerical matrix, new qualification case,
training, cluster work, or sealed-data access. No check was run by the
implementation agent while preparing this repair.

## Preserved first attempt and diagnosis

`coordinator-checks/attempt01/attempt.json`, `stdout.log`, `result.json`, and
`source-snapshot` preserve the exact pre-repair inputs and outcome. The parent
archived all eight locked source files before this edit. Its pytest command was
`.venv-local/bin/python -m pytest -q src/tests/test_recovery_coordinator.py` with
`PYTHONPATH=src`. It completed with **22 passed and 12 failed**.

Every displayed failure is the same exact-arithmetic expectation defect: the test
asserted the string `119/2`, implicitly treating the market coefficient `.2` as the
decimal rational `1/5`. The fixture supplies a Python binary float. The existing
lift intentionally represents that stored float exactly with `Fraction(.2)`.
The independently handwritten expected bill is:

```python
Fraction(7) + 2*15 + Fraction(.2)*225/2
```

This equals `2143713422628356141/36028797018963968`, whose float value is `59.5`.
The formula uses the fixture's operations cost 7, linear tariff 2 and load 15,
and quadratic coefficient `.2` times squared load divided by 2. It does not call
the lift or coordinator to manufacture the expected value.

The complete twelve-case failure inventory is:

| Test | Failed cases |
| --- | ---: |
| `test_admitted_fallback_survives_every_later_failure` | 7: exception, start_rejected, start_unknown, timeout, no_incumbent, bad_replay, infeasible |
| `test_only_unrestricted_guarded_mip_lower_survives` | 1 |
| `test_fallback_objective_not_overwritten_by_later_solver_objective` | 1 |
| `test_more_expensive_full_witness_does_not_replace_prefix_bill` | 1 |
| `test_prefix_save_just_past_15_retains_witness_and_stops_full` | 1 |
| `test_slow_full_bound_replay_cannot_import_late_lower` | 1 |

The seven parameter cases first fail at the retained fallback bill assertion;
the five other cases first fail at selected-bill equality. Assertions following
those failures were not reached and must be established by the repaired check.
No other failure cause is shown in the preserved first-attempt log.

## Repair and check scope

Replace all seven assertion sites using `119/2` with exact string comparison
against the shared handwritten rational expression above. Preserve all remaining
assertions and cases. No approximate comparison, altered tariff, production
arithmetic change, widened tolerance, solver rerun or extra case is part of this
repair. Update `RECOVERY_COORDINATOR_IMPLEMENTATION.md` with the real first-check
outcome and the stored-float semantics. The coordinator and frozen native/lift
sources remain unchanged by the implementation agent.

The parent must freeze the repaired sources before `attempt02` and use its
resource-supervised solver-free check launcher. The source-hashed attempt records
the final exact command and any parent-owned launcher hardening. This prospective
reason claims neither a passing repaired outcome nor native qualification.

## Carried charge and stop rule

First-check allocation charge: **0.7734692078083754 seconds**. Its additional
supervisor CPU charge: **0.01885300000000001 seconds**. Preserve the current total
**87.67245720780838 seconds**, comprising phase-0 66.880135 seconds, the package's
20-second administrative allowance, and the first check's two charges.

Attempt02 gets the protocol's second 30-second solver-free allocation and its
actual/conservative process-tree plus supervisor charge. The original 900-second
ceiling, 720-second dispatch stop and shutdown reserve continue to apply. There
is no automatic third check: any further repair requires a new stated reason and
budget before dispatch. Neither unused allocation nor a passing solver-free
result authorizes the deferred native matrix.
