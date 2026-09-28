# Fixed-price cold/start diagnostic

This pilot measures whether a checked feasible fleet helps the compact native
pricing solver return a better incumbent or bound under the same time cap.
The [reviewed protocol](../../doc/PRICING_START_PILOT_PROTOCOL_20260928.md)
declares 16 calls across four development cases and two predetermined prices,
with arm order counterbalanced across cases within each query.

Both arms share the same known feasible-plan baseline when comparing quality.
Native results, start submission, start acceptance, and the source-plan baseline
remain separate. Preparation time and original source-generation cost are
retained. The two public depot variants are one Hildenbrand timetable group;
this is not a test of complete iterative speedup or independent scalability.

The [source inventory](../pricing-start/SOURCE_INVENTORY.json) pins four initial
qp-cache fleet pools from the previous comparison. A read-only Unicorn check
matched all eight recorded raw-result and receipt hashes. The selected plans
and query prices will be frozen in the exclusive execution checkout before
submission. The pilot consumes physical plans, not historical pricing bounds.

The execution ceiling is one serial Slurm job requesting one CPU, 8 GB and one
hour, with all numerical/native threads one and no retry/requeue. It excludes
`scaglione-compute-01`; other projects and held jobs remain untouched.
Controller and outer caps are 2,700 and 3,000 seconds.

The [runner](../../src/experiments/pricing_start_pilot.py) and bounded Slurm wrapper
are implemented. Ten focused pure tests, shell syntax and compile checks pass;
all four actual source pools passed non-optimizing physical admission. Independent
launch review and published CI precede the prospective freeze and submission.
No job has been submitted and no pilot outcomes have been inspected.
