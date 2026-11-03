# Three-cover candidate pool: exposed-case competence gate failed

25 October 2026. The prospective one-shot pilot completed both cases normally;
both saved plans independently replay on the original physical case. The
prespecified competence target was met at40 trips and missed at80. No retry,
pool expansion, parameter adjustment or extra native call followed.

| Case | Retained/all movements | Flexible retained/all | Route-only paths in each cover | Replay-valid buses | Pool fleet bound/status | Native solve | Complete case |
|---|---:|---:|---:|---:|---|---:|---:|
| scale:50685:40 | 173/1507 | 93/1427 | 3,3,3 | 3 | 3 / OPTIMAL | 0.0930s | 1.5069s |
| scale:50605:80 | 273/6042 | 113/5882 | 3,3,3 | 24 | 24 / OPTIMAL | 0.7463s | 12.4408s |

The exact integrated system costs evaluated after these fleet-count solves are
674.56708485 and3283.59894794. Electricity cost was not the optimized objective.
All80/160 original boundary movements were retained. Three maximum-cardinality
matchings used travel time, single-vehicle charging capacity and deterministic
diversification secondaries; their unions contain53/99 trip pairs. Every original
parallel mode for those pairs was retained. No nonchronological mode was excluded.

**Interpretation:** the80-trip restricted native solve finished quickly and
reported a24-vehicle optimum. The known historical full-case feasible witness
uses5 vehicles. Subject to the solver's numerical optimality qualifications,
the selected pool itself excludes such compact solutions; additional search on
this identical pool is not the remedy. Its three-path topological covers do not
encode accumulated SOC, shared charging or physical implementability. The
native bound is restricted to the pool, never an unrestricted fleet certificate.

This does NOT establish that matching, conventional methods or their charging
proxies are inferior to learning. The80-trip pool retains only about1.92% of
flexible movements, whereas the historical GNN selector kept approximately30%
plus per-trip floors. Pool size is a major confound. These cases are exposed,
and objectives/seeds/allocations differ from historical ML runs. No matched
advantage, generalization, speedup or necessity of learning is claimed.

**Next decision:** before a more elaborate resource-constrained route generator,
freeze a separate candidate-density control using the same common backbone and
exact K for conventional charging-aware scoring alone and matching-union plus
that score. Retain the coherent covers within K and use a predetermined fill
order; do not select a successful density after inspecting outcomes. Keep this
failed sparse design unchanged. A route-generation redesign is justified only
after separating aggressive sparsity from the scoring/structure mechanism.
The larger ML comparison remains gated on competent conventional controls.

Whole process:14.54s elapsed and13.56s user+system CPU, within300wall/360CPU seconds.
The single finalization/archive process used0.92s elapsed/0.88CPU seconds. Startup,
pool construction, original-model build, one matrix inventory, bound changes,
native search, capture, extraction, independent replay and durable case output
are included. Raw large artifacts remain locally and losslessly in gzip for Git;
their original streaming hashes/sizes are in summary.json. No production source,
model, protected data or cluster state was changed. Historical accounting stays
separate and its unknown actual review CPU stays unknown.
