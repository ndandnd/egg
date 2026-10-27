# Closest prior art and the claim we cannot make

Targeted primary-source review on 27 October 2026, not exhaustive novelty clearance. This work is newly justified by the human's ICML request. No old outcomes or raw data were used.

| Primary source | Direct overlap | Required distinction |
|---|---|---|
| [Gerbaux, Desaulniers & Cappart, COR 2025](https://research.dial.uclouvain.be/entities/publication/ce60f346-f699-41e0-b2d3-d0d7744d91aa) | GNN plus greedy arc selection for capacitated electric-bus column generation; experiments already involve large timetables. | Neither electric buses, learned arc reduction, classical/learned combination nor simply scaling is new. |
| [Sun et al., ICLR 2023](https://openreview.net/pdf?id=JHW30A4DXtO) | Learns columns useful to optimal integer solutions in vertex coloring. | Integer usefulness instead of negative reduced cost is already a learning target. |
| [Yuan, Fang & Song, AAAI 2024](https://ojs.aaai.org/index.php/AAAI/article/view/28661) | Reinforcement learning for selecting multiple columns during CG. | Selecting multiple columns is not by itself a new mechanism. |
| [Maher & Rönnberg, MPC 2023](https://link.springer.com/article/10.1007/s12532-023-00240-w) | IPColGen: incumbent destroy/repair with jointly useful generated sets for integer recovery. | Compatibility, positive-reduced-cost alternatives and incumbent-conditioned repair are not new. This is a central conventional comparison. |
| [Nair et al., 2020](https://arxiv.org/abs/2012.13349) | Neural Diving proposes partial assignments that a conventional solver completes. | Learned proposals plus exact completion/retention are established. |
| [Mandi et al., ICML 2022](https://proceedings.mlr.press/v162/mandi22a.html) | Decision-focused pointwise/pairwise/listwise ranking of feasible decisions. | A downstream-value loss or ranking objective alone is insufficient novelty. Here the known-cost search action, rather than an unknown cost coefficient, is predicted. |
| [Gao et al., COR 2025](https://doi.org/10.1016/j.cor.2025.107152) | Learning-guided column generation for constrained vehicle routing. | Constrained routing and integer-relevant learned arc contributions are also occupied. Full method comparison remains needed. |

Source depth: parent inspected the Gerbaux institutional abstract, Maher/Rönnberg full-text page and Mandi proceedings record. A bounded reviewer inspected the other primary records/paper results; OpenReview subsequently challenged the parent's browser access. Do not claim a complete implementation reproduction or theorem-by-theorem novelty review.

A possible differentiator is learning **conditional completion value of complementary bundles under shared resources and an explicit paid search budget**, with empirical evidence that additive membership scores and competent classical repair miss it. This is a hypothesis about a residual difficulty, not an established novelty claim. The classical completion problem in `SCIENTIFIC_TARGET.md` can solve the same selection exactly; any learning advantage must be computational or statistical under an honest information/budget comparison.

No universal requirement to add every cited method as a separate arm: choose direct relevant comparisons, implement faithfully, and explain exclusions. In particular, a weak reduced-cost ranker cannot substitute for joint completion or IPColGen-style repair.
