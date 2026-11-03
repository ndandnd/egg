# EGG — historical 17 October review checkpoint

**Superseded on 23 October 2026:** the user resumed research with an FT50 publication aspiration. Start at `../research-20261023/CONTINUATION.md` for the current handoff. The completed results and pause below are historical and preserved.

17 October 2026. The user requested a graceful stop at an independent-review-ready state. **The experiment is complete, no EGG campaign worker remains, and `advance-egg-journal-research` is PAUSED. Do not resume or launch follow-up experiments until the user asks.** Other paused schedules stay paused. `STOP_RECEIPT_20261017.json` records process/owner/schedule checks.

Worktree `/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017`, branch `codex/ml-prediction-20261017`. Start with `REVIEWER_HANDOFF_20261017.md`; the compact `REVIEW_BUNDLE_20261017.zip` contains the reviewer evidence. Do not reread Claude's large state map or restart unrelated old work.

## Completed results

All 360 registered decisions completed: twenty distinct synthetic development timetables (ten at 40/80 trips), three paired solver seeds, six methods, 60 seconds end-to-end each. Counts of valid endpoints /60: graph attention60, newCatBoost60, nonlearned60, random59, full4 44, cold8 59. Random has one extraction/replay-related unresolved run, full4 has sixteen no-plan outcomes, and cold has one censored endpoint. Failures remain preserved.

Graph-attention median group bill gains versus nonlearned: **0.47% at40 trips;68.36% at80**. Versus random:29.76%/19.37%; versus CatBoost:approximately0%/44.37%. The pooled33.03% statistic masks strong size dependence. These are feasible-bill differences in this synthetic development population, not optimality gaps or final generalization evidence.

`screen-analysis-v3-final/summary.json` is the successful formal analysis: all15 prespecified gates pass, decision eligibility for a separately frozen recovery study. **No recovery launch occurred because the user requested review first.** `INDEPENDENT_SCREEN_CHECK.md` recomputes key statistics with no numerical disagreement. Figures/CSVs are in `screen-analysis-v3/figures`.

`FINAL_REPLAY_VERIFICATION.{json,md}` independently replayed all342 supervisor-valid final plans on their original full cases and recomputed exact bills. All342 pass; zero mapping/replay/bill/stored-projection mismatches. The audit used51.50CPU seconds and no optimization/training. `VERIFY_REVIEW_EVIDENCE.py` preserves the audit procedure.

Algorithm screen CPU was13,408.97s=3.72CPUh including supervisor, within8CPUh. `CLOSEOUT_ACCOUNTING.json` records conservative additional analysis/packaging charges separately. A first postprocessing attempt had an output-folder collision; its failure is preserved in `screen-analysis-v3/ANALYSIS_ATTEMPT_FAILURE.json`. No experiment was rerun or data changed. Corrected qualification cost<=420.06CPU seconds including conservative allowances, below its0.5CPUh ceiling; failed qualificationv2 is preserved.

## Other completed work and limitations

Replay completion preserves independently admitted raw plans when repair fails; true-bill retention and original-vs-restricted bound provenance were fixed and independently reviewed, with58 focused tests. See `replay-fix/IMPLEMENTATION_PROTOCOL.md`.

`classical-training/RESULTS.md`: logistic/CatBoost trained on admitted TRAIN128 with80fit/16inner/32historicalouter groups. Inner-only selection; labels imitate feasible source incumbents, not optimal routes. CatBoost depth6/266trees;20.69s training wall. Graph arm is one fixed v8task00 model, not an ensemble. Shared generator/physical-profile overlap, one tariff, finite budgets, slightly differing retained counts and a single inexpensive nonlearned rule remain important limitations. Generic GNN arc pruning is existing prior art. Sealed DEV/TEST/A6/B3/confirmation/GIRO remained closed.

Recovery exists only as `RECOVERY_IMPLEMENTATION_CONTRACT.md` plus pure `recovery-prototype/` (eleven tests, exact billing). No optimizer integration or recovery experiment. Future work should follow external review, then a new prospective protocol/budget and cohort. Act as manager using GPT-6.1 Sol if resumed. Initial local limits were two one-thread workers,5GiB each/10GiB aggregate; leave Unicorn to v2g.

## Backups and communication

Commit as `Nathan Cho <nathan.cho2013@gmail.com>` (verified connected GitHub login ndandnd), using explicit per-command identity. Push only origin/codex/ml-prediction-20261017; no history rewrite, PR merge or journal submission. Preserve old branches. Source/model/case identities remain in `local-assets-v3.json` (runtime source commit1ede7e0f). Original12GB native traces and raw solver diagnostics remain local; final hash manifest identifies them. Public bundle excludes raw stdout/stderr and native variable traces.

The original Google Doc received the verified17October training milestone and final review checkpoint with figure, preserving earlier content/images. `GOOGLE_DOC_REVIEW_CHECKPOINT_20261017.md` records the latter. Never repeat the six October1 historical entries. No external reviewer has been messaged; the user can share the handoff or bundle.
