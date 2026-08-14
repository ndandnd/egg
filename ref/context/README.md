# Archived context from adjacent repositories

This directory preserves research context that informed the `egg` project.
The files are snapshots, not active source code and not a signal that the two
repositories should be merged.

- `CLAUDE_HANDOFF_PRICE_MAKER_20260813.md` is a verbatim archive of Claude's
  original price-maker handoff from `EVSP-DR`.
- `evsp_dr/CURRENT_RESEARCH_PLAN_20260810.md` is the corrected EVSP-DR research
  plan used to qualify claims about exactness, tariffs, and current results.
- `evsp_dr/HANDOFF_20260810.md` is the historical operational handoff. Any job
  state or run identifier in it must be treated as a dated snapshot, not as
  current cluster state.

The live EVSP-DR source of truth remains:

`/Users/nathan.cho/Documents/demandResponse/EVSP-DR`

At the time this archive was made, the relevant live branch and commit were
`peel-and-price` at `b50d648`. Re-verify both before relying on implementation
details because that adjacent repository may continue to evolve.

Copy verification on 2026-08-14:

| Snapshot | SHA-256 |
|---|---|
| `CLAUDE_HANDOFF_PRICE_MAKER_20260813.md` | `baeb3e179db74b8a4243b4ecde112f2761d436261adc4b2f6a739c9ecd0d9385` |
| `evsp_dr/CURRENT_RESEARCH_PLAN_20260810.md` | `37872756ab3636d93e2a90c3f1beeb9cb4ae63e6160ef54266eccc08657e7dcc` |
| `evsp_dr/HANDOFF_20260810.md` | `87808038ddfd2cffe8de9cac59d9ccbfd3b72fee13727da22d45d12bcd4df7ea` |
