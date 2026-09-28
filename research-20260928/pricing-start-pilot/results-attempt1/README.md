# Feasible fleet starts: mixed effects in fixed-price solving

Status: independently reviewed; all 16 declared calls reconciled without new
optimization. Figures visually checked. All cases are development cases. The two public depot
variants share one Hildenbrand timetable.

In this 16-call pilot, supplying a physically checked fleet as a native starting
hint had mixed effects on final solution quality. Both arms certified the small
synthetic problems. Every public call used its 160-second native phase allowance,
and all public optimality intervals remained open. The marginal-price query is evaluated at the prospectively selected source fleet.
The data support a comparison of final quality at matched budgets; they do not establish faster convergence.

For the depot-15 linear query the same feasible cost was found, but the starting
hint weakened the lower bound. For its marginal-price query the hint improved the
feasible cost by about 1.10 while weakening the lower bound. Depot 16's linear
query was effectively unchanged. For its marginal-price query the feasible cost
was unchanged and the hint strengthened the lower bound by about 11.78. These
four comparisons are diagnostic observations from one base timetable and one
solver seed, not independent replications of a treatment effect.

The preselected source fleets cost 0.32–2.74% more than the best newly returned
public incumbent in each query. This is a comparison with returned fleets, not
a guarantee relative to the unknown optimum; source-generation work remains paid.

Both arms were compared against the same feasible source fleet. Returning or
submitting that fleet is not counted as discovering a new improvement. Start
submission is observed; solver acceptance is unobserved. Numerical lower bounds
retain native solver tolerances. No learned model, complete iterative-method
speedup, or public-case optimality follows from these observations.

## Computation and evidence

Job 577225 completed with exit code 0 in 22m14s on one allocated CPU, requesting
8 GB. All 16 declared calls returned, with no hard timeouts: eight synthetic
certifications and eight public bounded outcomes. All eight hint submissions
were recorded. Original source generation, preparation, native solve, complete
child, wrapper and whole-job times are retained separately; overlapping clocks
are not summed. Original source-generation cost remains payable even when a
starting fleet is reused.

Analysis: [16 calls](analysis/calls.csv), [eight paired comparisons](analysis/pairs.csv),
[accounting](analysis/accounting.json), and [interpretation](analysis/ANALYSIS.md).

![Public cost intervals and the common feasible baseline](analysis/public_bound_quality.png)

![Complete call time and historical source costs](analysis/paid_times.png)

 Independent result review:
[review and reproducible checker](../../agent-notes/pricing-start-result-review/REVIEW.md).
The published execution source is `6759daa4eaeb92152607a3d60840d52988093973`.
Source CI 36443216684 passed; the preceding launch-receipt backup b912078 passed
CI 36444453893. Collection matched every entry in the 119-file sealed manifest
and the prospectively frozen input hash. The full raw archive is retained
privately; this public record contains a compact derived analysis and receipts,
not the complete raw optimizer logs. Analysis scripts state their input paths.

## Consequence for the research plan

Physical pricing still consumes nearly all measured online time on these public
cases. A feasible hint is useful as an optional proposal, but this pilot does not
justify treating it as a general acceleration method or replacing verification.
A route predictor could improve a feasible schedule without resolving its global
lower bound. Those must remain separate evaluation tasks.

The next bounded package should build the independent timetable benchmark:
validate one additional public network and a small synthetic scaling family,
record physical assumptions, and reserve base-network groups for future testing
before training or comparative outcomes. Prepare the cold, retained-column and
nearest-neighbor proposal/repair comparisons with common quality targets and
explicit budgets. The current cases stay development data. Do not enlarge the
solver-start experiment merely to seek a more favorable result.
