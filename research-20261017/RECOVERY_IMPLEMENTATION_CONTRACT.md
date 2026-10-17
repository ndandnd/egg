# Pruned-plan → full-model recovery contract

**Design only, 17 October 2026.** No source/model changes, solver runs, training, cluster
work, launch or promotion are authorized by this document. Frozen screenv3 workers remain
untouched. Recovery needs a separately frozen budget/design after the complete current
cohort satisfies every recovery gate in `LOCAL_CAMPAIGN_PROTOCOL.md`, lines 136–172.
A partial or favorable subset cannot trigger it. This specifies candidate engineering,
not learned-ranking superiority or a new optimality claim.

## 1. Input and lift invariants

Inputs are the immutable full case, its explicitly identified pruned subset, a saved
physical fleet plan, target market, and an absolute common monotonic deadline. Retain
source/full identities, subset mapping/hash, plan hash, objective/extraction-policy
identities and acquisition costs. Validate unique movement/trip IDs and exact equality
of shared physical definitions: trips, legs, charge visits/windows, fleet/battery/reserve,
efficiency, charger/power limits, market edges and cost coefficients. A movement with the
same ID but different physical content is a mapping violation, not a usable start.

1. Replay the source plan on its source case and recompute its physical bill. Validate
   route coverage/ownership with `recover_paths`. Reject malformed/unknown/duplicate IDs.
2. Construct a separate full-case physical witness preserving vehicle routes and charge
   events. Replace case identity only after the subset-equivalence checks, then independently
   replay on the FULL case and target market. Recompute full-case load, operating cost and
   true supply bill; do not merely restamp cached replay or copy its aggregate objective.
   Retain both source witness and lifted witness plus provenance. No physical relaxation,
   charge clipping, topology alteration or tolerance change is allowed.
3. Build `build_feasible_model(full_case, 'GRB')`. Map every `built['x']` by the full
   case's movement ID, assigning one for selected movements and zero for EVERY other
   full-case movement, including all edges absent from pruning. Submit all binaries once
   through `model.start`; verify the discrete-variable inventory as
   `_attach_pricing_start` currently does. These are start VALUES, never variable bounds
   or constraints: all original full-case alternatives remain available during search.

The initial safe contract is **binary-only start**. Leave charge, SOC, aggregate-load and
objective epigraph variables undefined so the solver computes its own continuous extension.
Python-MIP documents automatic computation of auxiliary/continuous variables, and Gurobi
allows partial starts; start submission is an attempt, not a guaranteed accepted incumbent.
See [Python-MIP Model.start](https://python-mip.readthedocs.io/en/latest/classes.html#mip.Model.start)
and [Gurobi Start](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/variable.html#start).
Providing explicit zeros for unselected binaries is this contract's audit choice, not an
assertion that the API requires every zero.

Never copy positional `(j,k)` charging assignments from the pruned model. Here `j` is a
movement index and `k` indexes `compile_case` elementary intervals: restoring edges/visits
can split intervals and change both maps. Optional continuous starts are a future separate
variant: derive energy by intersecting the physical charge events with FULL-case elementary
intervals and matching movement IDs; derive SOC from ordered physical events, loads from
full-period energy, and epigraph values from current tangents. Validate original rows and
shared coupling. Ambiguous mapping rejects the continuous hint; it must not discard a
valid physical fallback. No copying source solver-load/roundoff arrays or source epigraphs.

## 2. Three different evidence claims and failure behavior

| Evidence | Permitted conclusion |
|---|---|
| Full-case independent physical replay and bill admission | A feasible physical fallback and its upper bound exist. |
| `model.start` submitted / solver log reports processing or acceptance | A hint was submitted / the solver reports a native starting solution. Neither proves independent physical replay nor optimality. |
| Full unrestricted solve supplies an admissible global lower bound, and retained witness supplies replayed upper | An enclosure for the full problem; certification only when the unchanged admission/gap tests pass. |

Save the admitted lifted witness BEFORE start setup/search. Return the lowest independently
replayed true-bill witness across source fallback and every later candidate, including
same-round raw/completed candidates. Start rejection, no new incumbent, timeout, extraction,
completion or backend failure preserve this fallback and report the failed stage/type/message,
solver status/log and timings. Without an admitted witness return explicit no-plan/failure.
A reported full-model infeasibility conflicting with a replay-valid witness is a visible
model/replay contradiction; retain the physical witness but make no infeasibility certificate.

Pruned/restricted MIP lower bounds and fixed-topology LP lower bounds NEVER bound the full
problem: those feasible sets are subsets. Only full unrestricted native bounds, with the
existing guard and objective admission, may raise the full lower bound. A tangent model's
bound underestimates the convex bill; final upper is recomputed true bill. Preserve raw MIP,
completion and selected-admission objectives separately. A fallback without a fresh valid
full lower bound remains feasible-only; it cannot be called certified. Never attach another
candidate's solver objective to the fallback to manufacture objective equality.

## 3. Deadline, interfaces and minimal qualification tests

Start one monotonic clock before data/model loading, scoring and pruning. Pass absolute
`deadline = t0 + total_allowance` to every stage; recovery receives only the remainder.
Acquisition, lifting/replay, full-model construction, start processing, all native phases,
completion, final replay and artifact work count. Existing `Budget.wall_seconds` APIs create
new relative deadlines, so add an explicit external-deadline path and clamp every native
phase to it. Freeze search/postprocessing reserves prospectively and identically by arm;
no free cleanup solver time or retry budget. Record wall/CPU and stage overrun/failure.

Needed changes, after the current cohort is terminal and the next prospective design is frozen: generalize `_checked_pricing_start` to validate source→full
lift and supported completion policy explicitly (it currently requires exact case identity
and historical extraction policy); reuse `_attach_pricing_start` unchanged for full binary
mapping; add `start_plan`, external `deadline`, and separately retained fallback to
`solve_planner` (currently none). Rebuild/attach the selected start to each new tangent model;
carry admitted best forward. `solve_pricing` already has `start_plan`, but requires the lift,
policy compatibility and external deadline path. Keep `_extract`, `_candidate_score`,
`_candidate`, `admit_bound` and independent replay as admission boundaries. Log submitted,
solver-reported accepted/rejected and unknown start status separately; `model.start = ...`
alone is only submitted. No source edits are included in this design package.

Minimal meaningful tests before a later tiny solver qualification:
- Permute full movement order, add extra edges and split charge intervals: every selected
  ID remains one, all extras zero, no source `(j,k)` or continuous variables submitted;
  variable bounds/physical constraints remain unchanged.
- Reject unknown/duplicate IDs and same-ID changed physics; successful lift must pass
  full-case replay and independent bill recomputation, including a changed tariff.
- Preserve admitted fallback on start setup/rejection, no incumbent, optimizer timeout,
  and later replay failure; reject invalid fallback; never fabricate a lower bound.
- Mock a deceptively high restricted/completion bound and verify it never becomes global;
  a full native bound must remain separate from the fallback's objective.
- Fake-clock loading/setup/recovery exhaustion: no phase gets a fresh allowance; reserves
  and failure finalization are charged; no solver call starts after the deadline.

For attribution, later compare ranking sources under the SAME pruning, initial/recovery
split, full-model search, start policy and total clock. Include the frozen nonlearned ranking
and matched random; distinguish pruning-stage bill from final bill and paired recovery
increment. Compare recovery versus no recovery within each ranking with equal total budgets
(and full-model controls). Recovery benefit alone cannot establish learned ranking value.
Do not select a recovery split or seed from partial current outcomes. Complete development evidence may motivate the next hypothesis, but its comparison requires a newly frozen design and cohort; it is not confirmation on the reused screen. If the current promotion gate fails, this contract does not override it: diagnose the failure and justify any different follow-up protocol explicitly.

A retention guarantee is deliberately narrow: returning the minimum admitted bill cannot worsen the SAME acquired prefix witness. It does not guarantee superiority over a static pruned solve that spends the entire allowance searching, nor over the cold full model. Model rebuilding and start processing may consume the recovery budget without improving the plan. Those opportunity costs belong in the matched comparison.
