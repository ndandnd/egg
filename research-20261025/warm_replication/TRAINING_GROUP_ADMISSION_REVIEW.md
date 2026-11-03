# Training-group admission: declared lists are available; instance mapping is incomplete

25 October 2026. Bounded static review of identifier fields and schema in exactly
the following locked metadata files:

- `/Users/nadan/Documents/ChatGPT/egg/claude-local/v8/task00/inner_progress/fit_only_preprocessing_and_groups.json`
- `research-20261017/classical-training/attempt1/catboost/preprocessing.json`
- `research-20261017/classical-training/attempt1/catboost/metadata.json`

No model weights, preprocessing numeric arrays, training rows, labels, outcome or
metric values, protected indexes, or other dataset files were inspected. No
hashes were computed and no imports, tests, inference or generation were run.

## What these files establish directly

Both preprocessing files expose `fit_groups`, `inner_groups`, and `outer_groups`:
80 fit,16 inner,32 outer identifiers in the `physical_v2_s10000`–`physical_v2_s10127`
namespace. These are explicit model-associated group declarations, stronger
provenance for this question than a historical experiment-use index. Conservatively
consider the union of all three lists when discussing prior exposure, rather
than equating absence from fit alone with absence from selection or inspection.

The eight planned bases50604,50606–50612 and their declared
`scale:<base>:40` / `scale:<base>:80` spellings are not literal entries in these
lists. CatBoost metadata's `selection` schema identifies an inner-selection
criterion, but its value was not read or reassessed. The metadata also contains
`training_source_hashes` references to the GNN preprocessing file, source files
and a TRAIN pool manifest, and `pool_table_hashes` names `cases.jsonl` and
`source_inputs.jsonl`. The CatBoost preprocessing file has a
`pool_manifest_sha256` reference. These are recorded provenance links; this
review did not verify their bytes or open either row table.

## What remains unproven

The three files provide no inline crosswalk from their group strings to canonical
generator/base IDs, complete source case identities, size variants and aliases.
The GNN preprocessing schema itself contains feature/group/normalization fields,
without that crosswalk. A different namespace or numeric range therefore does
**not** prove that a proposed case is absent as a source, alias or variant of a
fit/selection group. The metadata supports literal declared-group absence;
cross-namespace timetable/variant nonoverlap remains **UNPROVEN from these files
alone**. It also cannot certify globally unseen use or independent evaluation.

Prior cohort inspection separately disclosed shared TRAIN-derived physical
regimes. Even a future canonical-ID nonoverlap check would not establish new
physical-population transfer, independence of the nested40/80 variants, or
generalization from eight deterministic development groups.

## One proposed metered preflight check

Before any new case solve, permit one metadata-only read of the exact manifest
named in CatBoost's recorded source references:

`/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/pool_manifest.json`

Use only generator/schema/version and group-registry metadata. Needed fields
are an explicit mapping from every declared fit/inner/outer group to its canonical
generator and base ID, with all size/variant aliases or case identities sufficient
to resolve the proposed scale keys. Check the complete alias/variant closure
against the fixed eight bases and16 planned case keys. Record which mappings
are present and the precise scope of any supported nonoverlap conclusion.
This is a requested schema, **not a claim that the manifest exposes it**.

If that single whitelisted metadata file lacks the crosswalk, preregister
`mapping_unproven` and retain the development/provenance limitation. Do not infer
a mapping from spelling, replace cases using outcomes, descend into
`cases.jsonl` / `source_inputs.jsonl`, or search training rows, DEV/TEST sources
or sealed indexes. Parent owns whether and how this check enters the existing
8-hour experiment budget and frozen manifest; no new data access or launch is
performed by this note.
