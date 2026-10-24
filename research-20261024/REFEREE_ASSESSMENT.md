# What to take from the referee perspective

24 October 2026. Integrated research decision, informed by bounded historical
document, primary-source and proof checks. This is not a new empirical closeout,
manuscript draft, resource increase or launch manifest. Supporting notes are
`REFEREE_EVIDENCE_NOTE.md`, `REFEREE_THEORY_NOTE.md` and `REFEREE_SOURCE_NOTE.md`.

The report supplies useful pressure to scale and specify the institution, but its
promised speedups and proposed theorems are not reliable instructions. It largely
evaluates August stabilization/measurement experiments, rather than the current
local prediction/replay campaign. The older negative result remains relevant;
neither the report nor the newer implementation work establishes paper readiness.

## Keep these challenges

**Honor the failed stabilization claim.** Historical B2 documents support the
reported median total-call ordering24 versus30–34 and corrected solver-wall
38.48 versus43.59–57.08 seconds. They do not support presenting A3–A5 as overall
winners. Reduced clean calls do not pay for additional candidate calls by
themselves. This rejects the specified acceleration claim on that cohort; it
does not invalidate price-support analysis or prove all stabilization futile.
Full startup-to-verified-output time remains the current comparison endpoint,
not the historical corrected solver-wall metric alone.

**Scale a defensible question.** Forty-plus trips and richer charging/tariffs are
necessary evidence for a fleet-method claim. Current code paths at40/80/120 trips
do not substitute for a verified matched large-case result. Do not build an
experiment whose success condition presumes stabilization wins. Test the cheapest
credible certified baseline and strong charging-aware classical proposals alongside
learned ones; attribute any benefit beyond simply shrinking the problem.

**Define the market institution.** Dantzig–Wolfe can compute a convexified bound
and supporting dual prices. An executable allocation, price rule, side payments
and information/reporting assumptions still need to be specified for an economic
implementation claim. A price-taking result is not strategic truthfulness.
[Hua–Baldick, §III.A](https://users.ece.utexas.edu/~baldick/papers/convex_hull_2017.pdf)
recovers the Lagrangian-dual value, not equality to the indivisible primal optimum.

## Correct these statements

1. **The loop headline is misstated.** The detailed measurement document reports
   zero fixed points across176 algorithm-parameter cells only at `b=.05`, on32
   distinct instances. At `b=.01` some fixed points were observed. Strong-feedback
   runs also include unresolved transients. These finite trajectories do not
   establish nonexistence of a fixed point. A targeted erratum now corrects the public status summary;
   the underlying measurement record and protected outcomes remain untouched.
2. **More price coordinates do not guarantee a3–5-fold speedup.** Decisions depend
   on load-difference directions, not just the number of stored price entries.
   Redundant time refinements can leave the active price dimension unchanged.
   Degeneracy, pricing difficulty, candidate overhead and stopping rules matter.
   Primary stabilization literature motivates a controlled test, not that forecast;
   see the source note for full-text versus abstract-only access limits.
3. **The proposed cycling inequality is not a theorem as written.** For exactly
   two schedules, define `delta=L_y-L_x`, `p_x=a+B L_x`,
   `g=c_y-c_x+p_x^T delta`, `Q=delta^T B delta`. A strict undamped two-cycle occurs
   exactly when `-Q < g < 0`; additional schedules require global dominance
   checks. For scalar feedback, `Q=b||delta||^2`, which has cost units. A bare
   `b||delta|| > vertex margin` needs a defined margin and consistent units.
   Damping need not create a long-period orbit: the theory note gives a strict
   two-cycle for every `0 < alpha <= 1`, locally attracting for `alpha < 1`.
4. **Sparse menus and zero indivisibility gaps are different.** Carathéodory
   bounds representation support, not discovery by an arbitrary top-K rule or
   pure implementability. The two-hour example in the theory note has all feasible
   schedules already in its two-column menu, yet its pure cost is1/2 versus
   convexified cost1/4. Menu approximation error is zero while the indivisibility
   gap remains1/4. The official
   [EUPHEMIA description, §5.4.2](https://www.nemo-committee.eu/assets/files/euphemia-public-description.pdf)
   retains acceptance restrictions; a fractional fleet mixture is not automatically
   an executable exclusive-group order. At-most-one block acceptance also does
   not enforce the exactly-one complete schedule needed for mandatory service;
   a feasible outside option/fallback and the service obligation must be mapped.
5. **The welfare ladder is a hypothesis-generating result.** Reported3.74 and
   25.97/79.8 gaps concern particular historical synthetic regimes and absolute
   system-cost units. They do not show universal near-efficiency of strategic
   fleets. Test normalized losses, the fleet-size/charging-cost decomposition,
   supply curvature, competing fleets and tariff/physical shifts before making
   a broad managerial claim. Do not introduce every extension into one paper.

## Concrete continuation, in order

1. Correct the small canonical-accounting initializer and preserve the stopped v4
   package. No numerical retry is authorized by this referee discussion. A future
   launch needs its own prospective decision and fresh namespace, carrying all
  1518.4011370494984 spent seconds and the approved bounded resource policy.
2. Finish trustworthy recovery/replay and a matched learned-versus-classical
   comparison. Current ML quality is an empirical question; fit/AP or small-case
   implementation success cannot answer it. Fix the end-to-end baseline first.
3. In the next prospective scaling design, separate trip count, time resolution
   and actual economic dimension. Use public/synthetic bases, paired seeds and
   grouped variants; preserve physical energy, horizon and supply-cost units when
   refining time bins. For a continuous power-cost density
   `a P + beta P^2/2`, energy variable `E=P*dt` gives interval cost
   `a E + beta E^2/(2dt)`; retaining the same energy-quadratic coefficient while
   changing `dt` changes the economic problem. Record oracle time, total calls,
   recovery/replay, full bound quality and failures, not just clean calls.
4. Develop the narrowly valid fixed-point/two-schedule propositions, then identify
   what additional structure yields an empirical prediction worth testing on
   independently generated timetables. These elementary proofs themselves are
   not claimed as a new contribution. A finite catalog needs global omitted-plan
   checks before it speaks for the original fleet's full feasible set.
5. Keep exclusive-group implementation as a bounded economic extension, with a
   precise order/payment/allocation mapping and distinct menu, integrality and
   price-support errors. Do not turn it into an unsupported truthfulness or
   guaranteed-gap-closure claim.

Recommended paper anchor: explain when indivisible fleet schedules resist price
support, and test whether price-aware proposals reduce the work of verified
coordination relative to strong nonlearned methods. Stabilization is an optional
component to earn its place. If learning adds no matched benefit, report that and
reconsider the algorithmic anchor; a venue aspiration is not a result.

Protected A6/B3/confirmation outcomes and sealed DEV/TEST/GIRO stay closed. No
cluster/solver/model runs, new data intake, current native retry or budget change
was performed for this assessment. Old source/result branches remain intact.
