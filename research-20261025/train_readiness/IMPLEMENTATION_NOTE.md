# Metadata collector implementation boundary

Static preparation only. `audit_metadata.py` opens only the four literal paths in `WHITELIST`, plus the literal script/PROTOCOL/LAUNCH identity files. The source maps are stable; their permitted selected paths are represented explicitly in the source. Source/protocol/LAUNCH are hashed but never interpreted as commands or extra file permissions. Nothing inside metadata is followed. No JSON assets, model weights, rows or outcomes were opened to implement this collector.

Before any input read, a fresh exclusive `attempt01/receipt.json` placeholder is created. All seven exact files are stat-capped at8MiB each and32MiB combined before reading; each is read into its buffer once and hashed once. The three selected metadata pins are hardcoded. Registry identity reuses its computed digest and must equal the selected CatBoost preprocessing pool pin. Only the four JSON buffers are parsed. File changes during a read fail closed. No recursive filesystem discovery, substring filtering, referenced-file hashes or import pipeline exists.

The explicit projection reports root key names/types; features and partition identifiers; normalization presence/type/length ONLY; whitelisted global manifest declarations; declared digest maps; and the exact admitted-shard provenance fields. CatBoost selection loss/metrics, raw attempt evidence, registered_censor, free text outside named fields and normalization entries are excluded. Selection config is copied only as a flat scalar dictionary. Nested/unapproved value shapes are recorded unknown, never recursively dumped.

Eligibility VALUES are projected only for the union of the two declared FIT-group sets. Inner/outer lists remain identifiers only. FIT coverage reports matched, missing and ambiguous IDs without repeating the old partition-qualification matrix. Observed source names/counts are metadata availability declarations, not verified numeric tariffs, target differences or teacher quality. GNN preprocessing is not treated as a verified training-pool lineage pin merely because CatBoost pins a manifest. Missing keys remain unknown; no paths, partitions or provenance are inferred from names.

Parent's pre-freeze narrow addition summarizes the same allowed FIT fields into
known eligibility/count denominators, declared full-pair/incomplete/unknown
groups and a source-fleet sum only if every planned FIT group has a valid count.
No additional fields, files, readiness tests or model-quality criteria are added.

The standard-library process has body45CPU/60wall and total60CPU/90wall, one Python thread and an observed5GiB RSS bound. Final receipt publication occurs even after a caught failure and replaces only its owned placeholder. A pre-existing attempt cannot be resumed. The external meter must be added once to the prior closed19638.10CPU/20223.65elapsed-sum; historical guard/unknown review CPU remain separate.

The receipt deliberately does not assert model readiness, generalization, conditional label support, teacher optimality or alias closure. Parent freezes the literal whitelist/source and exact once-only command in LAUNCH after static review. This implementation note does not authorize dispatch, further row inspection, fitting or evaluation.
