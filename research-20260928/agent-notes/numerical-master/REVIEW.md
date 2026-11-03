# Focused review: numerical restricted-master proposal

**Verdict: PASS for the scoped opt-in implementation and pure tests.** No native optimizer or experiment was run for this review. The default `native_lp` identity and result/count keys remain unchanged; the QP policy and its denominator/iteration limits are included in the opt-in state identity and forwarded by the compact-pricing wrapper.

The SLSQP result is treated only as a proposal. The implementation checks the returned exact weights and fixed-denominator units, replays the complete-fleet columns, reconstructs the mixture with rational arithmetic, and recomputes the restricted-pool Fenchel residual. A non-success SciPy flag is retained but does not by itself reject a finite replayable proposal. The normal fresh global pricing step still follows each accepted proposal; only its global enclosure against the replayed feasible upper can certify. The proposal path bypasses native LP/pairwise polishing without a hidden fallback. Proposal failures, import failures, and late returns preserve earlier replayed mixture/lower evidence with a noncertifying status; bit and deadline limits remain budget failures. Cache freshness gates remain intact, and final assembly rejects a negative exact enclosure width in QP mode even when no cache is enabled.

The previous concrete review findings are closed: physical replay errors are no longer relabeled as proposal failures, and lazy SciPy import errors produce a typed `proposal_failed` result. Focused regressions cover both, malformed simplex retention, non-success proposals, late return, exact-bit limits, cache interaction, and default identity. Sol reports 37 focused numerical-master/cache/reuse tests passing plus `py_compile` and `git diff --check`; I did not rerun them.

One cosmetic exception-message issue remains nonblocking: the final negative-width guard says “Cached physical bound reverses…” although it also guards the QP policy with cache disabled. The behavior is correct; a generic message would describe both cases.

Reviewed hashes:

- `src/egglab/native_hull.py`: `949de1551b4b6515860fdee7f63fd197c713c4645a7b20315802dd56712ada94`
- `src/egglab/native_pathflow_hull.py`: `928676e25a6473d9c9874aed433db8434953f54b5c7a3ba3f84d596f717c4759`
- `src/egglab/restricted_qp_proposal.py`: `466edb75dbd619feae37f423967cdd1068ec33abdcc70207fa01a006ba7b53dd`
- `src/tests/test_native_hull_numerical_master.py`: `e044d5ac4ae277ff66b72c988458da131bf4e7fdd332e92e09c80f30001f6b1c`
