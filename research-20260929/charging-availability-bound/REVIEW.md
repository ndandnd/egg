# Independent review of the four manuscript floors

**Verdict: pass for the pinned ideal-model cases and two archived markets.**
This review covers the four `f=100` manuscript rows, not the analytical
sensitivity grid or any native solver claim. I used the archived
`scientific_evidence.zip/frozen.json`, the previously reviewed exact two-bus
energy floors, and Python standard-library `Fraction`. I did not call the
bound builder or any optimizer to obtain the cross-check values.

The native physical schema permits charging on `depot` and `pullin` movements
only (`src/egglab/native_recharge.py`, `_window` and replay validation).
Enumerating those declared windows directly from the frozen public cases gives
first possible charging at 811/2 and 817/2 minutes for depots 15 and 16.
Every declared charging window begins after minute 360. The union is an outer
availability envelope, so zero grid load in the first six market hours holds
for every selected fleet and every convex mixture. Intersecting that union
with the single 360 kW connector gives seventh-hour caps 87 and 69 kWh;
the remaining 23 hourly caps are 360 kWh. These are energy caps, not weights
on the supply-cost function. Each bus starts full and the source model has no
other charging movement.

For each market I independently evaluated, with exact fractions, the
24-positive-period expression

`2f + p E2 - Σ_{t=7}^{30}(p-a_t)^2/(2b)`, with
`p = mean(a_7,...,a_30) + b E2/24`.

The result equals the exact `lower_exact` fraction in `bounds.json` in all
four rows. At these prices the three-or-more-bus lower expression is higher,
and every conjugate load `(p-a_t)/b` is positive and below its hourly cap.

| Depot | Market | Exact value, decimal display | Largest conjugate load | Smallest positive cap |
|---|---|---:|---:|---:|
| 15 | Original | 429.2262908630 | 42.69 | 87 |
| 15 | Changed | 430.2993968601 | 65.19 | 87 |
| 16 | Original | 440.9945782629 | 44.67 | 69 |
| 16 | Changed | 442.3044399933 | 67.17 | 69 |

Thus the first six zero-load hours produce the gain for these rows; the
positive connector caps validate the bound but do not bind its dual
maximizer. A fractional seventh-hour weight in the quadratic supply objective
would be incorrect because the declared market objective is in hourly energy.

I also checked the v0.8 table generator: it reads these four exact lower
fractions, rounds them downward, combines the archived screen's upper
fractions (except for the separate exact depot-15 original-market witness),
and recomputes the gap caps by outward rounding. It preserves the native
qualification on the other public uppers and all incumbent regret intervals.
The resulting public gap caps are 83.55, 87.03, 89.67, and 105.58. Every
interval still includes zero, and the result says nothing about public
optimal-fleet regret or a bus-cost sweep.
