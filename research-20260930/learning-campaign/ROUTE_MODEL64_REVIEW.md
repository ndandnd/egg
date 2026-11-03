# Bounded review: 64-group route-model replay

The saved-model replay is internally consistent with `ROUTE_MODEL64_RESULTS.md`. It checks the 64-group pool digest, all task/result/wrapper identities, fit-only preprocessing, saved outer probabilities and labels, source membership, and group-level metric aggregation. I independently compared the reported aggregate and common-32 paired fields in `ROUTE_MODEL64_REPLAY.json` with the report: the displayed values and directions agree. Each learned model improves log loss over kind-frequency on all 64 groups. The report also correctly describes the common-cohort gains as modest and heterogeneous, and does not equate edge prediction with legal routes, lower operating cost, or optimal labels.

The one-source censor is retained: 64/64 timetables contribute, with 127/128 source fleets observed. Group metrics average the available sources within each timetable and give each timetable equal weight. The common-32 comparison is paired by base group, and the report distinguishes that fixed learning-curve diagnostic from a randomized sample-size estimate.

I verified that the old 32-group pool and current 64-group pool have identical dataset-receipt, case-table, and source-table hashes for shards 0–3, so the present common-32 comparison uses matching admitted inputs. The replay script now pins both pool manifests and the old replay, then checks the exact shared-shard lineage before the comparison; its lineage-only validation passed.

Disposition: no substantive result or interpretation blocker found. Review was read-only; no model fit or replay was run.
