# Six-cell joint economic-support development diagnosis

Use the six seed-1006 synthetic development cells and alternating market order
from the frozen numerical-QP hull attempt: 8, 16 and 24 services, each at
`source0` and `target`. The previous QP attempt supplies the completed
convexified-hull interval `CH`; this run does **not** recompute that stage.
Pin its curated collection, frozen identity and summary hashes, verify the
complete on-time evidence and same case/market identities, and retain its
separate source commit and job lineage. Neither family member is independent
test data.

For each cell, run physical nonlinear planning `D` on the existing compact
path-flow model with native GRB seed 0, one thread, 180 s coordinator wall,
160 s native phase, at most 16 tangent rounds and epsilon `1e-4`. After an
on-time replayed planner witness and bounds, run one physical fixed-price
response at the gradient of **that named incumbent's** load: 60 s wall,
45 s native phase, one round and epsilon `1e-4`. The response uses precisely
the same physical feasible set. Record both independent native intervals,
their nonnegative planning-gap enclosure, and the incumbent's own-price
regret interval. A response cannot establish regret at an unknown optimal
fleet. All native bounds retain solver and physical-replay tolerances; stored
fractions are not ideal-model proofs.

There are 12 possible children, serialized as planner then response for each
cell. Planner/response child hard caps are 210/90 s, each with at most 10 s
TERM and 2 s KILL grace. The worst case is 1944 s, inside the 2100 s
controller, 2200 s outer timeout and 2400 s Slurm allocation. Request one
CPU, 8 GB, exclude `scaglione-compute-01`, and disable requeue and retry.
Freeze and preflight on the compute node. Preserve every stage outcome and
spent time, including a missing or ineligible response; do not import a hull
status as the status of either new stage. Do not touch public, protected,
held-out or old frozen retrieval data.
