# The modest GNN edge mixes energy quantity and priced load shape

25 October2026. The new stored-energy diagnostic ran ONCE, with no model,
optimization, replay or raw-plan activity. All168 operational cells and72
paired contrasts were retained. Exact data:energy-diagnostic.json. Costs below
use prior late electricity E0; energy fractions use the comparator's own grid
energy. They are different denominators and are not interchangeable.

|Comparator|Mean GNN energy change vs comparator|Mean GNN cost advantage / E0|Lower-energy cells|Cheaper cells|
|---|---:|---:|---:|---:|
|CoverCA1|−0.7977%|1.2319%|15/24|20/24|
|CA1|−1.3930%|2.0258%|18/24|21/24|
|random|−1.0886%|1.5888%|20/24|23/24|

GNN uses less total energy than the unchanged common prior in24/24 cells
(mean relative change−9.0440%). Fixed-route QP preserves that prior's energy
to the reported numerical precision in all seven admitted QP cases. Thus the
large contrast against fixed-route charging does not isolate tariff adaptation:
it includes the value of changing energy demand through different connections.
The modest contrast against competent classical routing is the useful ML screen.

Quantity alone also does not explain every paired ordering. Against CoverCA1,
six repeated cells have cheaper GNN endpoints despite HIGHER grid energy;
14 have both cheaper cost and lower energy, three have both higher, and one
has lower energy but higher cost. Group50600's median energy change is+0.1479%
while its median cost advantage is+0.3558%E0. These are descriptive checks that
priced load profiles matter for some endpoints; they do not identify a causal
effect of price inputs to the learned model. All methods' downstream solvers
already use the target prices. Four base units with repeated sizes/seeds remain
four units; no significance, novelty, generalization or model promotion follows.

## Next decisions

1. Keep the frozen warm continuation result and CatBoost non-result unchanged.
   Preserve both conventional routing controls and all energy/cost components.
2. Resolve conventional QP admission with a new prospective one-case numerical
   mechanism design. Method0 primal QP simplex is the narrow existing-API option
   in EXTRACTION_FAILURE_DIAGNOSIS.md. Do not erase positive charge, widen replay
   tolerances or rerun the seven successful cases. This is not a cleared command.
3. Revise the HELD eight-new-group study to include the stronger charging control
   before freezing its actual launch. Retain paid budgets, common valid fallback,
   both classical routing controls and grouped paired comparisons. Target-price
   versus day-conditioned frozen GNN is an inference-conditioning diagnostic;
   a comparably selected trained tariff-blind control is still needed later.
4. Do not respond by adding architectures or surveying more literature. The
   immediate question is whether the small routing advantage and any information
   value survive competent controls on new groups, then resource/tariff regimes.

Numerical readout external0.04CPU/0.06elapsed inside the shared QP allowance.
QP package now48.88CPU/50.65elapsed-sum; closed reset cumulative7053.23CPU/
7227.87elapsed-sum. These rounded process sums do not measure the whole session.
Historical conditional guard2546.091499549272 and UNKNOWN actual reviewCPU remain
separate. Every old failure and gate remains preserved; no automatic retry.
