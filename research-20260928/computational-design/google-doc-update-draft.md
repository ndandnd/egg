# Computational research direction — launch preparation

The research direction is computational: first assess iterative physical planning, hull, and own-price workflows; consider learned route proposals only after measuring a bottleneck. The first screen has four cases—cyclic2, multivisit3, and Hildenbrand depot-15/depot-16 variants—under two market states: eight case–market groups and up to 32 planner, cold-hull, retained-hull, and own-price stages. All are development diagnostics, not held-out tests. Launch awaits source freeze.

Each current EGG hull column is a complete feasible fleet plan with service coverage, movements, charging/SOC, and hourly load. A route prediction must be assembled or repaired into a complete plan and replayed before use; it cannot certify a lower bound. Complete-fleet pricing remains the certification step. Prior reuse evidence is incomplete and showed no reduction in clean pricing calls on matched cases, so no ML benefit is established. Preserve failures and bounded outcomes.

The pinned CC BY 4.0 Sistig archive has 20 operator timetable bases. Only Hildenbrand (37 services) has a prepared, qualified EGG input; its two depot variants are one development base. Eberbach (105), Dreieich (131), and Bad Nauheim (137) are next-scale candidates, not yet admitted. Group every variant by base timetable in evaluation splits.

The focused literature review covers Shen et al. (2022), Chi et al. (2022), Abouelrous et al. (2025 preprint), Nair et al. (2020), Huang et al. (2024), and Hottung & Tierney (2022); see the [six-reference review](LEARNED_ROUTE_REVIEW.md). The [recent scope check](../../paper/related-work/RECENT_SCOPE_CHECK_20260927.md) adds bus decomposition, stochastic battery scheduling, and aggregator-agent work. These motivate comparisons, not priority or efficacy claims. Assess the iterative baseline before any learning campaign.

Draft revisions distinguish price support from strategic price impact, label solver/tolerance limits, and add direct bus-scheduling context. Local Tectonic is available; no LaTeX toolchain was found on the cluster. The prospective cap is one serial job (request 1 CPU/8 GB, at most 2 hours), with hourly follow-ups and no retries. No run has started.

**Launch record (fill only after freeze/submission):** source commit `[pending freeze]`; frozen input SHA-256 `[pending freeze]`; job ID `[pending submission]`; launch/status `[pending confirmation]`; result path `[pending launch]`.
