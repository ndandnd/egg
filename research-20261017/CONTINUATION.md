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

Qualification v2 completed all 12 attempts with 160.79 worker CPU seconds plus freeze/supervisor overhead. The cohort exposed endpoint timing contaminated by watchdog cleanup and insufficient finalization reserve, so it does not pass engineering qualification and will not be used for model comparison. Full failure receipts remain in `local-qualification-v2`; raw native traces are preserved locally and backed up as verified lossless gzip archives. Analysis is `qualification-analysis-v2`.

Prospective v3 keeps identical qualification/screen cases, arms, models and seeds. It measures completion after result materialization using the shared parent clock, separates cleanup, reserves max(3s, 10% of the decision cap) for final replay/materialization, and carries all v2 costs plus 10 conservative CPU seconds for analysis/archive work into the same 0.5 CPUh qualification ceiling. See `LOCAL_CAMPAIGN_MANIFEST_V3.json` and the controlling protocol amendment. V3 qualification passed all engineering checks: 12/12 complete, no censoring or worker/infrastructure failure, 10 final replay-valid plans and two correctly recorded no-plan outcomes. This is engineering evidence only. Cumulative qualification accounting was 410.06 CPU seconds, plus 10 conservative CPU seconds for subsequent analysis/archive/readback, below the 1,800-second ceiling. See `qualification-analysis-v3`. Do not edit locked sources/assets while jobs run.

## Monitoring and backups

Existing `advance-egg-journal-research` was reactivated for this local campaign, hourly, with updated local-compute limits and this checkpoint. The app confirmed ACTIVE; no other paused automation was restarted. Milestones `b05cc056` and prospective v2 freeze `728ae96a` are pushed with author Nathan Cho <nathan.cho2013@gmail.com>. The October 2 scoped review schedule was deleted and must remain absent. Preserve old research and Google Doc history. Append consolidated verified milestones to the original Doc when useful; the six old entries are already posted, never repost them.

The original Google Doc received one verified 17 October milestone, recorded in `GOOGLE_DOC_UPDATE_20261017.md`. Historical entries were preserved.

## Active substantive screen — 17 October 2026

`local-screen-v3` is running under detached supervisor PID 93913. Authoritative launch receipt: `local-screen-v3-control/LAUNCH.json`; lock: `local-assets-v3.json`; supervisor ownership marker: `local-screen-v3/.supervisor-owner`. Started after complete v3 engineering qualification. At most two local one-thread workers; 360 registered decisions, 60 seconds each, eight CPU-hour hard ceiling. Runtime source commit `1ede7e0f`; locked sources and model assets must remain unchanged until terminal. No cluster work. Check PID/command and current ledger before acting; never infer liveness solely from the marker, never submit a duplicate.

Next wake: make one compact local status/resource check. While active, do not inspect bills to tune or select methods. On completion, run `analyze_local_campaign.py --lock research-20261017/local-assets-v3.json --runs research-20261017/local-screen-v3 --stage screen --output research-20261017/screen-analysis-v3`. Preserve all failures/censoring and create verified lossless native-trace archives as practical, retaining originals. Review frozen gates, update Git/Google Doc with substantive findings, and design the next justified bounded ML or recovery study. Read `LOCAL_MONITORING.md` for details. Manuscript work and sealed evaluation remain deferred.

## 19:07 UTC check and design package

Supervisor PID 93913 was verified alive on the recorded command. Snapshot: 125 terminal receipts, two active workers, no supervisor/resource failures; about 1.27 charged worker CPUh, peak worker RSS about 0.73 GiB. This is operational health only: no partial comparative bills were inspected or used to tune/select models. No duplicate launch, cluster access or frozen source/model change occurred.

GPT-6.1 Sol prepared `RECOVERY_IMPLEMENTATION_CONTRACT.md`, reviewed and clarified by the parent. It specifies movement-ID binary starts, no positional charging-variable transfer, independent full-case physical fallback, unrestricted-bound provenance and one shared clock. Restoring movements can split elementary charging intervals, so copying pruned continuous variables is unsafe. Retention only guarantees no worsening of the same acquired prefix witness; recovery can lose to a static solve using the whole budget. This is candidate design only, not a launch protocol or a bypass of the current promotion gate. After the cohort finishes, analyze it before deciding whether/how to implement this contract.
