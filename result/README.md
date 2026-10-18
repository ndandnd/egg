# result

Distilled experiment evidence referenced by `doc/`. Raw JSONL remains on the
cluster; canonical CSVs, audit verdicts, checkpoints, revalidation evidence,
and provenance are committed here.

The latest certified measurement closeout is
[`RESULTS_OVERVIEW_20260816T180507Z.md`](RESULTS_OVERVIEW_20260816T180507Z.md).
It supersedes the pre-hardening August 14 snapshot for scientific claims; the
older snapshot remains available as an archival hypothesis screen.

The canonical closed-fixture delta-debugging artifact is
[`strict_two_cycle/WITNESS.json`](strict_two_cycle/WITNESS.json); its scope,
reproduction command, and theorem/evidence boundary are documented in
[`../doc/STRICT_TWO_CYCLE_WITNESS.md`](../doc/STRICT_TWO_CYCLE_WITNESS.md).
Its `MANIFEST.json` and `SUMMARY.md` pin the exact committed analysis code;
all three files are published together only after the code test gate passes.

Each experiment family uses `result/<experiment>/<UTC stamp>/`. Read the
snapshot's `PROVENANCE.md` before analysis and use `replay_effective_ok` as the
canonical replay field. The raw `replay_ok` value is intentionally preserved.
