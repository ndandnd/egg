# E7 protocol: pruning with tariff-aware (multi8) scores

Declared 2026-10-01 12:30 UTC after E4 (multi8 improves held-out-tariff ranking 4/4
folds). Question: do multi8 scores prune better than v8 scores at scale?

- Scores: E4 multi8 graph attention, fold 0 / seed 17 (`claude_score_v8.py --e4-runs`),
  `day` tariff features. Scaled and public cases are outside the TRAIN bank, so fold 0
  is held out for all of them. (v8 E3/E5 scores were also fold 0 / seed 17.)
- Runs: arm `learned4`, keep 0.30, scale 50000-50003 x {40, 60, 80} at T in {60, 300} s
  (24 runs) and public Hildenbrand 15/16 at {180, 600} s plus Eberbach at {600, 1800} s
  (6 runs). Output names carry `-m8`. Harness-fixed code.
- Comparison: paired with the existing v8 `learned4` keep-0.30 runs (same case, T,
  keep, policy). Report wins/ties/losses and mean % bill difference; failures count as
  losses. One run per cell; descriptive.
