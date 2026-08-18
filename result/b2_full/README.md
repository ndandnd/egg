# B2 full-population results

Canonical artifact: [`20260818T140356Z/`](20260818T140356Z/).

This artifact joins the certified A2 and A3-A5 pilots with the 208-cell
expansion into exactly 256 matched method-cells (64 instances per method).
All cells certified within the 240-call budget and passed the provenance,
replay, completeness, solver-status, scientific-setting, and wall-accounting
gates.

The current A3-A5 variants reduce clean-master calls but do not amortize
their stabilized candidate calls: median total calls are A2 24, A3 30,
A5 32, and A4 34. See `SUMMARY.md` and `acceptance_status.csv` inside the
canonical artifact, plus `doc/DECISION_LOG.md` for the resulting research
decision.
