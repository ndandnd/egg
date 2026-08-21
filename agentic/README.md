# `agentic/` — continuity pack for the `egg` research programme

**If you are an LLM or a collaborator picking this up cold, read this file, then
`01_STATE.md`, then `02_AFTER_BREAK.md`. In that order. Nothing else first.**

Written 2026-08-21 by Claude (Opus 5), at the end of a long working session, so
that the programme survives the loss of the laptop the session ran on. Every
operational document that had been living untracked on one machine is now here.

## Why this folder exists

For two days the project's real operating knowledge — current state, task
briefs, review verdicts, an operator runbook for a one-shot recovery — lived in
untracked files in one working tree. That defeated the purpose of writing them.
This folder is the fix: it is committed, so a fresh `git clone` gets everything.

## What is here

| Path | What it is |
| --- | --- |
| `01_STATE.md` | Where the programme actually is: what is proven, what is open, every PR with its exact head and CI state |
| `02_AFTER_BREAK.md` | The first thing to run when you return, what the output means, and the decision tree |
| `03_RESEARCH.md` | The scientific programme: what is established, what the next experiments are, the novelty position |
| `04_LESSONS.md` | Hard-won engineering lessons from this campaign. Read before writing code or dispatching agents |
| `05_THREAT_MODEL.md` | The bounded integrity claim, in the wording an external reviewer supplied |
| `A6_RECOVER2_OPERATOR_RUNBOOK_20260821.md` | One-shot A6 recovery: read-only preflight plus the single exact command |
| `DEEP_RESEARCH_20260820.md` | Literature sweep: novelty verdicts, market-calibration route, ML design contract |
| `handoffs/LLM_HANDOFF_EGG_20260820.md` | The long-form master handoff (~1200 lines). The science chapters (1–7) are the durable part |
| `task_briefs/` | Every agent task brief written this campaign, reusable as templates |
| `review_requests/` | The adversarial review request template that actually found real defects |

## The three things to know before you touch anything

1. **The flagship population is complete and audited.** A 60-cell B3 factor
   pilot finished, all 60 Slurm tasks `COMPLETED 0:0`, the hardened audit
   returned PASS, and its raw tree is pinned by an outcome-blind digest
   (`efc5ca31…`, 363 files). **The preregistered analysis has deliberately NOT
   been run and no decision has been frozen.** That is not an oversight; it is
   what keeps every code review of the analyzer outcome-blind.

2. **Seeds are a one-shot resource.** 0–15 are burned by the B2/B3 populations,
   16–31 by the A6 holdout, **32–37 are the only reserved fresh seeds for the B3
   confirmation**, 38–47 are the last reserve. Spending 32–37 on an invalid
   design or a forged authorization permanently costs the flagship its
   confirmatory arm. Several open PRs exist specifically to make that
   impossible; none of them is merged.

3. **Never accept a self-reported test count.** CI exists (CBC-only GitHub
   Actions). This campaign repeatedly saw agents — and the assistant writing
   this — report green while CI was red or while a claim was simply false. If a
   number is not from a CI run on the exact head, it is not evidence.

## The non-negotiables, inherited and re-earned

- Inspect primary repo/run evidence before trusting any summary, including this
  one.
- Never score an incomplete or validity-failed population.
- Never substitute seeds or change a frozen grid after seeing outcomes.
- Keep A6, B3 and B31 evidence streams separate.
- A PR's author may repair it; only a **non-author** may review it.
- Do not merge or pull on the cluster while an `egg` array is running.
- Available compute is not a scientific decision rule.
