# Independent native primitive acceptance review

23 October 2026. **PASS for the six declared handcrafted primitive tasks only.** This read-only check inspected compact result/supervisor/planner/fallback/completion/attempt receipts, native event records, the frozen runner's expectation checks and the latest `analysis-1792773862945301000.json`. Only relevant Gurobi MIP-start lines were inspected; no solver or experiment was run.

| Task | Independent receipt assessment |
|---|---|
| source_normal | Saved exact bill equals fallback exact bill; floating bill 59.5; source-only bound scope retained; 2 model builds / 2 native starts. |
| full_normal | Same saved physical bill, floating 59.5; full-case identity and full bound scope; 2 builds / 2 starts. |
| changed_tariff | Repriced exact bill 67; full scope; 1 build / 1 start. |
| start_setup_failure | Injected attachment rejection preserves fallback exact bill; lower remains negative infinity; 1 build / 0 native starts. |
| expired_search_deadline | Valid fallback preserved; lower negative infinity; 0 builds / 0 native starts / 0 rounds. |
| invalid_fallback | Expected physical rejection; no plan or bill admitted; 0 builds / 0 native starts / 0 rounds. |

All six supervisor endpoint checks pass with return code zero. For the invalid-fallback task this means successful completion of the expected-rejection test, **not** a valid physical plan. Normal-task Gurobi logs contain “Loaded user MIP start” in all three tasks. This is stronger evidence of native processing than the planner's deliberately conservative `solver_start_status: unknown`; it does not establish any speedup or useful ranking effect.

The fixture restores an added movement and splits compiled charging intervals from 2 to 3. Full binary inventories include the added movement at zero and selected movements at one; frozen runner checks assert unchanged bounds/row counts and omission of continuous starts. Recovery provenance carries no global lower bound. Source solve lower scope is `source_restricted_only`; full-normal/changed-tariff bounds arise from their full native tangent models (59.499999 and 66.999999 respectively), not copied source or fixed-route LP bounds. Negative-infinity fallback-only values are not finite certificates despite the result's domain label.

Hash binding checks passed: all **146 frozen source hashes** match current bytes; campaign/attempt/completion/supervisor lock hashes agree; all six completion receipts bind the corresponding result bytes; analysis hashes bind all six native stdout logs. Every completion monotonic timestamp lies within the declared 30-second task allowance. Supervisor endpoint elapsed times range from 0.0804 to 0.2387 seconds. The analysis reports 66.8801 charged CPU seconds including its declared analysis allowance, below the 900-second ceiling; this review did not independently remeasure historical CPU usage.

The normal and failure-task exact bill strings agree with their saved fallback strings. Floating 59.5 is a fixture expectation; the quadratic-market exact rational stored for that case reflects binary floating coefficients and is not being asserted equal to the rational 119/2. Changed-tariff exact bill is 67. Saved replay receipts pass; this review did not independently rerun physical replay.

**Scope limitation:** the handcrafted recovery primitive is qualified under these declared checks. The 40/80-trip campaign harness remains pending. No statement about prediction efficacy, recovery superiority, public-network transfer, optimal physical fleet size, or hard wall-time behavior on larger models follows from this result.
