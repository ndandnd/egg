# Prospective pricing-start pilot runner

The runner declares exactly four development cases, two fixed-price queries and two
arms, with the protocol's counterbalanced within-query order. It performs no native
solve during `freeze` or `preflight`. Freeze is a one-time login-node action in the
clean, published execution checkout **before** `sbatch`:

```sh
PYTHONPATH=src python -m experiments.pricing_start_pilot freeze \
  --attempt result/pricing_start_pilot/20260928-attempt1 \
  --source-root /home/nc437/egg-solver-baseline-comparison-20260928/result/solver_baseline_comparison/20260928-attempt1
```

The attempt path must not exist. The batch script requires its frozen file and
checks it before calling `supervise`; it never recreates a freeze or overwrites
the exclusive attempt. It uses one CPU, 8 GB, one hour, one thread in native and
numerical libraries, no requeue, and excludes `scaglione-compute-01`.

Freeze pins the clean execution commit, source file hashes, control-relevant
Python/MIP/Gurobi/SciPy/NumPy versions, Gurobi runtime version, the existing
model seed read from a lightweight GRB model without optimization, its native
backend/library identity, exact predecessor `f4b342d` source-root freeze hash,
the inventory hash and all original raw/receipt hashes. The only admitted
historical inputs are the four own-case state-0 `qp_cache_feasible_hull` pools.
Each source receipt's original status and paid child time are retained. Every
column receives independent physical replay and compact-start source checks;
the historical lower certificates and pricing cache are not reused.

The state-1 linear tariff and stored-number rational gradient are selected
before either arm starts. The frozen file contains both full price vectors,
exact rational prices, selected source plan/load/key/hash/objective and duplicate
price flag. Every pair has the same known source-plan upper. Missing or invalid
source makes both calls in its pair ineligible, without regeneration or fallback.
The controller checks the frozen source before the first child. Each arm has its
own process and model, a 90/210-second child hard cap, its own raw files and
one receipt. The supervisor applies the 2700-second process-group cap; the
outer wrapper applies 3000 seconds. There are no retries.

The start-aware reader retains `mip_start_setup` submission, rejection and
timeout events with measured setup time. Submission leaves native acceptance
`unknown`. Each returned call's native seed and backend identity are checked
against the freeze. Raw native statistics remain separate from physically replayed
incumbents and admitted native bounds. Complete child elapsed, core call
timings, historical source paid time, freeze admission time, and one-time
source-inclusive total are reported separately. Timeout and failure traces are
preserved and a quiescent attempt is sealed with a manifest. Results still
require independent post-run review.

Focused pure validation command:

```sh
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m pytest -q src/tests/test_pricing_start_pilot.py
```

Author validation: **10 passed in 0.15 s**. `bash -n
src/cluster/pricing_start_pilot.sbatch` and `python -m py_compile
src/experiments/pricing_start_pilot.py` passed. The author also ran the
non-optimizing `_prepared_case` admission against the four existing local
sealed pools at
`/Users/nadan/Documents/ChatGPT/egg/research-20260928/cluster/solver-baseline-comparison-attempt1/sealed/20260928-attempt1`:
all four passed the inventory's raw/receipt hash pins, original status/time,
physical-column replay and compact-start validation, and both selected
queries were produced per case. This is source preparation only; no pilot
attempt or native optimization was run by the author.
