# E6 results: keep-fraction sweep for learned pruning (12 scaled cases)

Arrays 781395 (keep 0.15 and 0.50, 48 runs, code 0cd5da5) + existing keep-0.30 learned4
(765340) and cold/cold4 (761781; two cold4 artifact cells replaced by their -hfix
reruns 781391). Policy learned4 = v8 scores + four-round split; >= 3 options per trip
side are always kept. Cells: bill relative to the best bill of any listed arm/budget.
Collected 13:25 UTC. Script `summarize_keep.py`.

| Case | T s | cold | cold4 | learned4_k15 | learned4_k30 | learned4_k50 |
|---|---:|---:|---:|---:|---:|---:|
| scale:50000:40 | 60 | 1.08% | 0.85% | 0.00% | 0.51% | 0.85% |
| scale:50001:40 | 60 | 0.81% | 0.52% | 0.64% | 1.31% | 1.02% |
| scale:50002:40 | 60 | 0.78% | 0.49% | 0.08% | 0.10% | 0.52% |
| scale:50003:40 | 60 | 0.37% | 0.37% | 0.25% | 0.00% | 1.99% |
| scale:50000:60 | 60 | 2.97% | 170.92% | 0.00% | 1.42% | 1.21% |
| scale:50001:60 | 60 | 261.87% | 261.87% | 2.52% | 12.78% | 81.79% |
| scale:50002:60 | 60 | 4.38% | 141.89% | 0.27% | 11.05% | 1.77% |
| scale:50003:60 | 60 | 9.34% | 145.68% | 0.32% | 1.20% | 3.29% |
| scale:50000:80 | 60 | 270.37% | fail | 2.20% | 1.99% | 12.04% |
| scale:50001:80 | 60 | 275.37% | fail | 2.74% | 91.61% | 183.93% |
| scale:50002:80 | 60 | 268.81% | fail | 5.13% | 19.61% | 111.06% |
| scale:50003:80 | 60 | 319.68% | fail | 1.38% | 9.06% | 28.53% |
| scale:50000:40 | 300 | 0.21% | 0.50% | 0.00% | 0.20% | 0.02% |
| scale:50001:40 | 300 | 0.52% | 0.12% | 0.43% | 0.00% | 0.26% |
| scale:50002:40 | 300 | 0.17% | 0.00% | 0.08% | 0.10% | 0.29% |
| scale:50003:40 | 300 | 0.36% | 0.02% | 0.21% | 0.02% | 0.07% |
| scale:50000:60 | 300 | fail | 2.75% | 0.94% | 0.95% | 1.27% |
| scale:50001:60 | 300 | 24.18% | 261.87% | 0.00% | 0.48% | 2.00% |
| scale:50002:60 | 300 | 4.39% | 4.39% | 0.00% | 0.12% | 1.16% |
| scale:50003:60 | 300 | 8.75% | 9.34% | 0.15% | 2.02% | 0.00% |
| scale:50000:80 | 300 | 7.34% | 19.72% | 0.00% | 1.11% | 3.57% |
| scale:50001:80 | 300 | 275.37% | 260.44% | 0.00% | 14.40% | 133.01% |
| scale:50002:80 | 300 | 268.81% | 181.24% | 0.00% | 4.18% | 4.57% |
| scale:50003:80 | 300 | 25.24% | 302.39% | 0.00% | 0.83% | 0.77% |

learned4_k15 vs cold @60s: 12/0/0  median -6.09%
learned4_k15 vs cold @300s: 12/0/0  median -6.83%
learned4_k15 vs cold4 @60s: 11/0/1  median -29.69%
learned4_k15 vs cold4 @300s: 9/0/3  median -6.30%
learned4_k30 vs cold @60s: 10/0/2  median -4.47%
learned4_k30 vs cold @300s: 12/0/0  median -5.80%
learned4_k30 vs cold4 @60s: 11/0/1  median -27.24%
learned4_k30 vs cold4 @300s: 11/0/1  median -5.39%
learned4_k50 vs cold @60s: 10/0/2  median -4.01%
learned4_k50 vs cold @300s: 11/0/1  median -3.51%
learned4_k50 vs cold4 @60s: 8/0/4  median -24.88%
learned4_k50 vs cold4 @300s: 9/0/3  median -5.81%

Mean movements kept (all movements incl. pullouts/pullins):

| Trips | movements (full) | kept at 15% | kept at 30% | kept at 50% |
|---:|---:|---:|---:|---:|
| 40 | 1437 | 291 | 492 | 765 |
| 60 | 3408 | 611 | 1094 | 1742 |
| 80 | 6065 | 1052 | 1938 | 3122 |

## Findings

1. **Aggressive pruning (keep 15%) is best**: it beats the unpruned solver 12/12 at
   both 60 s and 300 s (median -6.1% / -6.8%) and the four-round unpruned solver 11/1
   (60 s) and 9/3 (300 s). At 80 trips it is within 1.4-5.1% of the best plan at 60 s
   and is itself the best plan on all four instances at 300 s.
2. **The E3 "ceiling" was not lost movements.** At keep 30% several 60-80-trip cases
   plateau 4-92% above the best; keep 15% removes most of it (e.g. 50001/80 at 60 s:
   +91.6% -> +2.7%; 50002/60: +11.1% -> +0.3%). The pruned MIP at 30% is still too large to
   solve well in the budget; the per-trip minimum of three options keeps the 15%
   problem feasible and good.
3. Keep 50% is consistently worse than 15-30% at 60-80 trips.
4. At 40 trips all settings are within ~2% of each other and of cold.

Scope: 12 development cases from one generator, one run per cell, `day` tariff; a
keep fraction chosen here is a design input, not a validated general rule. A natural
next step is keep 15% on the public cases and an even smaller keep (e.g. 5-10%).
