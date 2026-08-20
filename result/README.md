# result

Distilled experiment evidence referenced by `doc/`. Raw JSONL remains on the
cluster; canonical CSVs, audit verdicts, checkpoints, revalidation evidence,
and provenance are committed here.

The latest certified measurement closeout is
[`RESULTS_OVERVIEW_20260816T180507Z.md`](RESULTS_OVERVIEW_20260816T180507Z.md).
It supersedes the pre-hardening August 14 snapshot for scientific claims; the
older snapshot remains available as an archival hypothesis screen.

Each experiment family uses `result/<experiment>/<UTC stamp>/`. Read the
snapshot's `PROVENANCE.md` before analysis and use `replay_effective_ok` as the
canonical replay field. The raw `replay_ok` value is intentionally preserved.

The bounded local-move column-proposer spike is at
[`column_proposer/20260820T174254Z/`](column_proposer/20260820T174254Z/).
Its independently replayed frozen result is **HONEST-NEGATIVE**: 0 of 32
global strict-improvement opportunities were captured (0 accepted among 150
feasible/replayed candidate columns). This closes only the exact
four-trip relocate/swap proposer under its recorded dual representatives; it
is not a claim about every dual choice or larger instances.
