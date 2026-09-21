# Exact exploratory two-slot experiment

Scope frozen before first run on 21 September 2026. This is a deterministic
finite duty-menu model, not a new EVSP population, holdout or statistical test.
No existing experiment seeds, raw data, protected outcomes or solver licenses
are used. It runs locally with one Python process and exact rational arithmetic.

Each participant must allocate its positive energy block wholly to one of two
slots. Each choice may carry an intrinsic cost. Supply cost is
F(L)=a dot L + b ||L||^2/2, with b>0. Enumerate all binary joint profiles; solve
the convexified objective analytically on the lower hull of (early load,cost).

Run 36 homogeneous cases: N=1,...,12 crossed with (unit energy,fixed slope),
(unit energy,slope1/N), and (energy1/N,fixed slope). Run54 heterogeneous cases:
N in{4,6,8}, three energy patterns, two cost patterns, three linear-price offsets.
Report exact physical/convexified costs and gap, minimum aggregate own-price
regret, minimum maximum individual own-price regret, and supplier/fleet lost
opportunity costs at the supporting price. Verify all physical-profile regret
bounds, zero-gap/support equivalence, and price-taking participant regrouping.

One separate shared-capacity witness has two unit participants, early-slot
capacity1, a=(0,2), b=1. Distinguish unrestricted independent menu deviations,
residual-capacity feasible deviations (a generalized game), and a capacity
scarcity price. Do not infer decentralized support from joint-feasible gap=0
without declaring the individual deviation sets and all priced resources.

The results are explanatory examples and exact finite checks. Homogeneous
closed forms provide independent validation; non-author review must check the
heterogeneous hull solver and the economic interpretation. No claim of novelty
is made for classical convexification, regrouping or scarcity-pricing facts.
No runtime-speedup claim is supported by this solver-free experiment.
