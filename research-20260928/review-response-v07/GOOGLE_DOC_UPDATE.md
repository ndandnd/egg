## Review response and stronger bounds — 28 September 2026

The revised research draft 0.7 is ready for author review. Claude's review correctly identified a missing analytical baseline, incomplete reporting of the economic quantities, and limitations in the capped solver-development comparisons. We have corrected those points while keeping the broader computational research objective active.

The main paper now reports physical cost D, hull cost CH, their gap and regret of each named planner incumbent together. Independent exact arithmetic confirms changed-market hull lower bounds of approximately 418.97 at depot 15 and 430.27 at depot 16, stronger than the previous computed lowers. Exact ideal-model floors remain distinct from native numerical evidence. Neither public case has a certified positive planning gap, and regret of a returned schedule does not establish regret at a planner optimum.

Combining the existing three-service own-price response with its hull evidence also tightens that example's planning-gap upper bound to 0.10 under native numerical qualifications, without another optimization. This is postprocessing of existing evidence, not a measured reuse speedup.

The main draft is 17 pages with three figures, three tables and fifteen references. Andrianesis, Madani and Hümbs have been restored with primary-source checks. A separate seven-page development supplement preserves all historical outcomes, including failures and time spent, and explains the call/arithmetic caps and unconfirmed solver-start acceptance. The no-incumbent bug was already repaired and independently tested; its historical failures are not erased or relabelled.

We have not adopted the proposed two-paper split, predictions of inevitable journal rejection, or the untested claim that changing four calls to sixteen would certify the toy in seconds. Old convergence outcomes use a different terminal-battery rule and were not imported. A cycling update rule alone would not prove absence of a supporting price.

The next research step is a scope-checked analytic baseline followed by bounded budget sizing before another comparative experiment. Independent timetable evidence and common-quality comparisons still precede ML. No new optimization or cluster allocation was used for this revision; the previously pending replacement-run decision is unchanged.

- [Read revised draft 0.7](https://github.com/ndandnd/egg/blob/c058236436fe84d83dde1f1e5769f53e5e550c5c/output/pdf/egg-journal-v0.7-reviewed-draft.pdf)
- [Historical development supplement](https://github.com/ndandnd/egg/blob/c058236436fe84d83dde1f1e5769f53e5e550c5c/output/pdf/egg-journal-v0.7-development-supplement.pdf)
- [Review response, calculations and primary literature checks](https://github.com/ndandnd/egg/tree/c058236436fe84d83dde1f1e5769f53e5e550c5c/research-20260928/review-response-v07)
