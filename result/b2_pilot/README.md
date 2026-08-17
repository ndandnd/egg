# B2 pilot artifact index

- `20260817T225235Z/` is the canonical corrected closeout. Its manifest
  verifies analysis commit `f64b7ce`; all 48 method-cells are certified,
  and clean/stabilized solver wall is partitioned exactly once.
- `20260817T194110Z/` is retained for provenance. Its certification,
  oracle-call, and total-solver-wall results remain valid, but its
  `wall_clean_s`/`wall_stab_s` split mixed wrapper and solver timing and
  must not be used. Use the newer artifact for every decomposition claim.

Raw run directories remain gitignored. Each artifact manifest records the
input file hashes needed to verify regeneration from the retained raw data.
