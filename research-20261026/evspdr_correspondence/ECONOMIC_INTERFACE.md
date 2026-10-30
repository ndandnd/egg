# Economic interface and what the learned result actually tested

Source-only correspondence, 26 October 2026. No historical objective or result is changed.

EGG has two local model paths. `instance.py`/`evsp.py`/`regimes.py` use the earlier
slot-load formulation, configurable initial/terminal SOC, direct/depot alternatives,
and separate posted-price, strategic and planner solves. `evsp.solve_fixed_sequences`
keeps ordered trip duties but permits direct/depot choices. Its docstring calls it
an EVSP-DR analogue, not an adjacent-oracle invocation. The recent learned and
native pilots instead use `NativeCase`/`native_pathflow`: one depot/connector,
shared time-profile resources and per-bus full initial/final energy. Neither path
should silently stand in for the current multi-station EVSP-DR capacity oracle.

For period grid energy L, background grid energy U and affine price a+b(U+L):

| Institution | Fleet energy objective | Native supply coefficients alpha, beta |
|---|---|---|
| Posted price p, fixed before fleet response | p'L | alpha=p, beta=0 |
| Strategic uniform-price payment | (a+bU)'L + b'L² | alpha=a+bU, beta=2b |
| Incremental integrated system cost | (a+bU)'L + .5 b'L² | alpha=a+bU, beta=b |

The last column calls the existing native expression `ops + alpha'L + .5 beta'L²`.
For the particular posted-price convention p=a+bU, all three coincide at b=0;
posted prices need not generally equal that expression. Preserve a,b,U,p and the
institution separately: transforming coefficients does not turn beta into the
original market slope or make a planner result a strategic-payment result.
Cross-value every admitted schedule under all three original formulas. Evaluate
any matrix-transformation residual explicitly; do not change physical tolerances.

Sources: `src/egglab/market.py:1–16,35–55,75–103`,
`src/egglab/regimes.py:24–29,116–153`,
`src/egglab/native_hull.py` (`Market`, `supply`), and the frozen
`research-20261026/economic_recourse_pilot/miqp_control.py:300–329` objective contract.
L and U are kWh per period; a and p are cost/kWh; b is cost/kWh². Under an
average-power marginal-cost model alpha_power+beta_power*P over Delta hours,
b=beta_power/Delta. A different slot length at unchanged b changes the model.
Synthetic cost coefficients are not empirical monetary or clearing calibration.

The recent warm GNN pipeline tested a-only scores under the system-cost lens
without an explicit background-load feature. That scoped experiment cannot
establish a result for every strategic-payment or station-capacity model. Changing
institution also does not guarantee a learning benefit. Its failed practical gate
remains unchanged, as do the strong classical comparisons and all crash fallbacks.

A concrete control gap is that fixed movement paths are a subset of fixed trip
duties: a duty may retain its service order while changing a direct/depot movement
and its charging opportunities. The earlier Instance solver already expresses
that distinction, but the recent native fixed-QP arm does not. The next diagnostic
will make the distinction explicit on one source-defined common native model,
using existing QP/MIQP/replay helpers. This is an intentionally restricted seam,
not a claim of multi-station EVSP-DR runtime equivalence or a revived old cohort.
