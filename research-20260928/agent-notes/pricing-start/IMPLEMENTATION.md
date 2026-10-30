# Opt-in compact physical-pricing MIP start

The compact pricing API accepts `start_plan=` only when explicitly supplied.
The source must carry the exact physical case identity, schema, compact
formulation, native matrix, and extraction policy. The source is not mutated.
Its complete fleet undergoes independent `replay_native` validation of paths,
service coverage, charging sessions, resource capacity, continuous SOC,
market load, and intrinsic cost. `recover_paths` then checks the selected
movement graph. A bad source raises an explicit exception before model build;
there is no cold fallback.

After objective attachment, the start sets **every** compact movement binary
to 0 or 1 in declared case order and rejects an unexpected model integer
variable. SOC, interval charging, and market-load variables are continuous;
Python-MIP completes those itself. Setting `Model.start` means the hint was
submitted, not that the backend accepted it. The solver's own returned status,
incumbent, and lower bound still control extraction and `admit_bound`; an
unresolved call with a submitted start stays unresolved. No formulation,
objective, bound policy, certification rule, or default start behavior changed.

The pricing wall deadline is established before source validation. Validation,
model build, objective attachment, and start attachment have separate elapsed
times in the `mip_start_setup` event. Rejection and timeout events retain the
elapsed setup time and failing stage. The existing remaining-time guard stops
native optimization if setup or recording consumes the wall budget. The
`native_start` event records the backend runtime and read-only model seed for
both cold and started calls. Generating and selecting a source plan is an
offline cost that a paired diagnostic must account for separately. Supply
state changes alter the posted pricing objective, while the case and physical
feasible set used to validate the start remain identical.

Focused pure validation:

```text
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m pytest -q src/tests/test_native_pathflow_mip_start.py src/tests/test_native_pathflow.py
40 passed in 0.11s
```

One bounded CBC smoke used the synthetic `cyclic_case`, prices `[1,1,1,1]`,
one thread, a 5 s call wall cap and 3 s native phase cap. It returned
`certified`, admitted lower `36.999999`, upper `37.00000099999855`, with
0.23161 s total wall and 0.20787 s setup. The source was a separately replayed
one-bus physical plan from
`src/tests/test_native_pathflow_mip_start.py::known_fleet`. The native call can
be reproduced with:

```sh
PYTHONPATH=src:src/tests ../.research-venv-repaired-1176/bin/python - <<'PY'
from egglab import native_pathflow as pf, native_recharge as nr
from experiments.native_recharge_qualification import cyclic_case
from test_native_pathflow_mip_start import known_fleet
case = cyclic_case()
events = []
result = pf.solve_pricing(case, [1.0]*4,
    budget=nr.Budget(backend='CBC', threads=1, wall_seconds=5.0,
                     phase_seconds=3.0),
    start_plan=known_fleet(case), record=events.append)
print(result['status'], result.get('lower'), result.get('upper'))
PY
```

[SMOKE_RECEIPT.json](SMOKE_RECEIPT.json) preserves the
fixture, caps, backend library identity, seed, solver status, timings, and
event sequence. The smoke preceded the final pure-checked guard that rejects
any unexpected integer variable; no second native run was made. The receipt
reports solver start acceptance as unknown because the Python-MIP setter
does not expose an acceptance confirmation.

This package implements the core hint and its checks. It does not supply a
paired cold/start experiment, accept a speed claim, or connect the start to
the main hull coordinator.
