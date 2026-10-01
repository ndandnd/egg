# E0 results: price-support evidence on the 16 v7 TRAIN timetables (`day` tariff)

Jobs 758455 (smoke, 10074) and 758495 (15 groups), 1 October 2026, code
`claude/research-20261001` @ 26495e9. All 16 tasks completed; nothing retried.
Raw outputs: `~/egg-claude-20261001/runs/e0-support-20261001/out` on unicorn2;
compact rows: `e0_rows.json`. Values are native solver enclosures (Gurobi, replayed
plans), tolerance-qualified, not exact rational proofs.

## Headline

- **14/16 groups certify both hulls** (cold and source-seeded), typically in 3-75 s.
  The v7 hull failure was purely the keyword typo.
- **4/16 groups have a certified strictly positive physical-minus-hull gap**
  (10068, 10071, 10073, 10077): lower gap bounds 0.04-0.21, upper 0.17-0.50 cost
  units on bills of 450-570. In these timetables no physical fleet is a best response
  to its own marginal prices; the indivisible routing choice is economically live.
- The gaps are small: at most ~0.1% of the bill, consistent with the earlier
  8/16/24-trip diagnostics. 10 further groups have gap intervals [0, <=0.23].
- Own-price regret of the v7 cold incumbent is 0.12-3.25 (certified responses) in the
  14 well-behaved groups. By Proposition 1 it includes the incumbent's own excess over
  CH, so it is an upper-level incentive diagnostic, not the optimal fleet's regret.
- Hard groups: 10069 (cold hull failed - "whole-incumbent charge projection exceeds
  roundoff budget", a numerical extraction refusal; retained hull budget-exhausted;
  gap in [0, 8.5]) and 10075 (both hulls budget-exhausted; gap in [0, 1.14]). These are
  the same two groups where the v7 cold planner left visible gaps.

## Table

| Group | D | CH | Gap D-CH | Own-price regret of cold incumbent | Hulls (s) |
|---|---|---|---|---|---|
| 10064 | [659.094, 659.127] | [659.094, 659.094] | [0.000, 0.033] | [0.571, 0.571] | certified/certified {'cold_hull': 51.8, 'retained_hull': 51.7} |
| 10065 | [479.977, 479.992] | [479.977, 479.977] | [0.000, 0.015] | [0.322, 0.322] | certified/certified {'cold_hull': 19.0, 'retained_hull': 16.3} |
| 10066 | [712.983, 713.004] | [712.983, 712.983] | [0.000, 0.021] | [0.373, 0.373] | certified/certified {'cold_hull': 72.8, 'retained_hull': 74.4} |
| 10067 | [429.977, 430.039] | [429.977, 429.977] | [0.000, 0.062] | [0.874, 0.874] | certified/certified {'cold_hull': 6.0, 'retained_hull': 6.1} |
| 10068 | [572.623, 572.871] | [572.412, 572.412] | [0.211, 0.459] | [2.922, 2.922] | certified/certified {'cold_hull': 10.6, 'retained_hull': 9.7} |
| 10069 | [759.594, 768.129] | [759.594, 766.139] | [0.000, 8.535] | [6.946, 38.948] | failed/budget_exhausted {'cold_hull': 152.1, 'retained_hull': 171.8} |
| 10070 | [563.845, 564.079] | [563.845, 563.845] | [0.000, 0.234] | [1.297, 1.297] | certified/certified {'cold_hull': 39.6, 'retained_hull': 53.9} |
| 10071 | [506.274, 506.402] | [506.234, 506.234] | [0.040, 0.167] | [1.364, 1.364] | certified/certified {'cold_hull': 11.4, 'retained_hull': 10.8} |
| 10072 | [531.561, 531.570] | [531.561, 531.561] | [0.000, 0.009] | [0.361, 0.361] | certified/certified {'cold_hull': 26.3, 'retained_hull': 34.5} |
| 10073 | [449.853, 450.016] | [449.737, 449.737] | [0.116, 0.279] | [2.550, 2.550] | certified/certified {'cold_hull': 5.4, 'retained_hull': 6.7} |
| 10074 | [495.561, 495.570] | [495.561, 495.561] | [0.000, 0.008] | [0.203, 0.203] | certified/certified {'cold_hull': 5.6, 'retained_hull': 2.9} |
| 10075 | [571.916, 573.059] | [571.916, 572.240] | [0.000, 1.143] | [2.215, 6.720] | budget_exhausted/budget_exhausted {'cold_hull': 171.3, 'retained_hull': 172.1} |
| 10076 | [622.775, 622.821] | [622.775, 622.775] | [0.000, 0.047] | [0.124, 0.124] | certified/certified {'cold_hull': 20.5, 'retained_hull': 24.0} |
| 10077 | [566.092, 566.382] | [565.881, 565.881] | [0.211, 0.501] | [3.249, 3.249] | certified/certified {'cold_hull': 10.4, 'retained_hull': 7.8} |
| 10078 | [579.418, 579.600] | [579.418, 579.418] | [0.000, 0.181] | [1.193, 1.193] | certified/certified {'cold_hull': 62.6, 'retained_hull': 36.6} |
| 10079 | [486.914, 486.921] | [486.914, 486.914] | [0.000, 0.007] | [0.183, 0.183] | certified/certified {'cold_hull': 6.4, 'retained_hull': 3.1} |

D: v7 cold planner bounds, lower tightened by D >= CH-lower. CH: best of the two hull
runs, upper capped by D-upper. Gap = [max(0, D_lo - CH_up), D_up - CH_lo].
