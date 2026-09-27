# Uniform-price exact Fenchel bound, depot 15 — candidate supplement

27 September 2026. **The inequality is valid for the ideal stored-input, full37, depot-15 nonlinear hull**, subject to the already independently passed one-bus obstruction and cardinality-flow certificate. This is an arithmetic supplement, not a replacement for the matched nonlinear pilot or a result from that failed attempt. No optimizer, public solve, cut, or model change was made. `check_uniform_bound.py` uses only the Python standard library, pins and checks its evidence bytes, and writes no files. `RESULT.json` records the full exact fractions.

The pinned flat-pilot input, cardinality-flow frozen case, and depot-15 case identity match exactly (`1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`). The published nonlinear source/protocol specifies 30 hourly periods and `F(L)=Σ_t[a L_t+b L_t²/2]`, with exact stored binary floats `a=3602879701896397/18014398509481984` and `b=5124095576030431/4611686018427387904`. The case has `f=100`, zero deadhead-time cost, efficiency 1, full replenishment by 30:00, and nonnegative service and declared movement energies. Thus total grid energy `E=Σ_t L_t` equals total route consumption in every feasible physical plan, and its uniform-price operating cost is exactly `Kf+pE` for `K` used buses.

The independently audited exact cardinality-flow lower bound at price `a` is
`Lflow=4106419645886056876377559228024553/10141204801825835211973625643008` (≈404.924239883878), attained by two relaxed paths. Its 39 selected movements plus all 37 services consume exactly
`Emin=(Lflow−2f)/a=576810456487633549/562949953421312` (≈1024.6211994193884 kWh). Every feasible two-bus plan maps into that relaxation and has `2f+aE≥Lflow`; hence `E≥Emin`. The independent one-bus proof excludes `K=1` for the same stored graph.

Set the uniform price `p*=a+b Emin/30=18532522483900860236424071843325139/77884452878022414427957444938301440` (≈0.237948933312). For every `K≥3`, nonnegative movement energy gives `E≥Eservice=250264333071608593/281474976710656` (≈889.1175194193885). The exact partition check is
`3f+p*Eservice−(2f+p*Emin)=2970810917322600962115942763650908954120237428078543/43845049119927087546110544981488490589677976289280` (≈67.757043884173) **positive**. Since `p*>0` and `f>0`, every `K≥3` plan also has `Kf+p*E≥2f+p*Emin`. Consequently the global physical uniform-price minimum, and any convex mixture of physical plans, is at least `2f+p*Emin`.

For each nonnegative hourly load, Fenchel gives `aL+bL²/2 ≥ p*L−(p*−a)²/(2b)`. Summing 30 periods yields the exact hull lower bound

`CH ≥ 2f+p*Emin−30(p*−a)²/(2b) = 2f+aEmin+bEmin²/60 = 37212685765349361762366900450676559743312987906100791/87690098239854175092221089962976981179355952578560 ≈ 424.365880667204`.

This certificate uses an exact flat **lower** bound to limit two-bus energy, not a two-bus feasible optimizer value. It does not certify a nonlinear planner value `D`, a `D−CH` gap, cost optimality, rounded native-MIP feasibility, or recurring daily operation. The separate exact two-bus candidate has since passed its independent ideal-model feasibility audit, but it is not needed for this lower certificate; no upper value is combined here. The fixed nonlinear pilot remains a separate required experiment, and its attempt 1 failed without a scientific conclusion.
