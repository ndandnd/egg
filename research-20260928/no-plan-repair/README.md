# Compact pricing: unresolved calls without a new plan

The completed ordered solver comparison exposed a return-path error in three
public target calculations. The native solver returned `NO_SOLUTION_FOUND`
without an incumbent or plan, and the compact wrapper checked extraction
policy on that absent plan. Earlier bounded calls existed in those attempts.

This repair concerns how future calls return incomplete results. It does not
rerun the comparison, change its three failed outcomes, or establish public
optimality or faster computation. Full spent time and failed outcomes remain
in the [reviewed comparison](../solver-baseline-comparison/results-attempt1/README.md).

The required behavior is to pass a valid unresolved result to the coordinator,
retain any earlier verified evidence, reject invalid present witnesses, and
preserve the fresh-pricing requirements for certification. A missing plan is
neither an executable schedule nor a new global certificate.

The unresolved call keeps its complete result in a distinct event. The event
reader must accept that record while successful pricing results retain their
one-to-one correspondence with admitted bounds and cache evidence.

The implementation passed 156 focused tests across seven existing test files.
The checks cover an unresolved first call, preserved bounds after a later
unresolved call, a finite raw solver lower without a new admitted certificate,
cache-only evidence without fresh certification, invalid witnesses and reuse
admission of a bounded prefix followed by an unresolved call. No native
optimization was run locally. The independent [review](../agent-notes/no-plan-repair-review/REVIEW.md)
found the implementation and focused cases consistent with this contract.
The [implementation note](../agent-notes/no-plan-repair/IMPLEMENTATION.md)
records the exact test command. Publication CI is pending.
The next separate research package will assess supplying a known feasible fleet
as a physical-pricing MIP start, with a prospective comparison and complete
cost accounting before any new experiment. No additional cluster budget is
committed by this source repair.
