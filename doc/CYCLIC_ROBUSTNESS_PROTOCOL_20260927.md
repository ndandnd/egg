# Frozen execution contract: cyclic reserve, loss and connector controls

This protocol adopts the 16 unique cases and full physical/economic definitions
in `CYCLIC_ROBUSTNESS_DESIGN_20260927.md`. The analytical design predicts nine
positive-gap, six zero-gap and one infeasible case. These predictions precede
execution and are not native-solver results.

Execute the exact rational driver `src/experiments/cyclic_robustness.py` only
after committing it, this protocol and the analytical design. It reads no
external data and imports no solver or earlier experiment implementation.
For every case it independently builds the feasible one-bus and two-bus early
grid-energy intervals, minimizes each continuous quadratic branch, constructs
the lower convex hull of every feasible endpoint, and minimizes every hull
edge. It reports infeasibility explicitly and retains both physical minimizers
when tied. It saves every feasible branch optimizer, the hull supporting
components, full per-bus SOC and explicit nonoverlapping terminal sessions.
All feasible endpoints receive physical witnesses. Evaluate the full endpoint
set for each physical branch optimizer's posted-price response and record its
own-price regret, common-hull-price fleet/supply LOC and exact dual identity.
Use the same globally defined nonnegative-grid-load supply cost for its
conjugate, not only the restriction to fixed total energy.

The fixed grid is the Cartesian product r={0,1}, eta={1,19/20}, early power
={10,11,12}, terminal power=30, plus nominal r=0/eta=1/early power10 at terminal
power={10,20,47/2,24}. There are no sampled parameter values or post-result
selections. All buses have battery20, start/end20, service energy15 each;
grid power and battery energy are distinct, with constant efficiency eta.
The operating cost is7 per used bus, and the supply cost in grid kWh is
4E+(E^2+L^2)/10 in every case. One terminal connector serves both buses
sequentially at constant aggregate power. The connector model has zero
switching time and no taper; those omissions remain explicit.

One local process; external wall cap30seconds; output directory must not
already exist. Record source/protocol/design hashes, Git head, Python version,
elapsed time and any failure. Preserve all first-run files. No recovery/retry
or native optimizer is authorized by this exact-run contract. Subsequent
native comparisons require their own frozen source and status/budget rules.

An independent non-author must reconstruct the physical intervals, hull,
energy conversion, SOC, connector use and selected arithmetic before these
outputs enter the manuscript as independently verified evidence. The design
author's algebra is valuable prior derivation, but is not a second independent
post-result review. The original 24-case result remains unchanged.
