# Source-guarded route identity when the fresh candidate is unexposed

25 October 2026. **Conditional inference is sound under the exact guards below.**
Source-only inspection of `pf.recover_paths`, the needed NR case/path validation
and immutable `fixed_route_qp/qp_control_v3.py` candidate admission. No helper or
other source code was changed; no data, plan, row or receipt was opened; no
imports, hashes, tests, replay, generation or solver work ran. This is a source
argument for route identity, not runtime qualification, a new physical proof or
an optimum/certificate claim.

## The missing observable is real

The helper can admit a fresh physical QP candidate while retaining the better
fallback in its returned `plan`/`replay`. It exposes `candidate_bill_exact` and
candidate-admission flags, but replaces returned plan/replay only when the
candidate strictly improves fallback
([admission/selection](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/fixed_route_qp/qp_control_v3.py:399)).
Consequently, replaying or comparing the returned fallback must never be labeled
direct observation/replay/comparison of the fresh candidate. No helper modification
or candidate-plan return is required to establish the narrower route inference.

## Why the selected movements determine unique paths

`pf.recover_paths(case, selected_ids)` first validates the case, rejects duplicate
or unknown movement IDs, and requires exactly **one selected incoming and one
selected outgoing movement for each mandatory trip**. Starting at each selected
pullout, it repeatedly follows that trip's unique outgoing movement until a
pullin. It rejects repeated movements/trips, invalid ends, disconnected selected
movements and incomplete trip coverage
([recovery source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_pathflow.py:109)).
There is no alternative successor, route branching or choice of parallel mode
left once a passing selected-ID set is fixed. Start iteration follows stored
case movement order, making the recovered vehicle numbering deterministic;
the scientific route object can ignore that numbering.

NR case validation independently ensures unique trip/movement IDs, strictly
positive trip duration and chronological movement ownership. For an internal
arc from trip u to v, its legs depart no earlier than u's end and arrive no
later than v's start. Thus `u.start < u.end <= v.start`, so internal arcs advance
strictly in trip-start time and cannot form a directed service cycle. Reachability
alone would not prove uniqueness; the selected one-in/one-out and complete-path
checks above supply that property
([NR validation](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:148)).

NR replay also requires each vehicle's ordered movements to match its ordered
trip predecessor/successor pairs, pullout/pullin endpoints and exact once-only
mandatory coverage
([path replay](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/native_recharge.py:237)).
Any replay-admitted plan on the same case using exactly the passing selected
movement set must therefore have the same ordered trip/movement path multiset,
up to permutation of vehicle labels.

## The fresh-candidate guard closes the other link

The immutable helper independently replays the input fallback and rejects
duplicate/out-of-universe input movement IDs
([input guards](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/fixed_route_qp/qp_control_v3.py:123)).
After new QP extraction, it calls unchanged NR replay on the **new plan** and
requires replay_ok, no duplicate actual movement IDs, exact equality with the
input movement-ID set, equal fleet count and the same case identity
([candidate guards](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/fixed_route_qp/qp_control_v3.py:370)).
Only a proposal surviving objective/admission checks, no retained failures and
the final inclusive guard sets `qp_candidate_admitted=True`
([flag publication](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/research-20261025/fixed_route_qp/qp_control_v3.py:401)).
The exact consumed helper must preserve those source guards; a matching field
name in some other helper is not evidence of their execution.

## Required caller evidence and truthful reporting

Before claiming inferred candidate route identity, the caller must establish:

1. The actual bound case and original witness pass the selected identity/replay
   contract, and fixedSelectedIDs are the original witness's unique movement IDs.
2. Independently call `pf.recover_paths(case, fixedSelectedIDs)` and require its
   recovered routes to match the original witness's canonical ordered paths.
   A suitable comparison is the **sorted list/multiset** of
   `(tuple(vehicle['trips']), tuple(vehicle['movements']))`. Ignore only vehicle
   numbering and order of vehicles; do not reorder within a path or reduce the
   multiset to a set that hides multiplicity. Preserve the fleet-count check.
3. The consumed helper source/API is bound, and the fresh candidate really has
   `qp_candidate_admitted is True` with no helper/copy/fatal failure undermining
   its admission. Required native status, objective/matrix guards and parent-
   timely complete receipt admission remain separate pilot qualification checks.
4. Report `route_identity_method='source_guarded_unique_path_inference'` and the
   original-versus-recovered comparison separately from candidate admission.
   Do not report a direct candidate-path comparison when its plan is unexposed.

Under these conditions the two source links compose: the independently recovered
input topology is unique, and every helper-admitted fresh candidate is replayed
on exactly that topology. It follows that its canonical ordered routes equal
the original routes, even if fallback was retained for the returned operational
endpoint. This conclusion concerns the fresh admitted candidate, not an
assumption that returned fallback is that candidate.

If recovery, original-route comparison, actual source binding, fresh admission
or any required guard is absent/false/unknown, keep the cell unqualified; do not
fill the gap with fallback equality. `used_fallback` alone neither proves nor
disproves that a fresh candidate was admitted. Numerical OPTIMAL alone also
cannot establish any of these properties.

## What does not follow

The inference exposes no candidate charges, loads, SOC trace or full plan hash.
It does not permit an independent caller replay of an unreturned plan or transfer
the fallback's charging/cost evidence to that plan. Candidate physical admission
rests on the helper's unchanged new-plan replay and source guards; routes rest
on the argument above. It does not add a physical tolerance, prove global routing
optimality, create a solver certificate or establish runtime source integrity.
Parent must freeze this truthful evidence policy and the actual helper/caller
bindings prospectively before any pilot execution.
