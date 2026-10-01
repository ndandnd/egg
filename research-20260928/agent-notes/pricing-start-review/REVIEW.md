# Pricing-start review

Verdict: pass for the opt-in compact-pricing core and prospective fixed-price
protocol. The pilot has not run; this review makes no performance claim.

## Method and source contract

The compact path-flow model has one binary family, `x[j]`, for movement
selection. A source fleet maps to this model by its selected movement IDs,
independent of vehicle labels. Review requires every `x[j]` to be assigned
explicitly to 0 or 1, after checking the source's compact formulation, native
matrix, extraction policy, exact case identity, physical replay, and recovered
complete paths. The compact model's SOC, charge, and load variables remain
continuous completions. Python-MIP's `Model.start` is a solver hint; successful
submission does not establish acceptance, feasibility of the completion, a
bound, or a certificate. Existing independent replay and native bound
admission remain necessary for solver results. An invalid or rejected start
must be surfaced; the start arm cannot quietly retry cold. If acceptance is
not exposed by the selected backend/API, record it as unknown.

The compact input replay should validate the original physical witness before
mapping, including case identity, path ownership and service coverage, charging
windows/resources, state of charge, stored load, and intrinsic operating cost.
Source-plan objective is retained as a shared feasible baseline. It must not be
inserted as a fabricated native incumbent or solver lower bound when the native
call has no incumbent.

## Protocol assessment

The proposed 16 calls (four development cases, two predeclared prices, cold and
start arms) are a useful bounded diagnostic of fixed-price oracle behavior.
They are paired descriptive observations, not independent replications; the
two public depots share one Hildenbrand timetable. The current
`case_index + query_index` arm-order schedule counterbalances first arm within
each price query. It does not support a statistical speedup claim. The two
price queries are analytically distinct: the existing linear tariff `a`, and
the state-1 gradient `a_t + b_t L_t` at a deterministically selected checked
source-plan load. Keep both; identify duplicate vectors without replacing
them. Freeze selection/tie-breaks, prices, source pool and case identity before
either arm runs.

Compare solver incumbents, admitted lower bounds, intervals, and the common
known-source feasible objective separately. A cold no-incumbent call is not
infeasibility because the source plan remains known feasible. Do not interpret
the MIP hint or source baseline as proof of native optimality. This experiment
does not measure complete iterative-hull speedup, public optimality, scalability,
or learned-proposal benefit.

The reviewed implementation validates and replays the start before model
build, recovers the complete movement paths, maps every `x[j]` including zeros,
and rejects unexpected discrete variables. `start_plan=None` preserves the
cold path. Start setup rejection or timeout raises with a `mip_start_setup`
receipt; it does not retry cold. The deadline starts before source validation.
The setup event times validation, model build, objective attachment, and start
mapping/attachment separately; native optimization time is separately
recorded. Use complete child elapsed time for paired end-to-end cost. The cold
path has no per-stage setup event, so do not claim a matched component-level
build-time comparison from this core event stream.

Record source-pool generation/admission time separately from per-call replay,
mapping/attachment, native optimization, and complete child elapsed time. The
start overhead and validation belong inside the same core deadline as the cold
call; source-inclusive and conditional online costs should both be visible
without charging the historical source repeatedly for each query. Keep each
declared row and failure; no retries or silent substitution.

The prior `native_pathflow_qualification.read_worker_evidence()` whitelist
rejects `mip_start_setup`. The reviewed protocol now requires a start-aware
pilot reader that preserves submitted, rejected, and timed-out setup records;
do not reuse the legacy reader unchanged. The core event records the
Python-MIP `model.seed` and backend identity/library hash, while the smoke
receipt records Python-MIP 1.17.6. Freeze and record the Python-MIP package and
backend versions for both arms in the future runner.

Python-MIP's official [Model.start documentation](https://docs.python-mip.com/en/latest/custom.html#providing-initial-feasible-solutions)
describes supplying an initial feasible solution and completing auxiliary
variables; its [Model API](https://python-mip.readthedocs.io/en/latest/classes.html)
documents the `start` and `seed` properties. Gurobi's [MIP start example](https://docs.gurobi.com/projects/examples/en/current/overview/starts.html)
describes starts as candidate solutions and explains partial starts; its
[Seed parameter reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#seed)
documents the backend default. In the installed Python-MIP 1.17.6 wrapper,
`Model.__init__` initializes `seed` to 0, the getter returns it, and the CBC
and Gurobi adapters pass it to their backend. Record that value and runtime
versions without changing the existing default.

## Implementation verdict

The opt-in core passed this bounded contract review. `_checked_pricing_start`
checks exact physical identity and compact formulation/matrix/extraction
provenance, calls independent physical replay, and validates recovered paths.
The mapping sets all movement binaries; an absent source leaves the existing
cold path untouched, while malformed or mismatched input fails before model
build. A source replay does not itself prove the compact matrix completion or
native acceptance; the code correctly treats the hint as unverified and leaves
returned-plan replay and `admit_bound` as the only route to native intervals or
certification.

Sol reports the focused command
`PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m pytest -q src/tests/test_native_pathflow_mip_start.py src/tests/test_native_pathflow.py`
with 40 passed in 0.11 s. I did not rerun it. One small CBC cyclic-case smoke
returned `certified`, lower 36.999999 and upper 37.00000099999855 in 0.23161 s
total (0.20787 s setup) under a 5 s core / 3 s phase cap. The smoke preceded
the final pure-tested unexpected-integer guard; no second solver run was made.
Acceptance was recorded as unknown, consistent with the Python-MIP setter's
contract.

## Reviewed artifact pins

| Artifact | SHA-256 |
|---|---|
| `src/egglab/native_pathflow.py` | `cd61085c5942248e53cdfbd92056c4ba324dfd81d5d18b726f58715298003df0` |
| `src/tests/test_native_pathflow_mip_start.py` | `058c2182018b8b7f92d16c1f72e5a8c9249a816259e85cf8d218038234f6e125` |
| `research-20260928/agent-notes/pricing-start/IMPLEMENTATION.md` | `21ff48a39e24886389e49e691f89831ba54f9621d8987645543f99250a74e17f` |
| `research-20260928/agent-notes/pricing-start/SMOKE_RECEIPT.json` | `d0a0618799845ad36c3deb14dfde4e5423d11242fa27cd013be2e44fe6b0a6ab` |
| `doc/PRICING_START_PILOT_PROTOCOL_20260928.md` | `f4f8489e9e2fd59479810d2fa53d85b420c6f3546d6864a2de720943645195a3` |
| `research-20260928/pricing-start/README.md` | `356d9ac423a4a2f1186e66fde93e9e372c692102acc4b361ee89a64b13d2435c` |

The manager updated the README review-status sentence after this verdict; its pin above reflects that publication-only update.
