# E9 results: learned plans as seeds for complete-fleet hull certification

Array 785526 (10 cases), all completed, collected 16:25 UTC. Hulls: GRB, 1 thread,
500 s phase / 600 s wall, 32 pricing calls, QP master; seeds are the routes of the
learned 300 s runs (learned4 keep 15% and 30%, learned keep 30%) with charging
re-optimized by the fixed-route LP and replayed. D lower: best full-case cold planner
bound (pruned bounds never used), tightened by D >= CH lower. Native, tolerance-
qualified enclosures. Status `budget_exhausted` = interval valid but not closed.

| Case | cold hull [L, U] (width) | seeded hull [L, U] (width) | D interval | gap D-CH | regret of best seed |
|---|---|---|---|---|---|

## Findings

1. **Seeding with learned plans tightens the hull enclosure on 10/10 cases**:
   width ratios seeded/cold are 0.08, 0.28, 0.63 at 40 trips (plus one case certified
   only when seeded: 50002/40), 0.31-0.58 at 60 trips, 0.38-0.55 at 80 trips. Both the
   global lower bound and the mixture upper bound improve.
2. Only one hull certifies; every gap interval still contains zero. At 60-80 trips the
   enclosures remain tens to hundreds of units wide after 600 s.
3. The own-price response (60 s) is not solved at 60-80 trips, so those regret
   intervals are uninformative (lower ends far below zero; mathematically regret >= 0).
   50003/60 has a strictly positive regret interval [68.9, 164.5] for its seed plan,
   which includes that plan's own excess over the optimum.
4. Implication for the paper: learned plans make the price-support computation
   materially cheaper (tighter bounds in equal time), but certifying D - CH at 60+ trips
   still needs a stronger pricing oracle or longer budgets.
