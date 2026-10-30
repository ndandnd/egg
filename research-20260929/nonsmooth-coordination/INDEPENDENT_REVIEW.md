# Independent check of dispatch coordination and quadratic replay

29 September 2026. Reviewed `paper/latex/generation_dispatch.tex`,
`replay_subgradient.py`, `results/quadratic_summary.json`, and all 20,000 rows
of `results/quadratic_trace.csv`. This is a mathematical and deterministic
trace check, not a new optimization experiment.

The dispatch section's signs are correct. Dualizing `L=e(x)` gives
`Q(p)=V(p)-G*(p)`. An exact fleet minimizer contributes `e(x)` to a
supergradient of concave `V`; an attained maximizer of `p·s-G(s)` contributes
`-s` to a supergradient of `-G*`. Hence projected ascent uses
`p+=α(e(x)-s)`. The displayed projection proof yields the stated
best-iterate bound when `P` is closed convex, contains an unrestricted
maximizer, and the selected supergradients are uniformly bounded. With
`α_k=0.5/√k`, its numerator has a logarithmic squared-step sum and its
denominator grows as `√K`, giving `O(log K/√K)` for the best dual value.
Neither that bound nor this finite trace proves last-price or physical
schedule convergence. A balanced exact fleet/supply response at a common
price would force `D=CH`, so the positive-gap caveat is also correct.

The analytic replay preserves the complete two-bus choice
`(x,30-x), x∈[0,10]`: it selects `x=0` when `p_early≥p_terminal` and `x=10`
otherwise, with a valid `x=0` tie rule. It compares that response against
the one-bus `(10,20)` plan. For the nonnegative quadratic supply, the
conjugate is `2.5([p_early-4]_+²+[p_terminal]_+²)` and its supply response is
`(5[p_early-4]_+,5[p_terminal]_+)`. These formulas, the projected update,
current dual values, running maxima, response counts, and switch counts
match every saved row to numerical precision. Every dual value is at most
the exact `CH=7591/80`.

The reported call-20,000 pre-update checkpoint is consistent with the trace:
price `(5.3412173,4.6587827)`, current dual `94.8300269`, best-so-far dual
`94.8874988`, one-bus share `0.6682`, and 38 switches in the last 60
responses. At the pasted note's `(5.50,4.50)`, independent evaluation gives
`V=149`, `F*=56.25`, and current `Q=92.75`; its claimed `94.887` cannot be
the current dual at that price. No manuscript correction was required from
this review. The new four-period generation example was still being
prepared by another agent and is outside this check.
