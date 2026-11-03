# CF1 v5 deterministic fake capacity correction

24 October 2026. This prospective source-only correction addresses the shared
setup failure recorded in `CF1_V5_SOURCE_FAILURE_DIAGNOSIS.md`. In
`src/tests/test_cf1_entry_repaired.py`, `owner_harness` now uses one deterministic
capacity value, 8, for both the fake OS `cpu_count()` and the handwritten owner
root's `capacity_cpu_count`, before writing and hashing that root. The production
owner's CPU-capacity identity check and all other guards remain unchanged.

The handwritten passing source-receipt fixtures identify attempt02 and their
rejection cases identify the preserved attempt01. This follows the prospective
attempt02 wrapper identity; it does not relabel or modify the failed attempt.

Only this test source and this note were edited for this correction. No project
imports, test invocation, native work, data work, cluster work or commits were
performed. No unobserved latent behavior was patched. The failed attempt01,
its source snapshot, receipts, prior notes and final cumulative account
1534.2196428390087 seconds remain preserved without credit or reset.

This edit establishes no passing coverage. The 26 owner cases blocked during
common setup in attempt01 remain unestablished until a separately frozen and
authorized source invocation runs. Such a check still cannot establish actual
runtime ownership, timing, native entry or the CF1 mechanism. There is no
automatic retry or broader authorization from this correction.
