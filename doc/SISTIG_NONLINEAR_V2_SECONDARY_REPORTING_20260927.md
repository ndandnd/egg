# Nonlinear attempt 2: secondary reporting decision

27 September 2026. Lead decision after independent numerical and scope review.

## Decision

Job 559907 completed, but **the prospective strict-budget outcome is FAIL**.
Aggregate exact hull polishing took 5.190904918592423 seconds against the frozen
5.0-second cap. The final non-preemptible step crossed the remaining allowance.
Neither the deadline nor the original outcome is revised. No third attempt,
budget increase or new experiment is authorized by this decision.

The independent reconstruction separately **passes as conditional numerical
evidence**. The archived intervals may be reported only as an **off-protocol
secondary diagnostic**, with the timing deviation visible in the table and figure.
The planner remains bounded, the hull remains budget-exhausted, and the fresh
own-price response meets its declared numerical certification policy. Solver MIP
lower bounds are conditional on the native solver; numerical physical replay and
exact arithmetic on saved column projections do not turn them into exact global
physical proofs. There is no overall protocol or experimental PASS.

The signed planner-minus-hull interval is approximately [-46.1607063, 105.9931768],
so the gap remains unresolved under the frozen five-unit resolution. The own-price
regret interval is approximately [211.9863485, 211.9863505] and belongs only to the
named time-limited planner incumbent. It does not prove regret of a physical
optimum, a positive public-case gap, absence of price support at the optimum,
operational savings or a prospective runtime advantage. Displayed interval bounds
in the manuscript must be rounded outward. Exact endpoints remain in the report.

The separate ideal-model exact rational enclosures keep their own provenance and
scope. Do not silently combine an ideal exact lower bound with a tolerance-qualified
native upper bound into an alleged exact enclosure.

## Evidence and checks

- Execution source: `e23a653dcd77b6ce02eb0af5e544fea7edab9eca`.
- Frozen input: `eb1d9f5dc8b8f7f1561c21dd8f8cad6105f8cfbc272c23b8c8a334e6a626f352`.
- Raw manifest: `68032692ea5c5b349115bd6bd64740f0bd799fac9a8a4dcdf09462a844901cf9`.
- Independent audit manifest: `2edb2a60a1efdaf37159d6934e317700953e5013284517d5139fc9a18e726e61`.
- Full report: `dc1b176371cd5295d9bfcfd562b7cb69aaa8c3026c5c3a344a023d83a8027598`.
- Public-copy report: `1339fa71325437378c335ff6bb2ff2eefb1c06ef8576a5c92b28437c754d9987`.
- Public omission manifest: `facff4a3b2d6c38d0ce01e5cdaf0789b080ec30da5e9f621a026145763410137`.

The lead verified every hash/size in the 13-file audit package. Independent review
reconstructs two planner calls, three hull pricing calls, three master calls,
three physical columns, 17 exact polishing steps and one own-price call, including
all recorded model rows, physical replay, mixture and endpoint arithmetic. Six
targeted corruptions were rejected. The strict timing failure remains preserved;
REVIEW.md lists the three timing assertions separated only for diagnostic arithmetic
and the source-consistent terminal LimitReached sequence. Mathematical, source,
call-count, step-count and bit-count checks remain enforced.

Public Git retains 28 unchanged scientific/control entries, the original manifest
and the later wrapper. Only three complete licensing-only stdout files are omitted
by exact path, size and hash. The complete local/cluster archive stays intact.
The explicit public-copy audit passes, default full mode rejects that subset, and
a missing scientific input is rejected. Terminal scheduler receipts are preserved
under `research-20260927/launches/nonlinear-v2-job559907/terminal/`.

## Reproduction note

The sealed review's sample `--out` names an existing report and therefore correctly
refuses to overwrite it. For a full-archive rerun, use a fresh output filename in the
same review directory; never overwrite the sealed report. In a public checkout, run
`python3 research-20260927/agent-notes/nonlinear-v2-result-review/test_public_copy_mode.py`
from the repository root. It builds an ephemeral exact public layout and validates
the pinned omission policy without invoking a solver. Review scripts require the
pinned historical Git blobs. Keep their diagnostics separate from the sealed files.
