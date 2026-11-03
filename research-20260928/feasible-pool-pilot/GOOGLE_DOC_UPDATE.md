# Matched computational pilot launched — 28 September 2026

The first screen suggested a practical improvement: expensive pricing returned useful fleet plans, but the solver did not have time to combine the final plan into its best mixture. A new matched pilot now tests reserving ten seconds within the existing time budget for that work. A separate arm also reuses physically checked fleet plans from an unfinished but valid initial solve.

The pilot has 24 hull calculations: four physical cases, two markets and three methods—ordinary cold solving, cold solving with reserved finishing time, and feasible-pool reuse with the same reserve. Every method pays for its own initial solve. Only physical fleet plans transfer between markets; mixture weights and global bounds are computed afresh. Both Hildenbrand depots remain one timetable group, and all cases are development data.

The implementation and prospective protocol passed focused review and 113 relevant tests; the published execution commit also passed the complete CI suite and reconstruction of historical evidence. The single Unicorn job is 572392, submitted at 06:14 UTC and pending for priority at that observation. It requests one CPU, 8 GB and at most two hours, with no retry or requeue. No result is available yet. The next analysis will compare final enclosures, calls, failures and complete two-market time before considering a broader sweep or learned proposals.

Prospective design and resource limits: https://github.com/ndandnd/egg/blob/77dee963eb30ba85bca68b3efcf61d099fa33076/doc/FEASIBLE_POOL_PILOT_PROTOCOL_20260928.md

The previous computational figures, findings and historical failed attempts remain unchanged. This launch establishes no speedup, public optimality gap or learning advantage.
