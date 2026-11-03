# V2 semantic-bound and fresh-namespace delta review

25 October 2026. **STATIC REVIEW PASS — ready for the parent's deliberate new
attempt02, subject to the stated source/input freeze.** This is source-review
readiness, not a numerical result or an automatic retry instruction. No imports,
compilation, tests, hashes, solver calls, runtime/resource probes or commits were
performed. No source was edited by this reviewer.

The review compared `qp_control_v2.py` against immutable `qp_control.py`, and
`run_v2.py` against immutable `run.py`, then read `PROTOCOL_V2.md`,
`RESOURCE_DECISION_V2.md` and `LAUNCH_V2.json`. It did not repeat the v1 full audit
or inspect old outcomes/captures. The closed attempt01 cost and disposition are
accepted from the parent's supplied accounting, not newly measured here.

## Reviewed deltas

- `_bound_semantics` recognizes **LB <= -1e20 only on the lower side**, and
  **UB >= 1e20 only on the upper side**. Copying sends only those recognized
  sides to signed `GRB.INFINITY`; readback compares the same side-specific tags.
  Every other bound retains exact float-value comparison. The existing source
  NaN/order checks, dense original/copied index checks, continuous type check and
  fixed 0/1 routing guard remain. This is consistent with the documented native
  meaning of these sentinels, not a relaxation of a genuinely finite physical
  bound. [Gurobi 12 variable-bound reference](https://docs.gurobi.com/projects/optimizer/en/12.0/reference/attributes/variable.html).
- Counts of unbounded sides/variables, at most five raw/canonical examples, and
  a separate detailed offending-variable record are retained. Raw equality and
  canonical equality are distinct diagnostics. A non-equivalent finite bound,
  wrong index or wrong type still raises fatal `CopyContractError`.
- The helper diff otherwise changes only policy/documentation and corresponding
  bound-copy metadata. Nonzero row coefficients, RHS/senses, objective including
  the `.5` curvature factor, numerical tolerances, unchanged extraction/replay,
  raw/physical objective guards, provisional retention and the one-optimize-call
  contract remain unchanged from reviewed v1.
- V2 permits only canonical fresh `fixed_route_qp/attempt02`, both at launcher
  output creation and worker folder validation. Exclusive directory creation
  prevents resuming an existing partial attempt02. The current helper path is
  checked explicitly; attempt01 files are read as predecessor evidence and are
  never overwritten or resumed.
- The new preflight hashes only the predecessor preflight and five named new v2
  files. It verifies predecessor policy, the exact eight-case set, canonical
  saved-prior paths and presence of their inherited bindings. Old project/prior
  digests remain explicitly **inherited**, not newly verified hashes. This relies
  on the stated unchanged-byte freeze; it is not a fresh audit of old files.
- The same 1800 CPU / 2700 wall package retains attempt01's **0.72 CPU / 0.92
  elapsed** as nonrefundable carry. Dispatch funding includes that carry before
  the next 90-CPU worker provision; the wall timer/funding and final package
  totals also include it. Dispatch1620/reserve180, worker90 CPU, native52,
  inclusive60, cleanup3, one thread and observed5GiB remain unchanged. The v2
  launch command uses the new driver/helper namespace and distinct v2 logs.
- Protocol, resource decision and launch metadata agree on all eight original
  priors, one call per case, no new model/route search, no automatic retry and no
  numerical dispatch of the broader replication. The pre-v2 closed cumulative
  numbers 7005.07 CPU / 7178.14 elapsed-sum already contain attempt01. They must
  **not be added wholesale to a package total that also contains that carry**;
  those are overlapping accounting views. The historical conditional guard and
  unknown actual historical review CPU remain separate.

## Limits

No unresolved blocker was found in this delta. Actual public-library behavior,
matrix readback, optimal/provisional status, physical admission, deadlines and
resource closure remain observations for the one new run. The normalization
proposal does not establish the old failure's cause: the old offending variable
was not identified here, and new raw/canonical diagnostics must support any later
causal explanation. Missing or failed observations remain failures; neither a
passed source review nor a failed v1 attempt permits weaker physics or another
unrecorded optimization call.
