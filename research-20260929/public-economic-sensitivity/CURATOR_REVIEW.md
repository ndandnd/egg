# Curator review

**Initial status: blocked before using this curator to admit results; resolved below before publication.** The eight ordered cell rows and all 24 stage slots are retained, including missing stages. Native D/CH combination uses compatible intervals and the intended endpoint tightening. Regret is emitted only when the response's planner hash matches the admitted planner's plan hash. The analytical floor remains a separate exact value, and decimal outputs use directed rounding.

1. **The global integrity gate does not verify the sealed artifact manifest.** `_global_integrity()` checks summary counts and the supervisor/wrapper status flags, but `summarize.py` never reads `MANIFEST.json` or compares its byte counts and hashes ([summarize.py](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/research-20260929/public-economic-sensitivity/summarize.py:99)). A changed summary or per-stage assessment can therefore be admitted while the original supervisor receipt still says `stable_seal=true`. Validate manifest coverage and hashes before setting global integrity true; otherwise keep every interval inadmissible.

2. **The conditional ideal-gap upper bound lacks its required witness-feasibility gate.** The plan says the conditional bound is permitted only when the native upper witness is feasible in the ideal model ([RESULT_REVIEW_PLAN.md](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/research-20260929/public-economic-sensitivity/RESULT_REVIEW_PLAN.md:26)). The implementation instead sets `conditional = D_upper - ideal_floor` whenever an admitted D interval has `D_upper >= ideal_floor` ([summarize.py](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/research-20260929/public-economic-sensitivity/summarize.py:302)). It neither checks ideal-model feasibility of that witness nor ties the endpoint to the replayed executable witness cost. Leave this field unset unless that condition is evidenced.

3. **Paid child time can disappear on a summary/receipt mismatch.** The compact row takes `child_wall_s` only from the summary row; it checks the receipt's elapsed time against that value for admission but does not retain the receipt's elapsed time separately ([summarize.py](/Users/nadan/Documents/ChatGPT/egg/journal-research-work/research-20260929/public-economic-sensitivity/summarize.py:133)). For a missing summary row with an existing receipt, or a mismatch that correctly blocks admission, the actual paid time is omitted. Preserve `receipt.elapsed_seconds` in each stage row even when the stage fails admission.

## Resolution before result curation

The implementer added full manifest coverage/size/hash verification, preserved
receipt elapsed time separately from the summary and as the paid-time fallback,
and left the ideal-gap upper field null without an independently verified ideal
witness. Root inspected these changes. The implementer reports the focused
manifest-rejection and paid-time checks passed; no new native qualification was
run. The earlier mathematical expression remains a conditional calculation,
not a claim that native tolerance-based replay proves ideal feasibility.

The subsequent independent actual-result review passed all primary admission,
identity, accounting and interval/regret checks; see
`results-attempt1/INDEPENDENT_REVIEW.md`. Original findings above describe the
pre-fix source and are preserved as history.
