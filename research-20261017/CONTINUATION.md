# EGG local prediction research — continuation

Updated 17 October 2026. User resumed sustained research toward a strong prediction model; manuscript drafting remains secondary. Work in `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`, branch `codex/ml-prediction-20261017`, based on Claude handoff `90a61891`. Do not modify Claude's or the completed SOTA-review branches.

## Operating preferences

Act as manager, using GPT-6.1 Sol subagents for bounded implementation, analysis and routine checks. Read this checkpoint plus current protocols/receipts; avoid broad history rereads or repeated audits. Continue useful model/data/implementation work between runs; flag important scientific decisions or failures. Notify only meaningful results or decisions, not routine queued/running status.

The connected GitHub profile verified login `ndandnd` and author email `nathan.cho2013@gmail.com` (user's requested account). Use `Nathan Cho <nathan.cho2013@gmail.com>` for new commits, with explicit per-command author configuration; do not rewrite older commits. Push explicitly to this branch. No PR merge or journal submission.

Local runtime is `.venv-local/bin/python` with pinned dependencies, isolated from Claude's environment. No cluster work is needed; EGG yields to v2g/evspv2g-stochastic. Sealed DEV/TEST/A6/B3/confirmation/GIRO remain closed. Only admitted TRAIN bank groups 10000–10127 and explicitly registered new synthetic development timetables are eligible. All variants of a timetable stay in one split. The public plans inspected here are exploratory.

## Completed in this continuation

- Offline zero-solver audit: `offline-ranking/RESULTS.md`; two existing public plans replay successfully. Their learned-derived references make ranking comparisons biased; do not advertise the perfect Eberbach recall as independent evidence. All attempts/failures retained.
- New classical baselines: `classical-training/RESULTS.md`, models/receipts under `classical-training/attempt1/`. Exact admitted TRAIN128 pool, 80 fit / 16 inner / 32 historical outer groups, source-plan labels provisional. Logistic C=1 and CatBoost depth6 / 266 trees selected on inner loss only. Training took 20.69 s wall, 19.40 s CPU, one thread; no failures. Historical outer diagnostics are exploratory, not new-timetable performance.
- Replay completion and retention implemented, opt-in. Independently admitted raw and fixed-topology completed witnesses compete by true physical bill; valid witnesses survive later errors. Original MIP lower bounds remain separate from restricted completion objectives. Pricing/hull failure statuses preserve earlier valid evidence. Independent reviewer confirmed two admission/retention issues fixed. See `replay-fix/IMPLEMENTATION_PROTOCOL.md` and focused tests.
- Local campaign protocol/manifest freeze 20 independent base IDs (10 each at 40/80 trips), two separate qualification IDs, three solver seeds. Six arms compare v8, newly trained CatBoost, nonlearned ranking, random, full4 and cold8. No learned-specific gain has yet been established.

## Compute and next action

The prospective `LOCAL_CAMPAIGN_PROTOCOL.md` governs: at most two local single-thread workers initially, 5 GiB each / 10 GiB aggregate, <=0.5 CPUh qualification and <=8 CPUh screen. Every failure, scoring/completion overhead and process resource usage is recorded. Solver runs require the final asset/source lock, successful qualification and immutable receipts. No automatic retry of interrupted/unreceipted attempts. Gurobi is the actual backend; one tiny CBC check exited137 and is retained in the implementation protocol.

At this checkpoint, **no benchmark worker is running**. CatBoost/logistic training is complete. Runner interruption/resume fixes are being completed after independent review. Next: review the fixes, freeze sources/assets, run qualification, inspect its complete evidence, then launch the registered screen if its engineering gate passes. Do not compare/tune models on qualification outcomes. Source/assets must remain immutable while locked jobs run. Further datasets, recovery, ensembles and ranking losses require versioned prospective designs and grouped evaluation, not repeated selection against the same development cases.

## Monitoring and backups

Existing `advance-egg-journal-research` automation is paused at initial takeover; parent will reactivate it for this local campaign with an updated prompt and record confirmation here. The October 2 scoped review schedule was deleted and must remain absent. Preserve old research and Google Doc history. Append consolidated verified milestones to the original Doc when useful; the six old entries are already posted, never repost them.
