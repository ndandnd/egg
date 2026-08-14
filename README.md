# egg — price formation for indivisible mobile flexibility

Research repository for a PhD-thesis program on the **price-maker electric
vehicle scheduling problem (EVSP)**: a timetabled, trip-covering electric
fleet whose charging (and V2G discharge) load is large enough to move the
electricity price it faces — the "chicken-and-egg" feedback
`price -> schedule -> load -> price`.

Working umbrella title: *Price formation for indivisible mobile flexibility:
from benevolent dictator to market.* The two endpoints already exist as
separate projects: **EVSP-DR** (exact price-taking EVSP, Swedish bus data)
and **evspv2g_dp** (Cho, Lodi, Scaglione, arXiv:2508.06752 — the
benevolent-dictator microgrid with V2G + solar + storage, via column
generation). This repository develops everything in between: decomposition as
price formation, the welfare ladder (uncontrolled / price-taker / strategist
/ planner), mechanism design for one indivisible bidder, and V2G/locational
extensions.

## Current status (2026-08-14)

> **Initial literature review v1: breadth complete; verification and
> flagship-specific review pending.** (Closure record:
> `ref/SEARCH_LOG_20260814.md`.)

Evidence limits: only the 17 supplied papers are full-text audited; all other
catalogued works (305 of 322) are abstract-level or grey and must be verified
before manuscript use. The flagship first paper is **recommended but not yet
selected** (`ref/RESEARCH_DIRECTIONS.md` Section 4). No solver code exists in
this repository yet.

## Layout

- `ref/` — all literature and research-planning material (see reading order
  below). Sources for the audited papers: `ref/papers/`. Tooling:
  `ref/tools/bibliography.py` (validates `papers.csv`, regenerates the
  index).
- `doc/` — LaTeX write-ups, presentations (future).
- `result/` — figures, tables, experiment outputs (future).
- `src/` — code, runnable locally and on the Unicorn cluster (future; the
  EVSP-DR and evspv2g_dp solvers remain separate repositories used as
  oracles).

## Canonical reading order

1. `HANDOFF.md` — zero-context orientation (start here).
2. `ref/RESEARCH_DIRECTIONS.md` — live hypotheses, directions, decisions.
3. `ref/BRAINSTORM_20260814.md` — the idea catalog (B1-B34) and recommended
   thesis arc.
4. `ref/NOVELTY_MATRIX.md` — why the claim is unoccupied (all 77 identified
   core-threat works scored).
5. `ref/LITERATURE_INDEX.md` + `ref/papers.csv` — the full 322-work catalog.
6. `ref/review_notes/` — paper-level audits and scan reports.
7. `ref/READING_QUEUE.md` — what to acquire and audit next.
8. `ref/context/` — historical handoffs and archived prior context
   (provenance; superseded where marked).

## Working rules

- Evidence tiers are load-bearing: never promote an abstract-level claim
  into a manuscript without a full-text audit.
- Never fabricate bibliographic identifiers; copy verbatim or leave empty.
- Every new close paper gets a `NOVELTY_MATRIX.md` row before conclusions
  are drawn from it; any row reaching Y-Y-C-a on Duties x EndogP x Exact
  escalates immediately.
- Repository boundary: EVSP-DR and evspv2g_dp code is called as adjacent
  oracles, not copied here (see `ref/context/HANDOFF_PRICE_MAKER_20260814.md`
  Section 7).
