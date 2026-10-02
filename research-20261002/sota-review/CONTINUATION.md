# EGG final review handoff — 2 October 2026

Finalized after **2026-10-02T17:00:00Z**, the requested 1 p.m. New York cutoff. The bounded review is complete and its scoped automation was deleted through the app. All subagents are complete; no new research or cluster check started after the cutoff. Read this handoff first; the report and linked notes hold completed findings. Git history preserves earlier checkpoints.

## Scope and ownership

- Work only in `/Users/nadan/Documents/ChatGPT/egg/sota-review-20261002`, branch `codex/sota-review-20261002`. It branched from Claude commit `c560378adc84ef010afe5c4b1bfce0408dd1704b`; the newer takeover handoff at `ff2299f9` was read without changing Claude's branch.
- User confirmed Claude paused around 05:30 UTC and GPT owns the project/cluster. The former 17:45 UTC transfer/no-SSH restriction is superseded. Older paused automations remain paused.
- No sealed DEV/TEST/A6/B3/confirmation/GIRO access; no PR merge, submission or new solver/training launch during this review. Later experiments need frozen prospective protocols/resources.
- Act as manager; use **GPT-6.1 Sol** for bounded substantive and routine tasks with short self-contained handoffs. Check active workers; avoid full-history forks, duplicate searches and repeated audits.

## Live cluster state

At **15:02:19 UTC**, the E11 queue and priority-project entries were empty. Scoped accounting at **15:02:49 UTC** showed all **96 tasks COMPLETED/0:0**. No jobs or priorities changed. Newly completed tasks 74–95 and previously unavailable historical raw tasks 0–71 were collected once; combined with the earlier 72/73 archive, all 96 command/result keys and source versions reconcile without duplicates or missing outputs. Archives, member hashes, failures and accounting are preserved in `evidence/E11_FINAL_COLLECTION_20261002.json`; `evidence/analyze_e11_archives.py` reproduces the local summaries without extraction, code execution from archives or solver/replay calls.

**New substantive finding:** learned keep .15 wins 23/24 pairs against each baseline; keep .30 wins 24/24. These descriptive counts rank finite reported bills above failures. Both-finite comparisons also favor learned arms. Finite-bill counts are cold 21/24, cold4 9/24, keep .15 23/24 and keep .30 24/24. All failures remain visible. This strengthens conditional solver-seed repeatability, not learned-specific superiority or public transfer. `notes/E11_FULL_COHORT_ANALYSIS.md` contains the full denominators and per-cell summaries.

Exact-source checks at logged commit `711c3d7` establish **four progenitor groups**, with same-ID 60-trip cases prefixes of 80-trip cases. Seeds and sizes are correlated repeats. Case creation is outside the timer; extraction/replay can overrun; a later extraction exception can discard an earlier internal incumbent. `notes/E11_INTERPRETATION_REVIEW.md` preserves these limitations. No independent physical replay was done. The main review incorporates this completed cohort and retains the reliability-first, classical-comparator-first recommendation.

E11 is complete and fully collected: do not recheck its queue or recollect artifacts on later wakes. No new EGG job is authorized during this review.

For any later authorized cluster phase, EGG yields to nc437 jobs named `v2g*` or commented `evspv2g-stochastic`. Never change other projects' jobs, release explicit holds or duplicate/resubmit work. Exclude `scaglione-compute-01`; the inherited ceiling was 6–8 Gurobi processes. The existing `~/egg-claude-20261001/yield_check.sh` was inspected at takeover: pending EGG arrays get Nice10000/throttle1 while v2g has work. No background loop restarted.

## Completed — do not repeat

- **Six Google Doc entries done**, verbatim/in order, verified against current unchanged source hash. `GOOGLE_DOC_APPEND_RECEIPT.json` records preserved content/styles and 7 inline objects. Do not repost or rewrite historical claims.
- **`SOTA_REVIEW.md` covers all six handoff questions**, primary-source/access distinctions, ranked five studies, effort/CPU estimates, stop/go, do-not-pursue directions and honest OR assessment. It is a review, not a completed journal contribution.
- All five designs are written/challenged: numerical reliability 35–50 CPUh; recoverable pruning **45–60**; matched oracle allocation 45–55; learning signals 55–70; charging-route relaxation 20–40. None ran. Manifests, mappings, some thresholds and runtime feasibility remain launch prerequisites.
- Rank2's final amendment: **six arms, 540 runs, 41.4 estimated solver CPUh, hard 60 CPUh ceiling**, adding matched nonlearned greedy widening. This supersedes the unexecuted five-arm/50 CPUh design. No concurrency change. All arms pay for common fallback acquisition; unused learned scoring is not charged to full/classical arms.
- `notes/FINAL_CONTRIBUTION_CHALLENGE.md` is integrated: repaired classical comparator before expanded training; allocation versus stronger pricing chosen from measured bottlenecks; meaningful economic endpoints; promotion screens are not originality gates.
- The 10:01 UTC consolidation is complete and parent-reviewed. Sol6.1 edited only opening/status/closing; the parent tightened the comparator claim and bottleneck wording. No new scientific claim was introduced. All workers in this package have completed.
- At 16:01 UTC, Sol6.1 checked the new E11 extraction-failure finding against the numerical reliability design. The existing protocol already covers earlier-incumbent retention, explicit failure without an accepted candidate, no-time termination and complete pipeline timing. No amendment was needed; the later prelaunch implementation check must verify those requirements. No cluster check or new investigation was repeated.

## Scientific boundaries already reviewed

- Gerbaux/Desaulniers/Cappart2025 already has GNN/greedy bus arc selection and incoming/outgoing top-m; Sugishita/Grothey/McKinnon2024 learns CG dual warmstarts. Generic pruning or ML+CG is not novel.
- Global pricing lower bounds, feasible candidates and restricted-master values have different directions. Hull lower bounds subtract an upper conjugate enclosure. Candidate regret, planning non-support and price selection are distinct conclusions.
- Joint cached-price bounds, fleet energy/opportunity constraints, aggregate-load prior art and the inexact-oracle interface are derived/reviewed in linked notes. Standard inequalities are not claimed as new theory. Do not redo these packages.
- Route relaxation requires physical mapping with nonincreasing price objective, including signed prices/shared charging. Incomplete-CG correction needs global reduced-cost coverage and justified route mass. Exact route LP need not equal full-fleet hull. Small-case comparison uses an early checkpoint, retains zero-error ties and treats missing references as inconclusive.
- Kiwiel–Lemaréchal institutional full text was inspected with OCR/version limits; ConPaS final text retrieved. De Oliveira–Sagastizábal remains abstract-only after three bounded access routes; do not repeat them. Other access limits are in the report/notes.

## Next implementation and final status

The requested review is complete. E11 collection is complete; do not repeat its queue check or artifact analysis. The first later implementation action is common replay reliability, followed by the six-arm learned-versus-classical comparison. Freeze missing manifests, mappings, acceptance thresholds and resource accounting before any launch. The five studies are conditional options, not an automatic queue. The promising seed result does not remove the classical comparator or independent evaluation requirement.

Consolidated review commit `e22420e1`, initial two-task collection `ee0e90bc`, and full-cohort milestone **`ae5d6181`** are pushed to `origin/codex/sota-review-20261002`. The full cohort, reproducible analysis, interpretation checks and report updates are backed up. Final report status and this handoff are included in the closing backup. Commit only review deliverables; `tmp/` is scratch and stays untracked. Never reset/overwrite Claude's branch.

Scoped automation **`egg-literature-review-until-1-p-m` was deleted**, confirmed by the app after the cutoff. Older schedules remain paused. The six Google Doc entries are already done and must not be reposted. Latest cluster evidence remains the completed/reconciled E11 cohort observed at 15:02 UTC; no fresh queue inspection was necessary. Ending this bounded review does not revoke project ownership or change standing data/priority restrictions. No new schedule was created.
