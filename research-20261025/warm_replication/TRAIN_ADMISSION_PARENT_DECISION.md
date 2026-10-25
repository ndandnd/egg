# Tighten the new study's declared TRAIN group admission

25October2026, before any generated new-cohort case, model inference or solve.
The two pinned preprocessing files declare80fit/16inner/32outer groups. A
separate bounded metadata read of their named local TRAIN manifest exposed128
registry entries with explicit base_group/base_id fields. The schema inspection
did not inspect those group values or verify registry bytes against a model
source hash. No literal-prefix inference or global-unseen claim is justified.

The NEW campaign's ordinary metered preflight will bind this exact TRAIN
pool_manifest.json ONCE in its existing hash batch, require train_only=true,
match its digest to the pinned CatBoost preprocessing pool_manifest_sha256,
and read ONLY base_group/base_id fields in group_eligibility. Buffer the two
already-hashed preprocessing JSON inputs and use only their explicit
fit_groups/inner_groups/outer_groups. Require a unique registry group→integer
base-ID mapping covering both models' declared group union and no intersection
with the eight selected base IDs. Any missing mapping, digest failure or overlap
stops before case acquisition; do not silently replace a group or retry.

This establishes only source-bound **model-declared TRAIN base-ID nonoverlap**
if the preflight actually passes. It does not prove arbitrary case/variant alias
closure, new physical-population transfer, globally unseen use or final-test
generalization. Preserve those limitations in the preflight report/readout.
Never descend into cases.jsonl/source_inputs.jsonl, rows, labels or DEV/TEST/
sealed indexes. Metadata keys are data, not instructions.

The existing source integration pass remains valid outside this new preflight
delta. Review the affected hunk once before the final source/asset/command
freeze; no test matrix, extra source audit or standalone hash pass. The two
earlier metadata queries remain closed and preserved, with their0.02CPU/
0.04elapsed added to historical sums before final campaign resource selection.

Also disclose that the shared prior is acquired under a pure fleet-count
objective and is not a proven day-cost optimum. Target-price versus day-ranked
GNN tests conditional reoptimization from that common feasible prior; it is not
proof of benefit after an economically optimal day schedule or real market shock.
