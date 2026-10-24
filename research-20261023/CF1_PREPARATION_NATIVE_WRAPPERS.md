# CF1 preparation native wrapper bindings

Two new explicit launchers preserve the reviewed supervision algorithms. No historical launcher is modified.

`run_cf1_preparation_preflight_checks.py` copies `run_cf1_preparation_repair_checks.py`, changing only policy, input/output paths, selected test module, source inventory and absolute allocation constants. It executes **only** `src/tests/test_cf1_preparation_preflight.py`. The inherited `test_comparison_native_adapter.py` check binding and its `test_constructive_controls.py` fixture dependency remain hashed, unexecuted legacy closure; the new test imports neither. Carry is1416.3727097992353s from `cf1-preparation-repair-checks/accounting.json`, administration0, worker limit10s, cleanup/outer limit12.5s and inclusive planning15s. The exclusive output is `cf1-preparation-native-checks/attempt01`.

`run_cf1_preparation_native_freeze.py` copies `run_comparison_native_freeze.py`, with the new policy/path/module bindings and explicit package reserve. Work7.5s and outer10s are unchanged. It reads the actual carry from the new check's accounting and requires its complete passing source-bound receipt before launching this metadata-only command from `cf1-preparation-native-v2/freeze-command.json`:

```text
.venv-local/bin/python -m experiments.cf1_preparation_preflight freeze --design research-20261023/cf1-preparation-native-v2/design.json --checks research-20261023/cf1-preparation-native-checks/attempt01 --accounting research-20261023/cf1-preparation-native-checks/accounting.json --lock research-20261023/cf1-preparation-native-v2/lock.json
```

The command JSON contains absolute paths and the same interpreter as the external wrapper. Exclusive freeze output is `cf1-preparation-native-v2/freeze-attempt01`. Its receipt policy is `cf1-preparation-native-v2`, phase `comparison_native_freeze`. `charged_cpu_s` is total charged allocation plus supervisor CPU. `source_hashes` is exactly the lock's code source map; `checked_source_hashes` separately retains the full verified check closure, and `freeze_input_hashes` binds checked inputs plus freeze design/command/accounting. No fixture generator, model or solver is called by this metadata command.

Both wrappers retain shared absolute monitor sample deadlines, early scheduling, the strict0.25s completed-sample gap, all known process groups, registered detached test children, tri-state existence probes, bounded cleanup and leader reap evidence. Primary failures and secondary cleanup/audit errors remain separate. Child CPU is charged once using the reviewed maximum of elapsed allocation, sampled tree CPU and reaped children CPU, plus supervisor CPU; the monitor counter remains a diagnostic and is not added twice. Cleanup, accounting and output-audit helper bodies are unchanged. The check's sample deadline literal changes from20s to its10s work limit; the freeze's7.5s limit is unchanged.

Both enforce the existing1800/1620/180 cumulative policy and the narrower165s prospective package ending1581.3727097992353s, retaining30s for analysis/finalization. Failed spend is retained; neither launcher retries. The parent records and reconciles full-wrapper external time, including interpreter entry and receipt-tail work, against the inclusive plans. No new administration allowance is introduced.

Parent invocation, with all six numerical thread keys set to1 and `PYTHONDONTWRITEBYTECODE=1`, is:

```text
.venv-local/bin/python research-20261023/run_cf1_preparation_preflight_checks.py
.venv-local/bin/python research-20261023/run_cf1_preparation_native_freeze.py
```

The second command is conditional on the first gate and the parent's new accounting. This implementation agent only wrote and statically read the policy/path transformations. It did not import the runtime, execute checks, freeze fixtures, launch native work or change historical evidence.
