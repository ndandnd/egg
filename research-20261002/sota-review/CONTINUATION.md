# EGG review continuation — ends 2 October 2026 at 1 p.m. New York

Updated during the 10:01 UTC follow-up. Deadline: **2026-10-02T17:00:00Z**. Read this compact checkpoint first; the report and linked notes hold completed findings. Git history preserves earlier detailed checkpoints.

## Scope and ownership

- Work only in `/Users/nadan/Documents/ChatGPT/egg/sota-review-20261002`, branch `codex/sota-review-20261002`. It branched from Claude commit `c560378adc84ef010afe5c4b1bfce0408dd1704b`; the newer takeover handoff at `ff2299f9` was read without changing Claude's branch.
- User confirmed Claude paused around 05:30 UTC and GPT owns the project/cluster. The former 17:45 UTC transfer/no-SSH restriction is superseded. Older paused automations remain paused.
- No sealed DEV/TEST/A6/B3/confirmation/GIRO access; no PR merge, submission or new solver/training launch during this review. Later experiments need frozen prospective protocols/resources.
- Act as manager; use **GPT-6.1 Sol** for bounded substantive and routine tasks with short self-contained handoffs. Check active workers; avoid full-history forks, duplicate searches and repeated audits.

## Live cluster state

At **10:02:50 UTC**, E11 `798833_[72-95%1]` was pending for Priority, still 24 tasks remaining. Priority project had 126 running and 9 pending job entries. No EGG work ran; no jobs/priorities changed. E11's 72/96-run conclusions remain interim.

EGG yields to nc437 jobs named `v2g*` or commented `evspv2g-stochastic`. Never change other projects' jobs, release explicit holds or duplicate/resubmit work. One compact queue check per wake through `unicorn2`, after sourcing `/etc/profile.d/slurm.sh`, is sufficient; use scoped accounting if 798833 disappears. Collect newly completed E11 evidence only if available. Exclude `scaglione-compute-01`; inherited ceiling is 6–8 Gurobi processes. The existing `~/egg-claude-20261001/yield_check.sh` was inspected at takeover: pending EGG arrays get Nice10000/throttle1 while v2g has work. No background loop restarted.

## Completed — do not repeat

- **Six Google Doc entries done**, verbatim/in order, verified against current unchanged source hash. `GOOGLE_DOC_APPEND_RECEIPT.json` records preserved content/styles and 7 inline objects. Do not repost or rewrite historical claims.
- **`SOTA_REVIEW.md` covers all six handoff questions**, primary-source/access distinctions, ranked five studies, effort/CPU estimates, stop/go, do-not-pursue directions and honest OR assessment. It is a review, not a completed journal contribution.
- All five designs are written/challenged: numerical reliability 35–50 CPUh; recoverable pruning **45–60**; matched oracle allocation 45–55; learning signals 55–70; charging-route relaxation 20–40. None ran. Manifests, mappings, some thresholds and runtime feasibility remain launch prerequisites.
- Rank2's final amendment: **six arms, 540 runs, 41.4 estimated solver CPUh, hard 60 CPUh ceiling**, adding matched nonlearned greedy widening. This supersedes the unexecuted five-arm/50 CPUh design. No concurrency change. All arms pay for common fallback acquisition; unused learned scoring is not charged to full/classical arms.
- `notes/FINAL_CONTRIBUTION_CHALLENGE.md` is integrated: repaired classical comparator before expanded training; allocation versus stronger pricing chosen from measured bottlenecks; meaningful economic endpoints; promotion screens are not originality gates.
- The 10:01 UTC consolidation is complete and parent-reviewed. Sol6.1 edited only opening/status/closing; the parent tightened the comparator claim and bottleneck wording. No new scientific claim was introduced. All workers in this package have completed.

## Scientific boundaries already reviewed

- Gerbaux/Desaulniers/Cappart2025 already has GNN/greedy bus arc selection and incoming/outgoing top-m; Sugishita/Grothey/McKinnon2024 learns CG dual warmstarts. Generic pruning or ML+CG is not novel.
- Global pricing lower bounds, feasible candidates and restricted-master values have different directions. Hull lower bounds subtract an upper conjugate enclosure. Candidate regret, planning non-support and price selection are distinct conclusions.
- Joint cached-price bounds, fleet energy/opportunity constraints, aggregate-load prior art and the inexact-oracle interface are derived/reviewed in linked notes. Standard inequalities are not claimed as new theory. Do not redo these packages.
- Route relaxation requires physical mapping with nonincreasing price objective, including signed prices/shared charging. Incomplete-CG correction needs global reduced-cost coverage and justified route mass. Exact route LP need not equal full-fleet hull. Small-case comparison uses an early checkpoint, retains zero-error ties and treats missing references as inconclusive.
- Kiwiel–Lemaréchal institutional full text was inspected with OCR/version limits; ConPaS final text retrieved. De Oliveira–Sagastizábal remains abstract-only after three bounded access routes; do not repeat them. Other access limits are in the report/notes.

## Next and deadline

The requested review is substantively complete. Address another gap **only if new evidence can change a recommendation**. Do not invent work or repeat reviews to fill the window; no more subagent/editorial campaigns are needed for unchanged state. Preserve the compact E11 check and keep unchanged state quiet. The first later implementation action is common replay reliability, followed by a meaningful learned-versus-classical comparison; the five studies are conditional options, not an automatic queue.

All meaningful milestones are pushed to `origin/codex/sota-review-20261002`; latest prior package `7b4be468`. Commit only review deliverables; `tmp/` is scratch and stays untracked. Never reset/overwrite Claude's branch.

Scoped automation: `egg-literature-review-until-1-p-m`, hourly through 17:00 UTC. At/after 17:00 UTC start no new research; record final review/cluster state, back up artifacts, **delete this scoped automation**, and report the final deliverable. Keep older schedules paused. Ending this bounded review does not revoke project ownership.
