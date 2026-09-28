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
and query prices were frozen in the exclusive execution checkout before
submission. The pilot consumes physical plans, not historical pricing bounds.

The execution ceiling is one serial Slurm job requesting one CPU, 8 GB and one
hour, with all numerical/native threads one and no retry/requeue. It excludes
`scaglione-compute-01`; other projects and held jobs remain untouched.
Controller and outer caps are 2,700 and 3,000 seconds.

The [runner](../../src/experiments/pricing_start_pilot.py) and bounded Slurm wrapper
are implemented. Ten focused pure tests, shell syntax and compile checks pass;
all four actual source pools passed non-optimizing physical admission. Independent
launch review found no blocking issue, and source `6759daa4eaeb92152607a3d60840d52988093973`
passed [full CI](https://github.com/ndandnd/egg/actions/runs/36443216684).

Job **577225** was submitted once at 15:28 UTC. The single launch observation
was `PENDING (Priority)`, requesting 1 CPU/8 GB/1 hour. All four source pools
were eligible and all eight selected queries were frozen before submission.
No pilot outcomes have been inspected.

Receipts: [freeze](FREEZE_RECEIPT.json), [CI](CI_RECEIPT.md),
[submission](../cluster/pricing-start-pilot-577225.json),
[preparation and preserved helper failure](PREPARATION_NOTES.md), and
[independent review](../agent-notes/pricing-start-runner-review/REVIEW.md).
The original Google Doc launch update was appended once and verified after
reload; [persistence receipt](../agent-notes/google-doc-pricing-start-pilot/RECEIPT.md).
The README has subsequently gained launch status; the review records its
prospective version. Execution code and protocol pins are unchanged.

Next: one scoped queue observation for job 577225 at the next heartbeat.
After it vanishes, use scoped accounting and wrapper/supervisor receipts to
confirm termination and a stable seal before collecting and independently
reviewing all 16 declared calls. Do not resubmit, inspect active outcomes, or
start a larger sweep based on partial results.
