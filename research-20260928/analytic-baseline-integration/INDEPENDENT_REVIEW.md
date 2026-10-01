# Independent review: reporting-only analytic baseline

**Disposition: no remaining blocker in the reviewed implementation.** Scope was limited to `analytic_energy_floor.py`, the new opt-in reporter diff, and the focused test file; I did not run tests or a solver.

The baseline binds each full physical payload to its reviewed identity and pinned flow/one-bus evidence. It checks the stored physical assumptions, common positive curvature, supported uniform-price interior condition, and positive three-plus-bus margin before returning an exact rational ideal CH lower bound. It does not produce a native bound or reuse a native lower bound.

The reporter keeps the baseline in a separate opt-in appendix. Unsupported synthetic cases are marked unavailable; mixed intervals require established supervisor integrity, complete on-time evidence with an allowlisted outcome, and compatible planner/hull uppers. The implementation rejects malformed direct Boolean endpoints, inverted or conflicting intervals—including a hull lower above `min(CH upper, D upper)`—and an upper below the ideal floor. It preserves native rows and labels the combination conditional on native upper witnesses being feasible for the ideal model. Decimal displays round outward. The focused tests cover the requested fail-closed cases and native-row preservation; Sol reports 10 tests passing and a byte-identical curated smoke report.

One inherited parsing limitation remains outside this opt-in change: the reporter's existing `bounds()` converts JSON booleans through `Fraction`, so a Boolean can lose its type before reaching the new helper. The direct helper rejects Boolean endpoints; for this pinned public catalog, a Boolean upper also fails the ideal-floor check, while native lower endpoints are not transferred. I recommend addressing that at ingestion only if the legacy report's parsing behavior is separately revised.

Reviewed-file SHA-256:

- `src/egglab/analytic_energy_floor.py`: `04c3a63162abac93164291db462e1f4148eb9ff4fb72942d631db53b648cf8e4`
- `src/experiments/computational_benchmark_report.py`: `1c488d865d31562982f5ad55d9e8ee05daf001c68076bcdda3b4fdb1c3ad4444`
- `src/tests/test_analytic_energy_floor.py`: `24082fb3a4b98a8af065a4a2a2750733ca5c5e0e86df5ec15107f22d91f22a7c`
