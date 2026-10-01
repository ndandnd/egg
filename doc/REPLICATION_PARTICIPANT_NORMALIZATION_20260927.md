# Replication: explicit participant rights and incentive normalization

27 September 2026. Principal-researcher derivation from the already audited
replication family. This is a new interpretation/proof check, not a new frozen
experiment or an empirical multi-operator result. Independent review passed; see `REPLICATION_PARTICIPANT_NORMALIZATION_REVIEW_20260927.md`.

## Question and explicit alternative institution

The existing family treats all replicated services as one price-taking operator.
Its whole-operator regret can approach a positive constant while per-bus regret
vanishes. A reviewer can reasonably ask what happens if market growth instead
adds small independent participants. Make that question precise: partition the
2n services into n identical A/B service pairs, each owned by a separate operator.
Give each operator its own one early 10 kW connector and one terminal 30 kW
connector, the same 20 kWh batteries and permission to use one or two buses.
These are explicit reserved resource rights. There is no unallocated shared
charger whose unilateral availability is being assumed.

Each pair can choose the nominal one-bus schedule with early/late energy (10,20)
and intrinsic cost 7, or two buses with early x in [0,10], terminal 30-x and
intrinsic cost 14. The participant consumes all service energy and finishes
fully replenished. Supply is shared through the same scaled cost
F_n(E,L)=4E+(E²+L²)/(10n). Keep the original price-taking convention: alternative
plans are evaluated at the posted price, without internalizing their price effect.

For one bus, the battery trace is 20 → 5 → 15 → 0 → 20. For two buses, the A-only bus buys x early and 15-x terminal kWh; the B-only bus buys 15 terminal kWh. Serving their terminal sessions sequentially at 30 kW takes (30-x)/30 hours, at most the reserved hour. Thus the entire continuous two-bus interval is physically feasible, including its endpoints.

The audited physical optimum has m nearest to 27n/40 one-bus pairs and n-m
zero-early two-bus pairs. Write delta=m-27n/40. Its own aggregate marginal price
is p=(4+2m/n,6-2m/n). For all these minimizing integer choices m/n>=1/2; at n=2
there is equality. Hence the two-bus price response has x=0 (or any x at the
equality), because p_early-p_late>=0. Its private value is 14+30p_late, and the
one-bus value is 7+10p_early+20p_late. Their difference is exactly

`one-bus value - two-bus value = 40m/n-27 = 40 delta/n`.

Therefore an operator assigned one bus has regret max(0,40delta/n); an operator
assigned two buses has regret max(0,-40delta/n). Since |delta|<=1/2, every
participant's regret is at most 20/n, tending to zero. This upper bound concerns
one A/B service pair with its reserved connectors; it does not describe the
unrestricted whole-fleet operator's absolute incentive.

Summing the actual participants gives

`R_n = m max(0,40delta/n) + (n-m) max(0,-40delta/n)`.

This equals the previously calculated whole-operator regret for the symmetric
replication family: all participants' best responses are simultaneously feasible
under their reserved connectors, and separable private costs add at fixed prices.
There is no claim of this equality for arbitrary fleets or shared-resource games.
Along n=40k+1, delta=13/40 and m=(27n+13)/40, so the m one-bus operators each have
regret 13/n. Their total is 351/40+169/(40n), although the largest individual's
incentive vanishes. At multiples of 40 every regret is zero. At n=20, m=13/14,
each dissatisfied participant has regret 1; there are 7/14 of them, explaining
both saved whole-fleet regrets without discarding either planner tie.

## Exact consistency check and interpretation

Exact Fraction arithmetic reproduced this sum for all 88 physical optimizer
records at all 86 archived sizes, including both ties; no raw result was changed.
That finite check supports transcription, while the algebra above supplies the
general result. It does not make the resource-rights interpretation an observed
market or a prospectively selected experiment.

This qualification should accompany any strong rhetoric about nonvanishing
incentives in large markets. The growing whole operator has an O(1) absolute
incentive along a subsequence, whereas each explicitly bounded participant in
this alternative partition has O(1/n) regret. The distinction is consistent with
classical aggregation/convexification logic, not a counterexample to it.

## Literature check and access scope

Kerdreux, Colin and d'Aspremont, *An Approximate Shapley-Folkman Theorem*,
arXiv:1712.08559v3 (1 July 2019), describes how aggregation of bounded nonconvex
sets supports finite-sum duality-gap bounds. Its primary abstract was inspected:
<https://arxiv.org/abs/1712.08559v3>. This is contextual attribution, not an
assertion that this paper proves our specific fleet regret formulas. The introduction and §§2–3 of the primary PDF were subsequently inspected; the later approximate sampling proofs remain unreviewed. The classical finite-dimensional summand bound is context, not an automatic statement about every unnormalized incentive. Starr's 1969 *Quasi-Equilibria in Markets with
Non-Convex Preferences*, Econometrica 37(1),25–38, is a relevant antecedent;
the author-hosted PDF at <https://econweb.ucsd.edu/~rstarr/Non-Convex%20Preferences.pdf>
was located but timed out in this check. Do not describe that source as fully
reviewed on the basis of its search snippet.
