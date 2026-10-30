# Prospective grouped column-discovery workload

Status: **STATIC design complete; focused review PASS.** No cases, hashes,
imports, tests, data reads or numerical work occurred. This directory is not
a launch manifest. All prior experiments and failed attempts remain closed.

STUDY_DESIGN.md is the selected policy. SYNTHETIC_SPEC.md fixes construction
rules and their limits. TELEMETRY_AND_CONTROLS.md names the existing APIs and
measurement caveats. REVIEW.md records the focused review and clarifications.
No new controller, replacement oracle, dataset or learned model was created.

The design has four deterministic base seeds, nested12/24 trips, unchanged
per-bus/station resources, independently acquired fixed/full banks, and48
assigned paid A0/F1/C1 stages. No outcomes may choose replacement seeds,
parameters or larger instances. A0 may fail; cached missing states remain.
Nonuniform power is preserved by using retained-bank selection rather than
claiming unsupported warm CG. Original grid pricing and realized physical
admission remain distinct.

The next executable development step is a minimal source-only implementation
in a NEW pricing_workload_pilot directory: synthetic constructor and thin
actual-oracle/cache caller using existing ownership and admission machinery.
Review the narrow constructor/price-revaluation/clock/provenance changes once,
then separately freeze exact source, generated-input fields, ordered cohort,
commands and funding before any generation/import/numerical dispatch. The
proposed7200CPU/10800wall budget is inclusive, not a command or reopened budget.
No new human budget answer is pending.

No Google Doc append is appropriate for this preparation-only package. No new
scientific claim, learning restart or neural impossibility conclusion follows.
