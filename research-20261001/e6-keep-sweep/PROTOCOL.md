# E6 protocol: keep-fraction sweep for learned pruning

Declared 2026-10-01 11:35 UTC, after E3 phase 2 showed a ceiling effect (with 30% kept,
some cases plateau above cold because the best plan's movements were pruned).

- Arm `learned4` (v8 scores, four-round split), keep in {0.15, 0.50} added to the
  existing 0.30; same 12 scaled cases (50000-50003 x {40, 60, 80} trips), T in {60, 300}
  s, `day` tariff, >= 3 options per trip side. 48 runs, harness-fixed code.
- Question: is there a keep fraction that removes the ceiling without losing the
  speed advantage at 80 trips? Report per case and keep: bill relative to the best bill
  of any E3/E6 arm, buses, movements kept, failures.
- No selection of a "best keep" is claimed from these 12 development cases as a general
  rule; it informs the next design.
