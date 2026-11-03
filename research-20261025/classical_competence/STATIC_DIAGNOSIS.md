# Static diagnosis of the classical competence check

25 October2026. Source inspection only; no imports, tests, optimizer calls,
hashing or frozen-source edits. The large raw receipts were not read. Observed
numbers below come from the parent's compact receipt review.

## Evidence and its limits

The40-trip case50685 returned an independently replayed15-vehicle plan, versus
the historical graph endpoint's3 vehicles. That historical comparison remains
unmatched in seed, allocation and method. The80-trip case50605 constructed29
vehicles. Its helper reported a feasible internal candidate but returned after
53.737 seconds of helper work /55.359 seconds of case time, beyond the caller's
55-second completion cutoff. The caller therefore did not independently replay
or admit it. The helper retained an `objective2:extract` deadline failure;
nested receipt publication extended total case materialization to64.6127 seconds.

Thus one of two cases produced an independently admitted timely offline witness.
The80-trip outcome is **not** evidence of physical infeasibility or absence of an
internal candidate. Neither outcome establishes a learned-versus-classical
advantage over a competent classical baseline.

## Why this greedy rule can strand a large fleet

The constructor starts with one route per trip and chooses initial pullout/
pullin modes solely by movement minutes and ID
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_control.py:200)).
It then considers only joins from an existing route's tail to another route's
head. It irrevocably takes the eligible join with smallest added deadhead
minutes; extra charging capacity is only the next lexicographic key
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_control.py:215)).
There is no exchange, split/reconnect, lookahead or alternative boundary search.
It stops when no single eligible join remains
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_control.py:243)).

**Inference:** an early cheap direct join can consume endpoints or battery slack
needed for several later joins; a slightly longer depot connection could preserve
more future charging/route compatibility. This mechanism can leave a locally
unmergeable15- or29-route partition even when a much smaller feasible partition
exists. The source supports this explanation, but without tracing a rejected
alternative it does not identify which particular merge caused either result.
Adding a vehicle-cost term alone would not solve it: every immediate merge
already removes exactly one vehicle, so that term is constant across candidates.

The SOC screen gives each route its own maximum available charging opportunity,
starts it full and checks terminal replenishment
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_control.py:61)).
It explicitly does not check shared contention
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_control.py:157)).
Ignoring shared contention can cause charging trouble downstream; it is not by
itself an explanation for overusing vehicles. It must not be presented as a
minimum-fleet construction or a strong conventional scheduling control.

## Why the80-trip failure is not just solver difficulty

Completion builds the full physical model before fixing its movement binaries,
then repeatedly traverses every physical row, variable and bound. Inventories
occur before/after fixing and around optimization, extraction and candidate
commit
([inventory](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_charging.py:35),
[call sites](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_charging.py:197)).
Events are deep-copied into an in-memory history and copied again for the record
callback
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_charging.py:175)).
Captures, extraction, replay, billing and a final inventory all precede witness
commit
([source](/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017/src/egglab/constructive_charging.py:244)).

**Inference:** repeated inventory/capture/copy/serialization work plausibly used
a material part of the window and explains why a feasible internal candidate
could fail final admission. The parent observed inventories1..12 and very large
nested receipts. No static inspection can apportion the53.737 seconds among
native optimization, inventories, extraction and recording. Preserve the55-second
rejection and64.6127-second overrun; do not backdate an endpoint or call it
infeasible. Compact preservation is appropriate, but removing physical checks
merely to obtain a pass would answer the wrong question.

## Smallest defensible classical replacement

Replace irrevocable local merges with **global minimum-fleet path selection**.
A bipartite maximum-cardinality/min-cost path-cover construction on the declared
time-compatible DAG is the simplest route-only comparator: each selected join
reduces route count, while global matching can exchange earlier choices. Freeze
secondary deadhead/charging-stress keys before another run. However, pairwise
edge eligibility alone does not enforce whole-route SOC or shared charging, so
matching plus the unchanged charging/replay helper is a candidate control, not
automatically a competent electric-fleet baseline.

For a stronger direct check, use the existing full physical path-flow model with
a fleet-first objective, then price/charging refinement and independent replay.
That globally accounts for route choices and charging feasibility instead of
locking a weak greedy topology first. This is a conventional optimization
baseline proposal, not a new method or currently executed result. It requires a
separate small prospective driver/protocol and ordinary resource cap, not a new
recovery controller or relaxation of physical admission. Do not tune greedy
weights against these two outcomes and then call the result an independent
classical comparison. Broader matched experiments still need common budgets,
strong baselines and grouped fresh development timetables.
