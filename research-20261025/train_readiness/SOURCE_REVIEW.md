# Selected-metadata collector static review

25 October 2026. **STATIC SOURCE REVIEW PASS: no unresolved blocker found.**
One bounded read of `audit_metadata.py`, `PROTOCOL.md` and
`IMPLEMENTATION_NOTE.md`; no execution, project imports, compilation, tests,
hashes, metadata JSON reads, assets, rows, labels, outcomes, inference, native
work, replay, commits or new agents. No source was changed by this reviewer.
This pass covers the collector contract, not actual metadata identities or
model/data readiness. Parent still freezes the exact operative command and
LAUNCH after review; LAUNCH was absent at this review, as expected before that
freeze, and the collector requires it at runtime.

## Boundary and evidence checked

- **Exactly four metadata paths:** literal GNN preprocessing, CatBoost
  preprocessing, CatBoost selected metadata and the named TRAIN pool manifest.
  The only additional reads are this script and literal PROTOCOL/LAUNCH identity
  files. No directory enumeration, model import, row access, subprocess or path
  obtained from metadata is executed or followed. Identity documents are hashed,
  not interpreted as commands or permission expansion.
- **Single bounded consumption:** all seven paths are duplicate-checked and
  stat-capped before input reads, at8MiB each and32MiB in aggregate. Each is read
  once for its recorded size and hashed once; inode/size/mtime and byte-count
  changes fail. The three hardcoded selected-metadata digests must match. The
  actual registry digest is reused for comparison with the selected CatBoost
  preprocessing pin, with no rehash. No verification of referenced digest-map
  files is implied.
- **Literal projections:** root key names/types are allowed schema evidence.
  Feature names, group identifiers, named scalar declarations, flat selected
  CatBoost configuration and declared digest maps are explicit whitelist choices.
  Losses, performance/predictions, raw-attempt evidence, registered-censor values,
  arbitrary nested values and normalization entries are not exported. Mean/scale
  and possible GNN pool/seed fields expose presence/type/length only. No
  recursive or substring-based value discovery broadens this projection.
- **FIT-only registry values:** registry item key names are schema-only. Actual
  eligibility records are projected only for the union of the two declared FIT
  sets, using literal fields for base/group identity, intended/observed source
  availability and eligibility. Inner/outer declarations remain identifiers.
  Missing or ambiguous FIT mappings remain visible; the collector does not
  repeat the completed study's partition or full admission matrix.
- **Shard provenance is metadata:** only literal shard/dataset fields and named
  digest strings are emitted. No source plans, teacher outcomes, health file,
  referenced receipt or raw-attempt payload is opened. Source names/counts
  cannot be promoted to actual numeric tariff values or conditional labels.
- **Unknowns remain unknown:** GNN preprocessing identity is explicitly not a
  verified TRAIN-pool lineage pin. The receipt leaves within-case numeric prices,
  conditional binary target variation, teacher quality, alias closure and
  matched-blind readiness unestablished. `readiness_qualified` remains false
  even when metadata checks pass. Source capability and metadata declaration
  remain distinct from verified raw-data truth.

## Failure, publication and resource semantics

The exact source path is checked and `attempt01` is exclusively created. An
incomplete placeholder precedes the input batch; a pre-existing attempt is not
resumed. Exceptions inside the audit preserve observed hashes/projections and a
failed check. Final JSON is written exclusively to an owned temporary path and
replaces only the owned placeholder. A hard interruption can leave the
incomplete placeholder/partial temporary file rather than inventing completion.
Failure before creating the attempt has no claim of a completed audit receipt.

The body uses45 process-CPU/60 wall seconds with startup included in its clocks;
the hard CPU ceiling is60 and final publication wall boundary90, retaining the
stated15CPU/30wall suffix inside the total. Publication switches away from the
body signal exception while preserving the hard limits. One Python thread and
observed peak RSS<=5GiB are checked; this is not instantaneous memory containment.
Final in-receipt resource values precede encoding/write/exit, and the external
meter remains necessary to charge the suffix once. Prior closed process sums
19638.10CPU/20223.65elapsed-sum and the separate legacy guard/unknown actual old
review CPU are retained without a reset or whole-session exactness claim.

No dynamic compatibility, selected-input hash match, successful publication or
actual resource compliance was tested here. A completed audit may establish
bounded declared provenance; it cannot admit a trained-aware/blind experiment
or positive label signal merely by completing successfully.

## Narrow FIT availability-summary closure

The parent's subsequent `FIT_source_availability` block and matching protocol/
implementation wording were inspected once, without reopening the rest of this
review. **PASS; no additional blocker.** It uses only already joined,
nonambiguous FIT records and the two already whitelisted availability fields.
Each model retains its full declared FIT and mapped denominators; only actual
booleans enter the known pair-flag denominator, with false and unknown group IDs
explicit. Only nonnegative actual integers enter the known observed-count
denominator, and their sum is emitted only when every planned FIT group has a
known count. Missing/ambiguous mappings remain unknown rather than zero.
The summary adds no input, hash, row access, quality/readiness gate or historical
partition matrix. Its interpretation stays declared availability, not verified
numeric tariffs, conditional target variation or teacher quality. Existing body/
total resource provisions and final unknown/readiness semantics remain intact.
