# Prospective development diagnostic: a feasible start for physical pricing

Status: reviewed prospective design; pilot not yet run. Before launch, freeze
and check the execution source, input selection, runner and budget. The user's
standing authorization permits this bounded pilot; no further approval is needed.

## Question and scope

Does giving the compact physical-pricing MIP a checked feasible fleet improve
its returned incumbent or lower bound within the same complete-call budget?
This follows the observed pricing bottleneck and the repaired no-plan return.
It compares fixed-price oracle calls, not complete iterative hull algorithms.
No retrieval model, training labels, independent test outcomes or private data
enter this diagnostic. The start is a solver hint, never a certificate.

The two arms use the same physical model, prices, objective, native backend,
thread count and time caps. Read and freeze the effective `model.seed` and
runtime versions for both arms; retain the common backend default rather than
changing solver policy. The only algorithmic difference is supplying the
checked movement-selection vector through the native initial-solution API.
Continuous charging remains a native decision. All existing feasibility and
bound replay requirements apply to returned results.

## Inputs and grouping

Use the four existing development cases in their recorded order:
`synthetic_cyclic`, `synthetic_multivisit`, `public_depot15`, `public_depot16`.
Both public depots are the same Hildenbrand base timetable, not independent
replications. No cases will later be called untouched evaluation data.

The candidate fleet pools come exclusively from each case's own state-0
`qp_cache_feasible_hull` result in the sealed solver-baseline comparison,
execution source `f4b342dc85799d01d9313baeaf8c9ec527759d59`.
The runner must freeze source file hashes, original status and paid source
time, and replay the admitted physical columns before selecting starts.
A missing, ineligible or invalid source leaves the affected pair ineligible;
never substitute a different arm or regenerate a successful source silently.
The historical comparison's failures and timings remain unchanged.

For each case use the existing state-1 supply cost and two prospective queries:

1. **Linear tariff:** prices equal the state-1 coefficient vector `a`.
2. **Marginal price:** evaluate the state-1 supply gradient at the load of the
   source-pool plan minimizing operations plus the linear-tariff bill; break
   ties by the existing canonical column key. With the repository convention
   `F(L) = a·L + (1/2) Σ b_t L_t²`, the price is `a_t + b_t L_t`.
   Use the checked physical load and the repository's stored-number rational
   calculation before converting the final price vector to native floats.

At each query choose the start from the same admitted pool by minimum operations
plus that query's electricity bill, again with deterministic key tie-breaking.
Freeze the actual selected plan, load, pricing objective, price vector and
physical identity before either arm runs. The runner must check that the
selection uses no target solve outcome. Duplicate price vectors remain declared
diagnostic rows and are identified as duplicates rather than replaced.

The 16 declared calls are four cases by two queries by two arms. Within each
case, use the following predeclared order (zero-based case index in the list
above): cold then start when case index plus query index is even, and start
then cold otherwise. Query index is 0 for the linear tariff and 1 for the
marginal price. This counterbalances first arm across cases within each query,
including the two public depot variants; it does not create independent
replications or a statistical speedup estimate.
One serial process tree, separate child process/model per call, no retries.

## Cost and outcome accounting

Both arms have the same known feasible source-plan baseline when interpreting
quality. A cold native call with no incumbent does not mean no feasible fleet
is known. Report separately:

- Native status, returned incumbent availability and physically replayed cost,
  admitted native lower bound and resulting native interval when available.
- The known source plan's objective at the query price, and the best feasible
  upper available from that common baseline and any returned native plan.
- Start requested/submitted, selected movement count, mapping/validation time
  and any observable native acceptance status. Do not infer acceptance from
  submission or a later feasible result. Do not invent time to first incumbent
  if no callback records it.
- Complete child elapsed time, core call/model-build/validation time where
  actually measured, native optimization time and hard-deadline outcome.
  Failed or unresolved calls retain all elapsed time and raw evidence.
- Original source-generation time and preparation/admission time, explicitly
  outside versus inside each online call. Report conditional online work and
  source-inclusive work separately; do not count the historical pool as free
  or sum it repeatedly as if newly generated for every query.

A raw reported lower from an unresolved/no-plan call is not automatically an
admitted complete-fleet certificate. Preserve raw stats separately. A rejected
start is a failed start-arm call, not a silent cold fallback. Lower bounds and
numerical plans retain native solver-tolerance qualifications.

The pilot's evidence reader must explicitly accept and account for
`mip_start_setup` records, including submission, rejection and timeout. The
legacy `native_pathflow_qualification.read_worker_evidence()` event whitelist
does not accept this new opt-in record; do not reuse that reader unchanged or
silently discard the setup evidence.

## Prospective resource ceiling

For each synthetic call: one native thread, phase cap 45 seconds, core wall
cap 60 seconds. For each public call: one native thread, phase cap 160 seconds,
core wall cap 180 seconds. Start validation/mapping/attachment lies inside the
same core wall deadline; complete child elapsed is also recorded. The child
hard cap is core wall plus 30 seconds for process setup and teardown.

The 16 core wall caps sum to 1,920 seconds, and child hard caps to 2,400 seconds.
Allow a 2,700-second controller cap and a 3,000-second outer wrapper cap,
within one Slurm allocation requesting one CPU, 8 GB and one hour. All native
and numerical-library threads are one. No retry/requeue; exclude
`scaglione-compute-01`. Record actual allocation and setup time. Other projects
and held jobs are untouched. No job may launch before the runner, source and
input pins are frozen prospectively and the source passes relevant validation.

## Interpretation

Present all declared rows, including failures and ineligible inputs. Compare
final bounds and paid time together. Improvements would support further
testing of native starts inside iterative solving; they would not establish
whole-hull speedup, public optimality, scalability or learned-proposal benefit.
A null or harmful effect remains a result. Broader independent timetables and
nearest-neighbor retrieval still precede any learned proposal evaluation.

## Interface references

[Python-MIP's model API](https://python-mip.readthedocs.io/en/latest/classes.html)
documents the initial-solution and seed interfaces.
[Gurobi's parameter reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html)
documents the backend seed. A supplied start remains distinct from an accepted
incumbent; the implementation records what the API exposes rather than inferring
acceptance from a successful setter call.
