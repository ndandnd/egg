# TRAIN metadata readiness — completed 25 October 2026

The metadata readout completed once after source/protocol commit `d962c8f2`
was pushed. All selected identities and bounded-read checks passed. This
establishes a useful paired-source substrate in the declared TRAIN metadata;
it **does not yet establish price-dependent target labels or justify fitting**.
No training, scoring, solver, replay, row-table or weight access occurred.

## What the measured readout found

| Declared metadata coverage | GNN FIT groups | CatBoost FIT groups |
|---|---:|---:|
| Planned unique FIT groups | 80 | 80 |
| Mapped unambiguously to TRAIN registry | 80 | 80 |
| Known source-pair eligibility flag | 80 | 80 |
| Eligible for both source labels | 79 | 79 |
| Observed source fleets | 159 | 159 |

The incomplete pair is `physical_v2_s10037`; it stays in the denominator.
Global TRAIN declarations are128 groups with observed sources,127 full pairs
and255 of256 intended source fleets. These are metadata availability counts,
not independently verified physical cases, source quality or target changes.
The data are grouped by timetable; paired tariffs and edges are not independent
statistical units. No old partition-qualification matrix was rerun.

All three selected preprocessing/metadata pins matched the completed study's
identities. The TRAIN manifest hash matched the selected CatBoost preprocessing
pool pin and declared `train_only=true`. Both selected feature schemas have17
columns. Fit-only transform vectors were not exported; only their structure was
read. GNN preprocessing supplies no training-pool pin or seed. CatBoost supplies
a pool pin, seed17, feature names and the qualification: historical TRAIN-bank
grouped CV, single feasible-incumbent labels, not optima or an independent
benchmark. Its hyperparameter selection loss/performance was not read/exported.

No missing/unapproved-shape exception arose in the selected projections.
The receipt's `unknowns=[]` concerns those parsing/projection exceptions; its
explicit `readiness_limits` still lists major unresolved scientific questions.
An operationally successful audit is not a positive model-readiness gate.

## Source contract versus observed supervision

The static source maps identify intended within-timetable source tariffs:
source0 has flat a=.20; source1 has a=.10 in periods18–21 and .30 elsewhere;
both have30 periods and b=1/900. They also identify day/late target tariffs as
different time windows. This is a **source-defined contract**, not verification
of the numeric historical source rows or all executed source versions. A blanket
assumption that the declared training design had only one flat tariff would be
incorrect; actual conditional signal remains unmeasured.

The intended target is binary membership in one cheapest observed replayed
source plan from a bounded catalog, using integrated system cost. It is not an
optimality, regret or pairwise price-preference label. Two available source
records can have identical target movements, or different movements because of
teacher search/availability rather than economically important price response.
Metadata cannot decide between those explanations.

Source inspection traces four direct linear-tariff features:
`window_price_mean`, `window_price_min`, `market_mean`, `market_spread` (zero-based
columns11–14). Noncharging/empty-window edges still receive global price
information. GNN propagates these edge features into node and message states.
A future blind branch must remove all four before graph encoding and fit its
permitted transform on FIT only; decoder-only masking is insufficient. No direct
b input is present. These are source dependencies, not new model-performance
measurements. See FEATURE_SOURCE_MAP.md and PROVENANCE_SOURCE_MAP.md for lines.

## Concessions and next decision

Still UNKNOWN: actual within-case numeric tariff/physical identity correspondence;
binary target disagreement and its economic relevance; per-label teacher quality,
effort balance and RNG provenance; full GNN training-pool lineage; cross-generator
alias closure; and the value of a matched trained-aware/blind proposal pair.
Do not infer them from paired-source counts or hash declarations of referenced
files. Those referenced files were not followed or verified.

The smallest next inquiry is a separately frozen **FIT-only paired target/support
audit**, not another ML fit or larger solver replication. First freeze exact
TRAIN table paths/pins, identity fields and FIT-only semantic access rules from
the existing source contract. Preserve all80 intended FIT groups,79 declared
pairs and the incomplete group; report actual valid pairs and every mismatch.
Measure target set disagreement within the same physical case, keep price and
teacher-search explanations separate, and do not invent an outcome-selected
threshold or call disagreement information value. No inner/outer performance,
sealed bank, teacher solve or model expansion follows. NEXT_FIT_LABEL_DECISION.md
is a design direction, not a launch manifest.

The failed eight-group useful-margin gate remains unchanged. This readiness
inquiry neither rescues it nor forces a learned contribution. A strong classical
policy remains a legitimate operational conclusion for the tested regime.

## Resources and preservation

Four metadata files plus three source/protocol/launch identities were buffered
and hashed once in one standard-library process. No referenced files were read.
External displayed meter:0.04CPU/0.27elapsed seconds; self CPU before publication
was0.045704s, illustrating centisecond display rounding. Retain0.06s as a
conservative phase CPU charge rather than rounding that observation down.
Observed prepublication peak RSS22,822,912bytes; one Python thread. This is
observed resource evidence, not an instantaneous memory guarantee.

See FINAL_RESOURCE_RECEIPT.json. Prior measured process sums and the separate
legacy conditional guard/unknown old review CPU remain preserved. No reset,
refund, restored historical compliance or exact whole-session CPU claim.
