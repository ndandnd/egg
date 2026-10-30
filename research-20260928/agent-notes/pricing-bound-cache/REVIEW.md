# Focused review: physical pricing-bound cache

**Verdict: PASS for the scoped core change and pure tests; no native solve or qualification was run.** The cache remains opt-in. With it enabled, each imported physical pricing lower is re-admitted from the saved native incumbent/lower-bound record, its stored objective is checked against the saved plan cost and load at the exact saved price vector, and the target market's Fenchel conjugate is recomputed from its own stored coefficients. The cached price is retained as provenance for that conversion, not represented as a target-state price.

The target certification branch still requires a successful fresh target-state pricing solve, the usual replayed target mixture, and the epsilon enclosure. Cache-only budget exhaustion therefore remains bounded. Final assembly now rejects any negative exact target width even if no fresh pricing request was completed; the focused no-fresh-call reversed-enclosure fixture covers this case. Source case/state, oracle, extraction policy, per-record digest, call index, objective, status, native bound, and source work-cost fields are checked. The compact wrapper forwards the opt-in arguments, while the default identity/output path remains unchanged.

I found no remaining mathematical or admission blocker in the reviewed scope. Invalid explicit cache input propagates as `ValueError` before `physical_pricing_cache_checked` is emitted; the caller/supervisor should preserve that exception in its failure receipt. This is fail-closed and does not trigger a cold fallback. As agreed, the core treats the caller-supplied source object as the trust boundary; production use still depends on runner-side frozen-source, manifest, and raw-event pinning.

Reviewed source hashes:

- `src/egglab/native_hull.py`: `1b1ebf71fcc34a8faefa74b0af58be69d007a391fd29f1d58e23385c37907009`
- `src/egglab/native_pathflow_hull.py`: `9d30e9ca8babb2a7d3ddb0149161d522829ed3354fbc373d90e5f6eb592367f3`
- `src/tests/test_native_hull_pricing_cache.py`: `f4ae0e99fdbe1acaa823f125cd3f559f8a7d2ef2b86dd3a5e48db04e20b48a44`

Sol reports 26 focused cache and feasible-pool tests passing, plus `git diff --check`; no tests were rerun for this review.
