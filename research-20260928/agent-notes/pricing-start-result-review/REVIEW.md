# Independent pricing-start pilot results review

**Verdict: no blocking result or reporting issue found.** The 16-call result package matches the frozen design and is ready for root publication. The parent verified the 119-file seal and submitted-input pin; I did not repeat that transport audit or the historical cache-bound audit.

I added a read-only, non-optimizing checker at [check_pricing_start_pilot.py](check_pricing_start_pilot.py). Its invocation from the repository root is:

```sh
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python research-20260928/agent-notes/pricing-start-result-review/check_pricing_start_pilot.py
```

It passed. The checker reconciles the frozen 16-row order, all receipts and source times, source-column membership and selected common feasible baselines, exact fixed-price construction, physical replay of each native plan, and fresh native-bound admission. It checks start submission events, unknown acceptance, frozen seed/backend identity, call caps and time totals. It performs no optimization and emits no raw log dump.

All 16 calls returned on time with exit code 0 and a physically replayable native plan; there were no failed, unresolved, timed-out, or no-plan calls, and no event-evidence issues. All eight start calls recorded `submitted`; native acceptance remains unknown. The four synthetic pairs returned the same tolerance-qualified numerical intervals in both arms. All eight public calls used the 160-second native phase allowance and retained open admitted intervals. Depot 15 and depot 16 are two variants of one Hildenbrand timetable, not independent public replications.

The four public paired comparisons are mixed: start minus cold admitted lower bound was −5.679 for Depot 15 linear, −3.593 for Depot 15 marginal, effectively zero for Depot 16 linear, and +11.785 for Depot 16 marginal. The only improved replayed public incumbent was Depot 15 marginal, by 1.105 cost units; the other three public incumbent costs tied within 1e-5. Public source fleets were 0.320–2.737% above the best newly returned incumbent per query, a comparison to returned fleets rather than to the unknown optimum. These results support no general speedup, whole-hull, or optimality claim.

Paid-time arithmetic reconciles: 1,317.507 seconds across the 16 complete child receipts, 358.211 seconds of historical source generation paid once, and 1.652 seconds of internal freeze preparation produce the runner's 1,677.370-second source-inclusive subtotal. The separately measured whole freeze command was 1.956 seconds, so source generation plus that whole command plus child receipts is 1,677.674 seconds; its internal preparation measurement overlaps and is not added again. Supervisor (1,321.675 s), wrapper (1,329 s), and Slurm allocation (1,334 s) are enclosing overlapping intervals, not additional child work. The analysis accounts for all 16 rows and leaves unmeasured cold-arm setup fields blank.

I reviewed the final `ANALYSIS.md`, call/pair/source-cost tables, accounting file, and both PNG figures. The figures distinguish the common source upper, replayed native upper, and admitted native lower; time axes start at zero, and the text does not present the subsecond differences as a speedup. The analysis explicitly distinguishes submitted starts from accepted starts and retains solver-tolerance qualifications. No failure/no-plan timing case occurred in this pilot, so none is claimed.

Reviewed pins:

- Protocol `doc/PRICING_START_PILOT_PROTOCOL_20260928.md`: `f4f8489e9e2fd59479810d2fa53d85b420c6f3546d6864a2de720943645195a3`
- Runner `src/experiments/pricing_start_pilot.py`: `0efaa2fa49eee3d979bdc1569e26bbe2c98d5785f11f9602a001cad185e35937`
- Sealed `frozen.json`: `3204f528d8ef25b75c76841a5d0ed8d86b914d3f30126f5aabf580fb7aab385a`
- Sealed `summary.json`: `3affd8fcc04d05e1c955fd346211c8c92d00b01aee87cb44f4fa532c751304d6`
- Sealed `supervisor_receipt.json`: `bb22cb19f7403714cf03d974d9586ec3d53f7c33b7a0eec04f66c8ea126fe73d`
- Checker `check_pricing_start_pilot.py`: `3ef277a04d21f60332b41c8cd94e6c4bc8725c3379f865c9d05d76d998c97260`
- Analysis `ANALYSIS.md`: `3f0e876247d8c7071c5a3d641f4a3f30e12d9183772d95565786b71b4657b014`
- Analysis tables `calls.csv`, `pairs.csv`, `source_costs.csv`: `73ea5880fe536a025805926632d8be62b0ab71f155309cb706937049e509cf06`, `b9203b0ec6110d930364a16306bc6e8abf51d2b005821b7035af56c2684f5661`, `4788111b491d31031dabe6baa7dd1ae11182828013702163a29cb40ddd799e45`
- Analysis generator `make_analysis.py`: `45bcd1541226be1fcabaf8768f680aebf2d0c7867ca061a38a295feb404f5169`
- Accounting `accounting.json`: `a96c5f1ae69f3d4b066cb2b45221181bf27086a3878b33ba24667bd658278587`
- Figure PNGs `public_bound_quality.png`, `paid_times.png`: `4a5cfcf2f020023ea5aee44b06c5e6e33eb7873ded6cde3b3a2324886bc6b5c1`, `7d82edfae54924a48385118813d48d90ace6d8dd809a870ceb254b5311961d2e`
