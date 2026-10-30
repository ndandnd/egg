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

18 operators kept of 20 (two with fewer than five peak runs per batch).
B=400 kWh: 15/18 cannot have a gap at any price. B=300: 11/18 can, at spreads
≥0.75 EUR/kWh (f=150). Gap scenarios: 13/3330 (B=300), max 0.063% of cost,
regret ≈ 4.7× gap. Undamped cycles: 391/3330, of which 378 have Δ=0.

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
