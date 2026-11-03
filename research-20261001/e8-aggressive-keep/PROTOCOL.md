# E8 protocol: how aggressive can learned pruning be?

Declared 2026-10-01 13:30 UTC after E6 (keep 15% beat 30% and 50% at 60-80 trips).

- Arm `learned4` (v8 scores, fold 0 / seed 17; four-round split), >= 3 options per
  trip side always kept, harness-fixed code, `day` tariff.
- Public: Hildenbrand 15/16 at T in {180, 600} s and Eberbach at {600, 1800} s, keep in
  {0.05, 0.10, 0.15} (18 runs; keep 0.30 exists from E5).
- Scaled: 50000-50003 x {40, 60, 80} at T in {60, 300} s, keep in {0.05, 0.10}
  (48 runs; 0.15/0.30/0.50 exist from E3/E6).
- Report per case: bill vs best of any arm, buses, movements kept, failures (an
  infeasible pruned case counts as a loss). Descriptive; no general keep rule claimed.
