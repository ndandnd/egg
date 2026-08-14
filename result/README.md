# result

Figures, tables, and experiment outputs referenced by `doc/`.

Conventions (to adopt when the first experiments land, per the experiment
ladder in `ref/context/HANDOFF_PRICE_MAKER_20260814.md` Section 8):
- One subdirectory per experiment family, containing the outputs plus a
  `PROVENANCE.md` recording: instance/input hashes, price/model parameters,
  random seeds, solver status and bounds/gaps, oracle exactness tier, code
  commit, and wall time.
- Raw bulky artifacts stay on the cluster; commit only distilled
  figures/tables/CSVs plus provenance.
