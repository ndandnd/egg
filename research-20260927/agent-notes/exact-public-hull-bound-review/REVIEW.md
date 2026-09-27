# Independent review: exact uniform-price depot-15 hull bound

27 September 2026. **PASS for the ideal stored-input full-37 depot-15 hull lower bound.** I recomputed the arithmetic from pinned JSON with Python standard-library `Fraction`, verified frozen source blobs using Git, and did not run the candidate checker, import model code, or call an optimizer.

The candidate `NOTE.md`, `RESULT.json`, and author checker are copied byte-identically to `result/sistig_exact_hull_bound/20260927-uniform-price1/`; their hashes are in that package's manifest. The nonlinear pilot source and protocol are read from the pinned `80eb69544f568a7ed346f0d603004a10f61c481a` blobs, not the later v2 worktree. The flow and flat-pilot frozen cases match, with identity `1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7` and the same public payload. The pinned independent flow review is PASS for the exact two-path certificate; the pinned one-bus review is PASS for this graph.

The stored binary objective coefficients are exactly `a=3602879701896397/18014398509481984` and `b=5124095576030431/4611686018427387904`, over 30 hourly loads. Vehicle cost is `f=100`, efficiency is one, deadhead-time cost is zero, and service and movement energies are nonnegative. Each used bus starts and ends at full 400-kWh usable inventory, so total grid energy `E=ΣL_t` equals route energy consumption. At uniform price `p`, every physical plan's linearized cost is `Kf+pE`.

For exactly two buses, the audited flow lower bound is `Lflow=4106419645886056876377559228024553/10141204801825835211973625643008`. I independently summed the 37 service energies and all legs on its 39 selected movements; the exact selected energy equals `(Lflow−2f)/a = Emin = 576810456487633549/562949953421312`. Thus every two-bus plan has `E≥Emin`.

For one bus, chronological sorting forces all 36 adjacent-service transitions. My scan found exactly one mode for each, always direct; the pinned charging rules allow charging only on depot or pull-in movements. The full service energy `250264333071608593/281474976710656` kWh exceeds the 400-kWh initial inventory, so one bus cannot cover the route without a modeled recharge opportunity. For `K≥3`, even the service-energy floor gives `3f+pEservice−(2f+pEmin) > 0`; the exact margin is in the machine report. These cases imply `Kf+pE≥2f+pEmin` for every physical full-fleet plan and therefore for every convex mixture.

With `p*=a+bEmin/30`, `p*≥a`. The exact per-period Fenchel inequality is `aL+bL²/2 ≥ p*L−(p*−a)²/(2b)` for every nonnegative load. Applying it to the averaged load of any mixture gives

`CH ≥ 2f+p*Emin−30(p*−a)²/(2b) = 2f+aEmin+bEmin²/60`

`= 37212685765349361762366900450676559743312987906100791/87690098239854175092221089962976981179355952578560 ≈ 424.365880667204`.

As a separate arithmetic check, I evaluated the 30 exact loads from the already independently passed two-bus feasibility witness under the same stored nonlinear objective. This yields `CH≤D≤749413355126211649563801319041034658846056466667585/1461501637330902918203684832716283019655932542976 ≈ 512.7694256264009`, where `D` is the ideal physical minimum. This is a feasible-plan upper bound, not a pilot measurement. The review establishes no exact optimum and makes no claim about a positive or quantified `D−CH` gap, rounded native-MIP feasibility, or recurring daily operation.

Reproduce with `python3 verify_uniform_bound.py --repo REPO --output NEW_REPORT.json`. The independent verifier pins all inputs and source blobs, uses exact fractions, and never executes the candidate checker. Its sealed arithmetic is in `audit-report.json`.
