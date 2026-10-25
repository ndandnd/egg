# TRAIN admission and conditioning-pool source delta review

25 October 2026. **STATIC DELTA REVIEW PASS: no unresolved blocker found.**
The preceding `SOURCE_REVIEW_QP.md` pass remains scoped to the previously reviewed
implementation. This note closes only the newly authorized TRAIN admission,
partition guard and descriptive conditioning-pool report. Parent must still bind
the actual sources, inputs, assets and command before any launch.

## TRAIN admission

Reviewed `run.py`'s last `INPUT_FILES` entry, `train_admission`, and the existing
preflight stream/capture integration, plus the owner's implementation note.

- The exact approved TRAIN registry path is appended last, preserving the older
  indexed inputs. It is consumed in the duplicate-checked, once-only source/input
  batch. No TRAIN row table or new audit/hash loop is introduced.
- Only the two already selected preprocessing JSON streams are buffered during
  the existing asset hash pass. Parsing occurs after all five selected asset
  digests verify; those files are not reread. Actual registry digest must equal
  the CatBoost preprocessing pin.
- The registry requires `train_only is True`, the expected list shape, unique
  explicit group keys and canonical nonnegative integer base IDs. Both models'
  actual fit/inner/outer group unions must be covered by that explicit mapping.
  Planned IDs must be disjoint from the mapped registry base IDs; there is no
  name-prefix inference or replacement cohort on failure.
- The final narrow guard rejects duplicate group IDs inside each model's
  partition and every cross-partition group-ID or mapped-base-ID intersection.
  It records duplicate/intersection lists, each partition's mapped base-ID set
  and effective count. Distinct variants sharing a base inside one partition
  remain allowed, while crossing partitions fails admission.
- Split or cohort-overlap rejection returns `passed=False` with diagnostics,
  saves exclusive `train-admission.json`, and raises before acquisition/native
  dispatch. Schema/pin/coverage failures raise directly. The preflight record
  includes successful admission and its stated proof limits.

This is **model-declared TRAIN base-ID nonoverlap and split consistency**, using
the supplied registry. It does not establish alias closure, generator/timetable
independence, global nonexposure or any empirical generalization result. No actual
registry values or model/asset contents were read in this review.

## Conditioning-pool report

Reviewed only `run.py`'s GNN/GNN_day pool metadata and `finalize.py`'s set comparison,
cell carry and 48-pair descriptive summary.

- Pool IDs and protected/rank-fill counts are copied from the already computed
  selection only for GNN/GNN_day. They remain outside the common B/K contract;
  no rescoring, extra solve or outcome-dependent selection is added.
- Comparisons require selected, unique exact-K flexible pools with common M/K.
  Missing/unselected/mismatched pools remain undefined with reasons. All 48
  planned case/seed pairs remain in the report; complete mean/median overlap and
  mean ranking room require all 48 observations.
- Jaccard and symmetric-difference counts describe the full flexible pool,
  including the shared protected Bw. They are not ranking-only overlap measures;
  reported protected and remaining ranking-room counts are necessary context.
- Pool exposure has no promotion threshold and does not alter learned-family or
  strong-QP gates. The GNN_day contrast remains inference-time conditioning of
  the same fixed model, without a training-information causal claim.

The current historical prefix 7064.41 CPU / 7239.65 elapsed-sum is metadata, not a
new-package charge; this delta adds no dispatch accounting. No project imports,
compilation, tests, hashes, asset/registry reads, inference, solver work, probes,
commits, source edits or new agents were performed by this reviewer. Source-only
readiness does not establish actual admission, runtime compatibility or a passed
campaign.
