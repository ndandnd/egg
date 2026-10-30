# Compact QP analysis: focused static review

25 October 2026. **STATIC REVIEW PASS — ready for the parent's frozen once-only
analysis command; no unresolved blocker found in the requested scope.**
One bounded source review of stable `analyze.py` and `ANALYSIS_DECISION.md`, using
the already established compact QP/warm-summary field contracts. No outcome
computation, source imports, execution, tests, hashes, replay, inference, solver
calls or source edits were performed. This review does not repeat engineering
or model audits.

## Narrow correction closed by delta inspection

Candidate-only feasible costs now require both a reported bill and
`helper.qp_candidate_admitted is True`. They do **not** require `qp_success`,
so a physically admitted nonoptimal candidate remains eligible. Any reported but
unqualified bill is retained separately as telemetry, not a feasible comparator.

The physical-candidate count and parent-timely/operational eligibility count now
have separate labels, as do their provisional subsets. This distinguishes a physically
checked candidate and an endpoint whose entire publication/readback met the
clock. Only those changed hunks were inspected after the initial pass. There was
no change to optimization, physics or completed outputs.

## Other requested checks

- **E0:** the script obtains `target_E0` from each valid common prior in the
  passed warm summary. That field is the exact late-tariff electricity component,
  not total bill, fleet cost, energy quantity or a candidate-specific denominator.
  Every old seed and both controls for a case use that same E0. Nonpositive E0
  stops qualification rather than becoming a free normalized zero.
- **Operational versus candidate:** selected operational cost uses the
  parent-admitted physical endpoint, or the pre-existing valid prior if no new
  endpoint is available. Helper `ObjVal`, `ObjBound` and raw objective fields are
  retained only in numerical telemetry. The last case's native OPTIMAL status
  cannot supply a physical candidate cost when extraction/admission failed.
  The intended eight operational endpoints versus seven physical candidates is
  an input distinction, not a new result recomputed by this review.
- **Missing-candidate denominators:** all eight assignments and three old seeds
  remain represented. A missing candidate is null, not a substitute native
  objective or an automatically dropped case. Candidate aggregate mean/median
  require all planned 24 comparisons; otherwise they remain null. Defined counts
  and signs remain descriptive, without an available-only mean replacing the
  planned estimand.
- **Units of comparison:** each single seed17 QP reference is reused against
  the three old solver seeds. The script forms four base-group summaries, each
  requiring all six size/seed values, and labels the 24 comparisons as repeated
  measurements rather than 24 independent QP runs. Nested sizes and scaled
  resources remain explicit; no significance or new generalization is claimed.
- **Interpretation:** native status/bounds are conditional numerical reports.
  Different backend/procedure prevents a speedup claim; energy changes do not
  isolate charging timing or learned-price value. Feasible cost comparisons do
  not establish a full-problem or exact physical certificate.
- **Accounting:** the closed pre-v2 cumulative base 7005.07 CPU / 7178.14
  elapsed-sum already contains attempt01's 0.72 / 0.92. The cumulative formulas
  add **only v2 and analysis** to that base. The shared QP-package formulas add
  v1+v2+analysis, exactly once each. External v1 charge is checked, the whole
  60CPU/90wall analysis provision is funded inside the existing package, and
  prepublication measurements are distinguished from the final external analysis
  meter. Historical guard/unknown actual review CPU remain separate.

The requested qualification/label delta is closed. No broader rereview,
numerical check or additional source gate was performed or is required by this
static note. Actual analysis output and complete external process accounting
remain observations for the parent's once-only command.
