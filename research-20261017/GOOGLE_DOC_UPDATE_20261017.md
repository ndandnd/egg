Local ML campaign resumed — 17 October 2026
EGG has resumed on the Mac, leaving Unicorn available to v2g. The immediate scientific question is whether learned connection ranking improves replay-valid bills beyond the benefit of reducing the optimization model. Existing learned-generated reference plans cannot answer that question by themselves.

New logistic-regression and CatBoost baselines were fitted to the admitted 128-group TRAIN bank, preserving the historical 80-fit / 16-inner / 32-outer timetable split. Selection used inner groups only. The selected CatBoost model (depth 6, 266 trees) had historical outer log loss 0.0787 and average precision 0.8243, versus 0.1256 and 0.5913 for logistic regression. Total training took 20.69 seconds on one native thread. These are exploratory diagnostics against observed feasible-incumbent edges, not evidence of optimal routing or independent final-test performance.

The solver now optionally rounds qualified routing decisions and completes charging on fixed routes within the original deadline. Independently replay-valid raw plans are preserved if completion fails, and the best valid plan is retained across rounds. Original global bounds remain separate from fixed-route completion objectives. Focused tests and independent code review are complete.

Before campaign outcomes, a local comparison was registered: 20 distinct synthetic development timetables (10 each at 40 and 80 trips), three paired solver seeds, six arms (graph attention, new CatBoost, a nonlearned ranking, random pruning, and two unpruned controls). All restricted arms use the same retention policy; actual retained counts and all scoring/repair overhead will be reported. Two separate timetables are used only for engineering qualification. The screen has a hard eight CPU-hour envelope, two single-thread workers, and sealed evaluations remain untouched. No benchmark conclusion is available yet.

Protocols, trained models, source hashes and failure receipts are on branch codex/ml-prediction-20261017 in github.com/ndandnd/egg. Commits use Nathan Cho <nathan.cho2013@gmail.com>. Next steps are to complete engineering qualification, run the fixed comparison, then use its evidence to design recovery after pruning and subsequent model/data improvements.

Verification: appended verbatim once to original Google Doc; exact text read back successfully. URL: https://docs.google.com/document/d/1NmPC_qo_uOnA48dV6Ibhs3Pj9EgOD-oJTBuVi41p6bg

