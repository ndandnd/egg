Independent-review checkpoint — 17 October 2026
The 360-decision local development comparison is complete: twenty distinct synthetic timetables, three paired solver seeds and six methods at a 60-second end-to-end allowance. Graph attention, new CatBoost and the nonlearned ranking each produced 60/60 valid endpoints; random produced 59/60, the four-round full model 44/60, and the historical full-model control 59/60. Failures and the deadline-censored control remain in the evidence.

Graph attention reduced median timetable-level bills relative to the prespecified nonlearned ranking by 0.47% at 40 trips and 68.36% at 80 trips. Its gains over random were 29.76% and 19.37%; it essentially tied CatBoost at 40 trips and improved bills by 44.37% at 80. These finite-budget synthetic-development findings do not establish final-test generalization or a new generic pruning contribution. The strong size dependence deserves independent scrutiny; a pooled 33.03% figure should not replace the two size-specific results.

Independent reaggregation agrees with the final analysis. All 342 supervisor-valid physical plans replayed successfully on their original full cases, with exact bills matching and no mapping/replay/bill mismatch. All fifteen prospective gates pass; that makes recovery eligible for a separately frozen study. At the user's request, no next experiment is launched: all workers have exited and scheduled continuation is PAUSED for independent review.

The reviewer handoff contains the protocol, figures, per-group/per-cell tables, numerical check, replay audit, limitations and questions about baseline strength, data shift and novelty. Screen runtime was 3.72 CPU hours including its supervisor; closeout verification is accounted separately. Recovery remains a contract and solver-free prototype.

Reviewer handoff on GitHub

Verification: native append and chart read back once; earlier images preserved. Google Doc: https://docs.google.com/document/d/1NmPC_qo_uOnA48dV6Ibhs3Pj9EgOD-oJTBuVi41p6bg

