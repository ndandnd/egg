## Review corrections and stronger public bounds — 29 September 2026

Version 0.8 is ready for author review: both markets now appear in one table using the strongest reviewed bounds; regret is identified as a diagnostic of the returned schedule. The draft adds the exact undamped price-update cycle, explains the posted marginal-tariff institution, and removes the historical flat-price schedule figure from the main paper.

A new exact bound uses the union of every allowed charging visit. The first six hours cannot contain charging in either declared depot case. This improves the four lower bounds by 4.86–12.03 cost units without another optimization run. Public planning-gap caps are now 83.55 and 87.03 for depot 15, and 89.67 and 105.58 for depot 16 (original and changed markets). All gap intervals still include zero; combinations with numerical upper witnesses retain their feasibility qualifications.

The literature discussion restores [Zoltowska and Lin on aggregated bus auction bids](https://doi.org/10.3390/en14164727), [Bichler and colleagues on nonconvex demand pricing](https://doi.org/10.1287/isre.2022.1139), and [Löbel and colleagues on nonlinear charging](https://arxiv.org/abs/2407.14446). The comparison distinguishes fixed bus availability from choosing complete service assignments, without claiming those authors ignore discrete charging constraints.

Cluster job 597526 is running the matched physical-planning and own-price-response study on the six solved development cases, reusing their completed hull bounds. It has one CPU, 8 GB and a 40-minute ceiling. A separate public bus-cost and curvature study is specified prospectively, retaining the current scenario and all zero or unresolved gaps; it has not been submitted.

[Read draft 0.8](https://github.com/ndandnd/egg/blob/codex/journal-research-20260927/output/pdf/egg-journal-v0.8-reviewed-draft.pdf) · [New bound and proof](https://github.com/ndandnd/egg/blob/codex/journal-research-20260927/research-20260929/charging-availability-bound/PROOF.md)
