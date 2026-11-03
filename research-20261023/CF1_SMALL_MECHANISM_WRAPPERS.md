# Small CF1 mechanism wrapper bindings

These two new launchers are source preparation for one explicit engineering
mechanism package. Only the directly affected source check is eligible this
wake; metadata freeze and native dispatch remain disabled. Historical launchers
and failed80 proofs remain unchanged.
The mechanism case/policy/fixture/task contract belongs to
`CF1_SMALL_MECHANISM_PROTOCOL.md` and `CF1_SMALL_MECHANISM_REVIEW.md`.

`run_cf1_small_mechanism_checks.py` copies
`run_cf1_preparation_preflight_checks.py`, with policy/path/test/dependency and
allocation substitutions. Its sole executed test module is
`src/tests/test_cf1_small_mechanism_preflight.py`. The inherited qualified
`test_constructive_controls.py`, `test_comparison_native_adapter.py` and
`test_cf1_preparation_preflight.py` are hashed dependencies only; no historical
matrix is executed. The source closure retains all `src/egglab` and
`src/experiments` Python files to match the delegated native freezer's complete
code inventory. Its new note inventory is only the small-mechanism protocol,
review and wrapper note, plus the new freeze wrapper and check budget/command.
The inherited accounting proof closure is verified separately.

Authoritative carry is1503.9811370494986s from
`cf1-preparation-native-v2/accounting.json`, with administration0. Exclusive check
output is `cf1-small-mechanism-checks/attempt01`. Work is5s, outer allocation7.5s,
and inclusive planning10s. The full2.5s cleanup interval is preserved. Receipt
policy is `cf1-small-mechanism-v3`, revision3.

`run_cf1_small_mechanism_freeze.py` copies
`run_cf1_preparation_native_freeze.py`, with the same new namespace, module and
allocation bindings. It reads the actual reconciled carry from
`cf1-small-mechanism-checks/accounting.json` and requires its complete passing
source-bound check receipt. Its explicit same-interpreter command JSON is
`cf1-small-mechanism-v3/freeze-command.json`, representing:

```text
.venv-local/bin/python -m experiments.cf1_small_mechanism_preflight freeze --design research-20261023/cf1-small-mechanism-v3/design.json --checks research-20261023/cf1-small-mechanism-checks/attempt01 --accounting research-20261023/cf1-small-mechanism-checks/accounting.json --lock research-20261023/cf1-small-mechanism-v3/lock.json
```

The actual command JSON must use absolute paths and the external wrapper's
interpreter. Exclusive freeze output is
`cf1-small-mechanism-v3/freeze-attempt01`. Its work/outer/planning limits are also
5/7.5/10s, preserving2.5s cleanup. Receipt policy is `cf1-small-mechanism-v3`,
revision3, phase `comparison_native_freeze`. This metadata command must reuse the
explicit immutable fixture; it neither generates a case nor calls a solver.

Both wrappers preserve the reviewed ownership and accounting algorithms:
absolute sample deadlines, strict0.25s completed-sample gap, registered detached
children, tri-state existence probes, all known groups, bounded cleanup and
leader reap evidence. The `retain_error`, `cleanup_receipt`, `accounting` and
`output_audit` helper bodies are copied unchanged. `sample_owned` changes only
its work-deadline literal to5s. Primary and secondary failures remain separate.
Charge remains the maximum of elapsed allocation, sampled tree CPU and reaped
children CPU, plus supervisor CPU. Monitor-child CPU is retained diagnostically
and counted once through the reviewed observation convention. Unknown accounting
or ownership cannot pass.

The provisional package limit is115s, absolute endpoint1618.9811370494986s, inside
the existing TOTAL1800/dispatch1620/shutdown180 policy. Combined analysis and
finalization reserve is5s. These proposed values replace an earlier110s package
and25s supervision idea; they are not approved full launch clearance. Independent
review found that a successful40 mechanism may produce several captures and the
current per-task analysis is not preemptible, so5s final reserve is not yet
justified. The parent must reconcile interpreter entry and
receipt-tail work using positive-only external measurements; neither inclusive
planning value is free credit or a promise of numerical admission.

Native admission is separate and conditional on actual complete reconciled
receipts: remaining room must cover worker62.5s + supervision40s + combined
analysis/finalization5s =107.5s. Thus actual check plus freeze spend must be at
most7.5s at admission, and any additional charged prelaunch work reduces that
room. If it does not fit, stop with source/proof results and no native dispatch.
The10s planning cap for each preliminary gate does not override this condition.
No reserve is borrowed from shutdown or the8CPUh comparison envelope. Failed
spend is retained; neither wrapper retries.

The parent may explicitly invoke the check wrapper within its10s inclusive
source-only plan. A later metadata freeze/native package requires a robust
prospective reserve decision before either launch; passing the source gate
alone does not authorize them. The later freezer must recompute the selector
against the inspected50997/40 fixture because the old lock lacks selection
policy; it cannot reuse that metadata silently. This implementation
only wrote and statically compared source bindings. It did not import the new
runtime, execute checks, freeze fixtures, run a solver, alter historical evidence
or create a commit.
