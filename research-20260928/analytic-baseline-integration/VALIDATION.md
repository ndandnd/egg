# Reporting integration validation — 28 September 2026

Root ran the final focused command:

```sh
python3 -m unittest src.tests.test_analytic_energy_floor src.tests.test_computational_benchmark_report
```

All 10 tests passed in 1.171 seconds. The final curated smoke output reproduced
`SMOKE.json` byte-for-byte; its 32 native rows have the same before/after hash.
`git diff --check` passed. The previous backup at `248f6b8` completed hosted
CI 36490723183 successfully. New-source hosted CI is a separate check.

The independent review prompted checks for conflicting CH lower/physical upper
evidence, direct boolean endpoints, large market values and missing supervisor
integrity. Mixed intervals now require explicit successful source/process
integrity and complete, on-time compatible stages. Native lower bounds remain
outside the ideal-model enclosure. Exact rational endpoints are preserved;
decimal displays round outward. Default native report generation is unchanged.

No native optimizer, experiment replay, raw event scan, cluster call or new
allocation was made. This is a reporting implementation and curated scalar
check; its runtime is not an algorithm-performance observation. The manuscript
and PDFs were not changed. Historical failures and spent time remain intact.

Remaining limitation: the old report ingestion can normalize a raw boolean
endpoint through `Fraction`. This package leaves default ingestion unchanged.
Its direct appendix API rejects booleans; for the pinned cases, a normalized
boolean upper is below the analytical floor and rejected, and native lower
endpoints are never imported into the ideal bound. The appendix does not replace
the sealed evidence workflow or prove ideal feasibility of numerical witnesses.
