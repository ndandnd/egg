# E10 protocol: per-trip top-m pruning (no global keep fraction)

Declared 2026-10-01 16:35 UTC after E8 (best global keep fraction shrinks with size on
synthetic cases but must be larger on out-of-distribution public cases).

- Rule: keep, for every trip, its m highest-scored incoming and m highest-scored outgoing
  direct/depot movements (plus all pullouts/pullins); no global fraction
  (`claude_e3_prune.py --keep 0 --min-options m`). m in {3, 5, 8}.
- Arm `learned4`, v8 scores (fold 0 / seed 17), `day` tariff, harness-fixed code.
- Cases/budgets as before: scale 50000-50003 x {40, 60, 80} at {60, 300} s; Hildenbrand
  15/16 at {180, 600} s; Eberbach at {600, 1800} s. 90 runs, <= 3 concurrent, 32 GB.
- Question: does one m work across sizes and across the synthetic/public shift, where
  no single global fraction did (E8)? Compare with the best global-fraction learned4 run
  per cell and with cold/cold4. Descriptive; one run per cell.
