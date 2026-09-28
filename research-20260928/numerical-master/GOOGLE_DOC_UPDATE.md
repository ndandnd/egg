# Numerical master integration completed — 28 September 2026

An explicit numerical restricted-master policy now complements the saved-pricing-bound cache. It proposes mixture weights with SLSQP, rounds them to a fixed denominator, and replays the physical fleet plans and mixture objective. This avoids repeated pairwise rational polishing in the new policy; the original method remains available as a baseline.

A numerical success flag does not establish a global hull certificate. The coordinator records the exact restricted-pool gap and still requires fresh global pricing before certification. Failed proposals retain previously verified bounds and are reported explicitly. Time limits, arithmetic limits and invalid physical data remain distinct outcomes, with spent work preserved.

All 37 focused numerical-master, cache and feasible-reuse tests passed, and independent review found no remaining blocker. Online performance remains unmeasured. The next package will freeze and run an ordered comparison of reserve-cold solving, retained plans, the numerical master and pricing-bound reuse, on the existing development cases. No new cluster experiment was launched during this implementation.

Scope and independent review: https://github.com/ndandnd/egg/blob/dc5e01480996ae97adb08821e9fb518cba43492b/research-20260928/agent-notes/numerical-master/REVIEW.md
