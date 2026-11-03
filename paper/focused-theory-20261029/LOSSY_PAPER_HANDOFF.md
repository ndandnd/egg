# Lossy section handoff

Only lossy.tex and this handoff were added. Parent may input lossy.tex in the body and invoke `\LossyProjectionProofs` once after `\appendix` for the complete proofs. Main/v2g were not edited. This is the independently reviewed candidate, not a new calculation, support criterion or implementation qualification.

Body-ready short paragraph:

> Common charging and discharging losses require a joint early/terminal load description: terminal purchases depend on both net early energy and exported throughput. Under the same common-window physics, however, cardinality-matching minima still determine an exact efficient frontier, consisting of at most two line segments per vehicle count. This reduces physical and convexified planning for coordinatewise nondecreasing supply costs to a finite segment set and its convex hull. The result preserves neither the complete physical projection nor the lossless scalar support criterion; negative prices, asymmetric settlement and general timetable physics remain outside its scope.

Symbols follow v2g: battery capacity B; service consumptions a_i,b_j; grid-side early/terminal budgets K,H; charging/discharging efficiencies alpha,delta; kappa=1/(alpha*delta)−1. The capped-idle statement is domination/equality of efficient values, not literal projection equality. No empirical/public37V2G or practical-magnitude claim is made. No imports, computation, compilation, tests or commits.
