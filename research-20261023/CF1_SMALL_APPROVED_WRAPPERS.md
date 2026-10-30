# Approved CF1 engineering40 wrapper bindings

The approved package uses policy `cf1-small-approved-v4`, carry
1509.9511370494984s from `comparison-binding-checks/accounting.json`, package
limit165s, and absolute endpoint1674.9511370494984s. This package alone uses
TOTAL1920/dispatch1740/shutdown180. Each launcher sets those three globals only
inside its `main` process and verifies the explicit approval before dispatch.
The approval's scope is one inspected40-trip CF1 mechanism task. The native
worker60/61/62.5s, supervision45s and analysis/finalization30s are governed by
`CF1_SMALL_APPROVED_PROTOCOL.md` and `CF1_SMALL_APPROVED_REVIEW.md`.

`run_cf1_small_approved_checks.py` is the latest reviewed
`run_comparison_binding_checks.py` with package, source inventory and test
bindings substituted. Its only executed test is
`src/tests/test_cf1_small_mechanism_approved.py`. The four inherited modules
`test_constructive_controls.py`, `test_comparison_native_adapter.py`,
`test_cf1_preparation_preflight.py` and `test_cf1_small_mechanism_preflight.py`
are hashed dependencies only. Its exclusive output is
`cf1-small-approved-checks/attempt01`; work10s, outer12.5s, inclusive hard cap15s.
A separate parent closure reserve5s is recorded; the parent retains its actual
or conservative positive charge within the same165s package.

`run_cf1_small_approved_freeze.py` is the reviewed small-mechanism freezer with
the approved package bindings. It requires the new check's complete passing
receipt and freshly reconciled `cf1-small-approved-checks/accounting.json`;
carry is never reset. Its exclusive output is
`cf1-small-approved-v4/freeze-attempt01`; work5s, outer7.5s, inclusive hard cap10s.
The explicit command must start with the wrapper interpreter and
`-m experiments.cf1_small_mechanism_approved freeze`, with absolute paths for
`--design`, `--checks`, `--accounting` and `--lock`. No solver is called by this
metadata command. Both receipt policies are `cf1-small-approved-v4`, revision4.

Required prospective artifacts, created by the parent only after review:

- `cf1-small-approved-v4/approval.json`: object with
  `policy="cf1-small-approved-v4"`, `hard_ceiling_s=1920`,
  `dispatch_stop_s=1740`, `shutdown_reserve_s=180`,
  `package_start_s=1509.9511370494984`, `package_limit_s=165`,
  `absolute_package_end_s=1674.9511370494984`,
  `analysis_finalization_reserve_s=30`, `supervision_reserve_s=45`, `tasks=1`,
  `trips=40`, plus the original explicit approval question and answer.
- `cf1-small-approved-checks/prospective-budget.json`: object with
  `initial_charge_s=1509.9511370494984` and
  `absolute_package_end_s=1674.9511370494984`; record the15s inclusive source
  cap, parent closure5s and package analysis/finalization30s explicitly.
- `cf1-small-approved-checks/command.json`: exact list of strings
  `[/absolute/repo/.venv-local/bin/python, -m, pytest, -q,
  src/tests/test_cf1_small_mechanism_approved.py]`.
- `cf1-small-approved-v4/design.json`: module-compatible design; its
  `package_budget.absolute_package_ceiling_s` must equal1674.9511370494984.
- `cf1-small-approved-v4/freeze-command.json`: exact list of strings beginning
  `[/absolute/wrapper/interpreter, -m,
  experiments.cf1_small_mechanism_approved, freeze]`, then the four required
  absolute-path flag/value pairs.
- `cf1-small-approved-checks/accounting.json`: parent reconciliation of the
  new passing gate, with cumulative `charged_cpu_s` and verified
  `evidence_hashes`, retaining all prior spend and closure charges.

The check inventory hashes all `src/egglab` and `src/experiments` Python files,
the executed and four inherited test modules, ownership helpers, both new
wrappers, this note, approved protocol/review, approval JSON, and prospective
source budget/command. The freeze verifies that closure and adds its design,
command, new check receipt/logs/accounting and approval bindings. Historical
proof inventories are verified separately and remain immutable.

The inherited `retain_error`, `cleanup_receipt`, `accounting` and `output_audit`
bodies remain unchanged. The sourcecheck `sample_owned` retains the reviewed10s
work deadline; the freezer retains5s. Absolute monitor deadlines, maximum0.25s
complete-sample gaps, RSS/memory checks, detached child registration, tri-state
group probes, bounded cleanup and leader reap evidence remain fail closed.
Charge stays maximum(elapsed allocation, sampled tree CPU, reaped children CPU)
plus supervisor CPU; monitor-child observations are retained. Unknown ownership
or accounting cannot pass. Inclusive caps are ceilings, never free credit.
Native admission must independently retain worker62.5 + supervision45 +
analysis/finalization30 =137.5s after actual source/freeze/parent spending; the
15/10s prospective ceilings do not promise admission. No retries or new shared
administrative allowance are introduced.

These files prepare source only. No launch artifacts, attempt directories,
fixture reads, metadata freeze, checks, native dispatch or commits are created
by this wrapper preparation.
