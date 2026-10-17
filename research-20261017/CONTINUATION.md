# EGG local prediction research — current checkpoint

Updated 17 October 2026, 20:01 UTC follow-up. Worktree `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`, branch `codex/ml-prediction-20261017`. User authorizes sustained rigorous ML research; manuscript drafting remains secondary. Use GPT-6.1 Sol for bounded implementation/review. Preserve history; do not modify Claude's or completed SOTA branches.

## Active experiment and next action

**The 360-cell local screen is still running.** Detached supervisor PID **93913** was verified alive on its recorded `experiments.codex_local_campaign run` command. Snapshot: 260 terminal receipts, two active attempts, no supervisor/resource failures; 2.58 charged worker CPUh, peak worker RSS 0.73 GiB. No partial comparative bills were inspected or used for selection.

Authoritative files:
- `local-screen-v3-control/LAUNCH.json` — exact command, PID, launch time.
- `local-assets-v3.json` — immutable source/model/case lock; runtime source commit `1ede7e0f`.
- `local-screen-v3/ledger.jsonl`, per-cell attempt/result/completion/supervisor receipts.
- `LOCAL_CAMPAIGN_PROTOCOL.md` and `LOCAL_CAMPAIGN_MANIFEST_V3.json` — prospective design and budgets.

Do not edit frozen `src/egglab`, `src/experiments` or model assets while workers run. Do not duplicate or automatically retry any attempted/interrupted cell. The owner file alone is not proof of liveness. Leave Unicorn to v2g; no cluster monitoring or submissions. Current screen: 20 distinct synthetic development timetable groups, 40/80 trips, three paired solver seeds, six arms (v8, new CatBoost, nonlearned, random, full4, cold8). At most two single-thread local workers, 5 GiB each / 10 GiB combined, 60 seconds per decision, eight CPU-hour hard ceiling. Use `.venv-local`.

Next wake: one compact local operational check. On terminal completion, run:

```
python3 research-20261017/analyze_local_campaign.py --lock research-20261017/local-assets-v3.json --runs research-20261017/local-screen-v3 --stage screen --output research-20261017/screen-analysis-v3
```

Analyze the complete cohort before choosing models or follow-ups. Preserve missingness, failures, censoring, all spent time, and group/seed dependence. The analyzer implements frozen gates and group-bootstrap uncertainty; it rejects invalid resource accounting and nonpositive-bill applicability. Review its conclusions independently. A failed gate requires diagnosis and a new justified prospective design; it does not end the user's research or justify blind expansion. This screen is development evidence, never final generalization.

## Verified completed work

- `offline-ranking/RESULTS.md`: two public saved plans replay, but learned-generated references bias ranking recall; no independent superiority claim.
- `classical-training/RESULTS.md`: logistic/CatBoost fitted to admitted TRAIN128 (80 fit / 16 inner / 32 historical outer groups), selected using inner groups only. CatBoost depth6/266 trees; source labels are observed feasible incumbents, not optimal routes. Training 20.69 s wall / 19.40 s CPU. Historical outer diagnostics are exploratory.
- Common replay completion/retention fixes: preserve independently admitted raw plans when completion fails; select by physical bill; keep original MIP bounds separate from fixed-route LP objectives. Independent review plus 58 focused tests. See `replay-fix/IMPLEMENTATION_PROTOCOL.md`.
- Qualification v2 failed timing checks; preserved completely. V3 corrected shared clock/materialization timing and finalization reserve. All 12 v3 cells passed engineering checks: ten valid plans, two recorded no-plan outcomes, no failures/censoring. Cumulative qualification charge including conservative postprocessing allowance <=420.06 CPU seconds, within 1,800-second ceiling. See `qualification-analysis-v3`; no ranking conclusions drawn from qualification.

## Work prepared while the screen runs

`RECOVERY_IMPLEMENTATION_CONTRACT.md` specifies full-case replay, movement-ID binary starts, independent physical fallback, unrestricted-bound provenance and one shared clock. Restored edges can split charging intervals; never copy source positional charge variables. Retention cannot worsen the SAME acquired prefix witness but can lose to spending the whole allowance on static solving.

`recovery-prototype/` is a pure candidate implementation outside frozen sources: subset/physics validation, independent physical replay, ID-based binary specification and provenance. It is not imported by running workers and performs no model build, optimization or start submission. Handcrafted tests only; no dataset or screen-bill reads. Independent review caught and confirmed a billing-convention correction: the canonical exact rational bill is authoritative; the float is display-only. Eleven handcrafted tests pass in `.venv-local`, including a fractional-price/load regression. This is preparation, not a promoted recovery experiment. Integration, native start acceptance, common deadline and certification remain future work after complete-screen analysis and a new frozen protocol.

## Data, backups and communication

Keep sealed DEV/TEST/A6/B3/confirmation/GIRO closed. All timetable variants stay in one split; use grouped inner-only selection. No generic learned-pruning novelty claim. No PR merge, journal submission or reset-credit redemption.

Commit with `git -c user.name='Nathan Cho' -c user.email='nathan.cho2013@gmail.com' commit ...`; this email is verified for connected GitHub login `ndandnd`. Push only `origin/codex/ml-prediction-20261017`, without rewriting history. Last pushed milestone before this follow-up: `117ba3f9`. Raw solver stdout/stderr stay local (license details); hash them. Preserve native traces locally and back up practical verified lossless archives plus compact evidence; do not stage live partial outputs. See `LOCAL_MONITORING.md`.

Hourly `advance-egg-journal-research` is ACTIVE for this worktree. Other paused schedules remain paused; the October 2 scoped review schedule stays deleted. Notify only substantive findings, important failures/decisions or review-ready results. Original Google Doc received one verified 17 October milestone (`GOOGLE_DOC_UPDATE_20261017.md`); append consolidated verified findings when useful, never repeat the six historical entries.
