# Reporting-only analytical energy-floor baseline

This bounded development package adds `src/egglab/analytic_energy_floor.py`
and an opt-in `--analytic-energy-floor` option to the existing
`src/experiments/computational_benchmark_report.py` report driver. The
default report is unchanged. The opt-in appends a separately labeled
`analytic_energy_floor_baseline` object to `report.json` and a compact
appendix to `comparison.md`; stage rows and `stages.csv` retain their native
bounds, statuses, call counts, and timings.

The pure baseline accepts only complete physical payloads identical to the
two pinned, independently reviewed public depot cases. It reproduces the
case identity, checks the reviewed flow and one-bus lineage hashes, verifies
the full-terminal/zero-monetary-travel/unit-efficiency contract, and checks
every market coefficient and cardinality inequality before returning an
exact ideal stored-input CH lower bound. Valid supply-price changes can be
evaluated without a native call. A synthetic or unsupported case is
unavailable. A native upper below the ideal floor, an inverted native
interval, or a hull lower above the smaller of the hull and planner uppers
is inconsistent and remains unavailable, never clamped. Boolean native
endpoints are rejected in the opt-in combination. Oversized market integers
fail closed; supported exact lower values use outward decimal formatting
without conversion to float.

Optional mixed intervals use the exact ideal floor with the current report's
complete physical planner and hull **upper witnesses only**, conditional on
their feasibility for the ideal model. Native lower bounds are not
transferred into the ideal model. The mixed gap lower is zero and its upper
is physical upper minus ideal floor. These values do not certify the native
MIP, change a native stage outcome, enter a pricing cache or MIP cut, or
support a runtime claim.
Mixed native intervals require an explicit successful supervisor source/process
integrity flag. Failed or missing integrity suppresses those intervals while
retaining the independent ideal baseline. The curated smoke copies this flag
from its recorded analysis and remains conditionally labeled.

`SMOKE.json` is a small curated development check made by
`smoke_reporting.py`. It uses the published frozen declaration and scalar
analysis, reads no event stream or raw solver variables, and makes no solver
call. It reports all 32 native rows byte-identical before and after the
opt-in appendix. The four reviewed floors reproduce the prior exact values;
the conditional changed-market gap caps are approximately 98.3611 and
117.6042 for depots 15 and 16. These caps still have zero lower endpoints.

Focused regression command:

```sh
python3 -m unittest src.tests.test_analytic_energy_floor src.tests.test_computational_benchmark_report
```

The focused tests cover exact reviewed values,
price-only recomputation, mismatch and stale-lineage rejection, invalid
markets and oversized numbers, default/native-row preservation,
failed-stage nonpromotion, boolean endpoints, and incompatible native bounds.
