# Draft 1 status (30 October 2026)

Branch `paper/draft1-20261030`, directory `paper/draft1/`. Build: `./make.sh`
(add `--tests` for the exact randomized checks, ~8 min). The previous focused
draft (`paper/focused-theory-20261029/`, PDF v13) is kept unchanged as an archive.

## What changed relative to v13

| v13 problem (see the three internal referee notes) | Draft 1 |
|---|---|
| 66 pages, 8-page body, appendices A–Y, ~45 negations in the first 8 pages | ~21 pages total; one scope paragraph; proofs in 5 appendices |
| Competing centres of gravity (support, projection, certificates) | One story: exact projection, then what it implies for support and price iteration, then where it stops, then data |
| Support failure "inherited from classical theory" | New: gap anatomy (fee/spread condition, κδ²/8 bound) and price-iteration theorem (cycling iff degenerate tangency; damping traps; diminishing steps recover hull) |
| No practical significance; synthetic only | 18-operator calibrated study from public CC BY timetables (critical spreads, gap incidence, regret/gap, cycling) |
| Disconnected from the B1–B3 flagship | Theorem explains the flagship's tâtonnement cycles: most cycles in calibrated scenarios have zero gap |
| Wu 2019 compared from publisher preview only | Read in full (Imperial Spiral accepted version); positioned precisely |
| Zhou 2025 glyph-limited | Still not accessible in full text from here; the draft claims only what its abstract states |
| NP-hardness cited to a path-puzzles paper | Garey & Johnson [SP16] |
| Setup-slack proposition missing anchor membership | Dropped from this draft (discussed qualitatively as an open direction) |

## Established (proof plus exact randomized check)

- Theorem `thm:projection` (vetted v13 proof, restated for n_A ≠ n_B; sorted
  formula checked for unequal sizes).
- Corollary `cor:support`, Proposition `prop:support` (classical).
- Proposition `prop:anatomy` and Theorem `thm:iteration` (new): proofs in
  Appendix C; `code/test_twobatch.py` checks every clause on several thousand
  exact instances (vertex, sloping-face and flat-face cases).
- Propositions `prop:completegraph`, `prop:threebatch` (vetted v13 proofs).
- Public 37-service certificate (v13 evidence, unchanged; summarized only).

## Calibrated study (code/study.py → results/summary.json)

18 of 20 operators (two have fewer than five peak runs per batch). Operator /
battery combinations with a run longer than the battery are excluded, not trimmed.
B=400 kWh (all 18 eligible): 15 have r_m ≡ 0, so no gap at any price; the other
three need spreads ≥0.53 EUR/kWh (f=150). B=300: 8 of 14 eligible can have a gap,
from 0.91 EUR/kWh. Sweep at B=400 (2664 scenarios): 7 gap scenarios, max 0.023% of
total daily cost, regret ≈ 8.5× gap; undamped cycles in 397, of which 390 have Δ=0
(384 flat-face optima, 7 sloping-face, 6 vertex optima with too large a step).

## Independent referee pass (30 Oct)

A fresh referee subagent checked the new proofs, the n_A≠n_B projection and every
number. Fixed: an overstated iff for non-convergence (the abstract now separates
small-step convergence at vertices from cycling with large steps); a consistent
breakpoint definition; recurrence and M>0 caveats in Theorem (c); the
undisclosed run filter (now explicit exclusion); relative-cost denominator
(now total daily cost); κ notation; ρ=0 removed from the grid; the
"order of magnitude" overstatement; the uncited "our earlier work" claim;
the stale test log and a non-asserting test branch.

## Open / next

1. External expert read of the projection theorem's novelty (the aggregation
   comparison is still the main novelty risk).
2. Zhou et al. (2025) full text (needs library access).
3. Staggered windows or setup time with an error bound would most extend reach.
4. Run the price-iteration diagnostic (Δ vs. cycling) on the flagship B2
   instances. Computing Δ there needs a complete-plan hull bound, which is a
   separate project.
5. Economics in the study are a sensitivity grid, not a calibration; a real
   tariff (e.g. a demand-charge schedule) would sharpen Result 1.
