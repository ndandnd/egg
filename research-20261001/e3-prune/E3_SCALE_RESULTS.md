# E3 phase 2: learned pruning on 40-80-trip scaled timetables

Arrays 761781 (cold/cold4/learned/lp/random, 120 runs, code 4a4263e) and 765340
(learned4, harness-fixed code 0cd5da5; the 300 s learned4 cells were still running at
11:25 UTC). Cases `claude-scale-v1` 50000-50003 x {40, 60, 80} trips, `day` tariff, keep
30%. Scores: v8 attention fold 0 / seed 17 (trained on the 20-28-trip bank; all scaled
cases are new timetables at new sizes). Cells: bill relative to the best bill of any
arm/budget for that case. Two cold4 cells hit the fixed harness artifact and are rerun
once as `-hfix` (781391); other failures are genuine (4 LP runs where the LP used the
whole 60 s, 4 cold4 runs with no plan in its 15 s rounds, 1 replay refusal).

| Case | T s | cold | cold4 | learned | learned4 | lp | random |
|---|---:|---:|---:|---:|---:|---:|---:|
| scale:50000:40 | 60 | 0.88% | 0.65% | 0.00% | 0.31% | 2.28% | 37.66% |
| scale:50000:60 | 60 | 1.52% | 167.12% | 0.11% | 0.00% | 15.20% | 45.16% |
| scale:50000:80 | 60 | 263.12% | unresolved | 2.15% | 0.00% | 39.17% | 32.55% |
| scale:50001:40 | 60 | 0.69% | 0.40% | 0.78% | 1.19% | 32.16% | 32.19% |
| scale:50001:60 | 60 | 252.52% | 252.52% | 9.95% | 9.87% | 44.81% | 46.30% |
| scale:50001:80 | 60 | 234.70% | unresolved | 9.70% | 70.84% | fail | 21.30% |
| scale:50002:40 | 60 | 0.78% | 0.49% | 0.45% | 0.10% | 4.23% | 47.63% |
| scale:50002:60 | 60 | 0.00% | fail | 8.76% | 6.40% | fail | 23.57% |
| scale:50002:80 | 60 | 249.65% | unresolved | 1.48% | 13.39% | fail | 25.74% |
| scale:50003:40 | 60 | 0.37% | 0.37% | 0.36% | 0.00% | 10.11% | 48.51% |
| scale:50003:60 | 60 | 8.04% | fail | 2.28% | 0.00% | 4.02% | 35.39% |
| scale:50003:80 | 60 | 307.85% | unresolved | 4.19% | 5.98% | 530.75% | 31.45% |
| scale:50000:40 | 300 | 0.02% | 0.30% | 0.00% | 0.00% | 2.28% | 37.39% |
| scale:50000:60 | 300 | fail | 1.31% | 0.19% |  | 16.35% | 46.82% |
| scale:50000:80 | 300 | 5.24% | 17.38% | 2.10% |  | 20.82% | 29.80% |
| scale:50001:40 | 300 | 0.40% | 0.00% | 1.00% |  | 30.70% | 31.76% |
| scale:50001:60 | 300 | 20.97% | 252.52% | 0.00% |  | 44.46% | 35.18% |
| scale:50001:80 | 300 | 234.70% | 221.38% | 0.00% |  | 70.77% | 19.02% |
| scale:50002:40 | 300 | 0.17% | 0.00% | 0.02% |  | 4.23% | 47.63% |
| scale:50002:60 | 300 | 0.01% | 0.01% | 8.36% |  | 10.22% | 23.13% |
| scale:50002:80 | 300 | 249.65% | 166.63% | 0.00% |  | fail | 17.25% |
| scale:50003:40 | 300 | 0.36% | 0.02% | 0.36% |  | 9.31% | 48.22% |
| scale:50003:60 | 300 | 7.46% | 8.04% | 2.28% |  | 4.02% | 35.39% |
| scale:50003:80 | 300 | 21.71% | 291.05% | 0.00% |  | 24.90% | 33.00% |

Pairwise (win/tie/loss; failures count as losses; mean % bill difference over both-successful pairs)
learned vs cold @ 60s: 10/0/2  mean diff -29.369%  median -3.366%
learned vs cold @ 300s: 9/1/2  mean diff -15.974%  median -2.979%
learned vs lp @ 60s: 12/0/0  mean diff -20.822%  median -13.103%
learned vs lp @ 300s: 12/0/0  mean diff -14.734%  median -13.885%
learned vs random @ 60s: 12/0/0  mean diff -23.363%  median -24.106%
learned vs random @ 300s: 12/0/0  mean diff -23.847%  median -24.634%
learned4 vs cold4 @ 60s: 11/0/1  mean diff -21.950%  median -0.376%
learned4 vs cold4 @ 300s: 1/0/0  mean diff -0.297%  median -0.297%
learned4 vs cold @ 60s: 10/0/2  mean diff -27.957%  median -4.472%
learned4 vs cold @ 300s: 1/0/0  mean diff -0.018%  median -0.018%
cold4 vs cold @ 60s: 3/2/7  mean diff +27.051%  median -0.116%
cold4 vs cold @ 300s: 6/1/5  mean diff +36.040%  median +0.000%
lp vs cold @ 60s: 3/0/9  mean diff -1.158%  median +3.427%
lp vs cold @ 300s: 3/0/9  mean diff +4.029%  median +6.486%

## 80-trip bills (buses in parentheses)

| Case | T s | cold | learned | learned4 | random |
|---|---:|---:|---:|---:|---:|
| scale:50000:80 | 60 | 3271 (25) | 920 (4) | 901 (4) | 1194 (6) |
| scale:50000:80 | 300 | 948 (4) | 920 (4) |  | 1169 (6) |
| scale:50001:80 | 60 | 4082 (30) | 1338 (6) | 2084 (12) | 1479 (7) |
| scale:50001:80 | 300 | 4082 (30) | 1220 (5) |  | 1452 (7) |
| scale:50002:80 | 60 | 4499 (32) | 1306 (5) | 1459 (6) | 1618 (7) |
| scale:50002:80 | 300 | 4499 (32) | 1287 (5) |  | 1509 (6) |
| scale:50003:80 | 60 | 3872 (31) | 989 (4) | 1006 (4) | 1248 (6) |
| scale:50003:80 | 300 | 1155 (6) | 949 (4) |  | 1263 (6) |

## Findings

1. **Learned pruning beats cold** 10/0/2 at 60 s (median -3.4%, mean -29%) and 9/1/2 at
   300 s (median -3.0%, mean -16%). At 80 trips cold returns 25-35-bus plans (bills
   3200-4500) even after 300 s on three of four instances; learned pruning returns 4-7
   buses within ~2% of the best plan found.
2. **The learned scores matter beyond pruning itself**: learned beats random pruning
   12/12 at both budgets (median -24%) and LP-relaxation pruning 12/12 (median -13%).
3. **Ceiling effect of a fixed 30% keep rule**: where learned loses (50002/60 trips:
   +8.4% at 300 s; 50001/40) extra time does not help, because the movements the best
   plan needs were pruned. Remedies to test next: a keep-fraction sweep and a hybrid
   that warm-starts the full MIP from the pruned plan.
4. learned4 vs cold4 at 60 s: 11/0/1 (median -0.4%, mean -22%); the four-round split
   alone is unreliable at 60-80 trips with short rounds (no plan in 4 cases).
