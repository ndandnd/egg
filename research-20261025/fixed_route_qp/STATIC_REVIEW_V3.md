# V3 one-case primal-QP delta review

25 October 2026. **STATIC REVIEW PASS — ready for the parent's deliberate,
once-only attempt03 after freezing the reviewed bytes and exact command.**
No unresolved blocker was found in this bounded delta. No imports, compilation,
tests, hashes, solver calls, runtime/resource probes, source edits or commits
were performed. The seven successful v2 cases were not rereviewed or rerun.

Compared `qp_control_v3.py` with immutable v2 and `run_v3.py` with immutable v2;
read the stable `PROTOCOL_V3.md`, `RESOURCE_DECISION_V3.md`, `LAUNCH_V3.json`, and
only the five selected accounting scalars used from `FINAL_RESOURCE_RECEIPT.json`.
This does not repeat the old full audit or inspect raw/native outcome artifacts.

## Checks closed

- **Helper change:** the actual diff contains only the header/policy change,
  `qp.Params.Method=0`, its pre-optimize readback, and actual `Method` statistics.
  All semantic-bound, finite-bound, nonzero coefficient, matrix/objective,
  numerical tolerance, unchanged extraction/replay, provisional-retention,
  one-native-call and deadline guards are unchanged. Gurobi 12 documents 0 as
  primal simplex. [Gurobi 12 reference manual, Method parameter](https://docs.gurobi.com/_/downloads/optimizer/en/12.0/pdf/).
- **Exact scope:** runtime `CASES` contains only `scale:50603:80`, seed17. The
  original eight-case order remains a separate provenance constant. Preflight
  requires all eight inherited prior bindings and verifies their original
  canonical paths; selection of the last case retains its original ordinal008
  acquisition plan/replay/receipt, not the first prior. No solver or case-making
  loop revisits the other seven cases.
- **Fresh namespace:** launcher and worker require `fixed_route_qp/attempt03`;
  the worker uses canonical ordinal008 naming and checks the v3 helper path.
  Exclusive directory creation prevents resuming a partial namespace. Earlier
  attempts and their failed or successful outputs remain untouched.
- **Bindings:** one metered batch binds the v2 preflight, closed resource receipt
  and five new v3 files. Original project/prior digests and v2-fresh digests are
  preserved in separate inherited fields. There is no old source/prior hash loop
  or learned-asset access. The unchanged-byte freeze remains an assumption,
  explicitly not a fresh verification of inherited bytes.
- **Carry and budgets:** receipt fields have the numeric shapes and values the
  new preflight requires: shared carry48.88 CPU /50.65 elapsed, cumulative
  7053.23 CPU /7227.87 elapsed-sum, zero active workers. Shared funding/totals
  include the carry under the unchanged1800 CPU /2700 wall package,
  dispatch1620/reserve180. Fresh selected funding is separately120 CPU /180
  wall; it does not subtract or add the carry again inside that allowance.
- **CPU inheritance:** launcher soft30/hard90 plus existing SIGXCPU stop handling
  permits the child to set90/90 without raising an inherited hard limit. Selected
  dispatch funds current work plus worker90 plus closure15. The wall alarm clips
  to fresh180 or remaining shared wall. Final observed own-plus-waited-child
  totals are checked against both selected and shared limits. Conditional compact
  postprocessing15 CPU /20 wall must fit the actual selected remainder; it is
  not an additional allowance. External accounting still includes publication
  and exit omitted by self-receipt timestamps.
- **Command and scientific boundary:** the launch metadata agrees with these
  paths, carry, budgets and native52/inclusive60, one thread, observed5GiB and
  one-call limits. It describes a new exposed allocation-mechanism check, not an
  automatic retry, replacement of the old result, broader replication launch,
  training or a full-problem/physical optimality certificate.

## Accounting and inference limits

The cumulative base7053.23/7227.87 already includes the shared carry48.88/50.65.
A later cumulative sum adds only the **new v3 process and permitted readout**;
adding the entire carry-inclusive shared package to that base would double count.
The historical conditional guard and unknown historical actual review CPU remain
separate.

Method0 may select a different allocation, but this review establishes neither
representability nor the old offending charge's identity, magnitude or cause.
Actual method readback, numerical status, physical witness, timing and resource
closure remain observations for the deliberate run. Failed observations must
remain failures, with no extra call, weaker decoder or unrecorded follow-up.
