# No-plan pricing repair review

**Verdict: the repair meets the stated contract.** The compact adapter accepts only an `unresolved` result with no `plan`, after checking top-level formulation and extraction policy. Any present plan is validated; `certified` and `bounded` without a witness, and other missing-witness statuses, are rejected. The shared coordinator additionally checks the unresolved result’s case and prices, emits it as `pricing_unresolved`, and stops through a dedicated control path.

That path runs before physical column replay, bound admission, cache-evidence creation, or incrementing `fresh_pricing_successes`. It preserves previously checked bounds, mixtures and columns, and finishes `stalled_bounded` only when both a lower certificate and feasible mixture exist; otherwise it returns `unresolved` without inventing bounds. Since it exits before certification logic, a no-plan result cannot certify from a cached lower alone. Present invalid witnesses and proposal/physical validation failures remain errors.

The separate `pricing_unresolved` event keeps the successful `pricing_result` contract intact. The qualification reader now recognizes it, and the bounded-prefix regression confirms the strict cache audit still pairs every successful pricing result with its bound and evidence when an unresolved tail follows. The finite decoy native lower bound in the no-plan tests is preserved in the unresolved event but never becomes a new Fenchel certificate.

Sol reports 156 focused tests passed in 0.87 seconds across these seven modules: `test_native_pathflow_hull.py`, `test_native_pathflow_hull_policy.py`, `test_native_hull.py`, `test_native_hull_pricing_cache.py`, `test_native_hull_feasible_reuse.py`, `test_native_hull_numerical_master.py`, and `test_solver_baseline_comparison.py`. I reviewed the focused cases and final implementation; I did not rerun the suite or any native solver. The tests cover first-call and late no-plan outcomes, finite lower-bound decoys, preservation of prior evidence, cache-only non-certification, success without a witness, malformed present witnesses, qualification event parsing, and bounded-prefix cache admission.

The review does not reinterpret or alter the three historical comparison failures. The Google Doc update source accurately describes the repair, preserved evidence, tests and limitations; its `LINKS_PENDING` marker is expected until publication. It makes no speedup or optimality claim.

## Final file pins

| File | SHA-256 |
| --- | --- |
| `src/egglab/native_pathflow_hull.py` | `93177e6e712ae4c407a26202194c250a7c547801b0ee6a18ebcf5e49c90a2eb4` |
| `src/egglab/native_hull.py` | `dc8f04bfeab01fb6aaa4afca61c97887993b4e6181be8cabfa76858265051ffd` |
| `src/experiments/native_hull_qualification.py` | `ce2365885483e1adcf50e8da735dfc1abf0a9df04e83f193121a19dd24029a28` |
| `src/tests/test_native_pathflow_hull.py` | `b640e0f0d84333c5094730672b6c167089dc86cc3726d0afc01e07e47155e1ec` |
| `research-20260928/agent-notes/no-plan-repair/IMPLEMENTATION.md` | `a3d80be122424b561f1dcbabd2346ab49ef84447cc0ae4e9046b5e140a70a200` |
| `research-20260928/no-plan-repair/GOOGLE_DOC_UPDATE.md` | `bd213cf8bc1d13f7673d3f12d139dfdb95c18e096e8d278512313c9505edf89a` |
