# Independent implementation review: nonlinear timing amendment v2

27 September 2026. **PASS** for the bounded implementation preflight described here. This is not a result audit, source publication, attempt-2 freeze, or launch authorization. No optimizer, cluster job, or attempt-2 output was created during review.

The reviewed source hashes are:

| File | SHA-256 |
|---|---|
| `src/experiments/sistig_nonlinear_pilot.py` | `0ac3a005edcfd2e43ef48abb1e480f0f1685855b3c3cb4a866dc91093d787f80` |
| `src/tests/test_sistig_nonlinear_pilot.py` | `369180a89207c50fcd8f8d22659b4c75b56a0e0b380281cbd715d0dd44920426` |
| `src/cluster/sistig_nonlinear_pilot.sbatch` | `73634a773837ab29b95a4aa7c0e7d56ce87067fba3cc20b4b2db186d5ea92e25` |
| `doc/SISTIG_NONLINEAR_PILOT_V2_PROTOCOL_20260927.md` | `18ba732518335bc623c15ffdaa63b72a41a1dccfafb032e475b021a65e8a79d4` |

## Review findings

The only production timing change is reducing native wall budgets to **225/1380/225 seconds** for planner/hull/own-price, leaving **15/60/15 seconds** inside the unchanged complete-worker caps **240/1440/240 seconds** for assessment and receipt work. The 180-second phase caps, 48 planner rounds, six hull pricing calls, eight masters, 48-column pool, polish/rationalization limits, one own-price call, child caps **255/1455/255 seconds**, 2040-second supervisor cap, and 2070-second batch shell timeout remain unchanged. Backend is still one-thread GRB. These reserves are budget allocations; the retained worker elapsed guard is still authoritative if native or assessment time overruns.

The exclusive output identity changes from v1 attempt1 to v2 attempt2. `freeze` checks the exact attempt2 path, admission, current source hashes and their Git blobs before creating output. The frozen record stores both timing maps and every complete stage budget; `_frozen` rechecks them along with source, admission, case, market, backend, and environment identities. The reviewed v2 protocol is in the source list, as is this implementation review. The protocol retains its candidate-time pending banner and prohibits attempt-2 freeze/launch; that restriction remains in force until root publishes a source commit containing this PASS review and authorizes a subsequent step.

The qualification gate remains the previously admitted same-source GRB physical-20 plus hull-8 package. I independently checked its current admission pins and hashes, 20/8 control counts, all-pass and unchanged-source fields, and the shared native-source hashes against current files. The v2 gate code requires the separate v2 review file to contain the literal `**PASS**`. It consumes only the pinned GRB qualification evidence; it does not treat attempt1's failed nonlinear output as admission evidence.

The original model/replay core remains byte-identical to the source pins in v1's frozen record at commit `80eb69544f568a7ed346f0d603004a10f61c481a`: `native_recharge.py` (`0067123a…`), `native_pathflow.py` (`9b8f5017…`), `native_hull.py` (`ef7b3ee5…`), `native_pathflow_hull.py` (`853e590c…`), `solver.py` (`4d5ea429…`), `sistig_native_case.py` (`f47a7a92…`), and `native_pathflow_hull_qualification.py` (`81171ece…`). The batch change only directs `OUT` to attempt2; it retains the one-CPU/8-GB request, reserved-node exclusion, no-requeue policy, one freeze, supervised launch, and existing shell timeout.

The focused pure checks passed **6 tests** covering the unqualified hold, timing-map/budget freeze and mutation rejection, retained raw output on routine-cap breach, and supervisor timeout/source-drift receipt behavior. `bash -n` passed for the batch script. No full qualification gate or solver test was rerun.

The independent review supports proceeding to source publication review, subject to the existing hold. Attempt2 is not yet frozen or launched, and the failed v1 attempt remains immutable and not scientifically admitted. A native wall reserve does not guarantee that a future stage will finish within its worker cap; such an overrun must remain a failed stage with its raw result and failure receipt preserved.
