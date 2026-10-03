# Google Doc updates for the research log — POSTED

All six entries below were appended verbatim and in order by GPT on 2 Oct 2026 04:55 UTC
(receipt: `research-20261002/sota-review/GOOGLE_DOC_APPEND_RECEIPT.json` on branch
`codex/sota-review-20261002`). Do not repost. Verified present by Drive full-text search
on 3 Oct 02:45 UTC.


The research log is https://docs.google.com/document/d/1NmPC_qo_uOnA48dV6Ibhs3Pj9EgOD-oJTBuVi41p6bg/edit.
This session has only the Google Drive connector (read/create), not the Google Docs
editor, so these updates cannot be appended in place yet. Once the Docs connector is
enabled they will be appended verbatim; until then this file is the record.

---

## Claude takeover — 1 October 2026

Codex schedules are paused. Claude (Opus 5.5) is running the research for about 1.5
days on branch `claude/research-20261001` (independent of the Codex branch).

**Assessment.** The theory is correct and is the strongest contribution. The learning
campaign had three gaps: no matched-wall-time comparison with cold solving; training
where cold solving is already fast (20-28 trips); and no price-support evidence,
because all 32 v7 hull controls failed on a keyword typo. Full text:
`doc/CLAUDE_ASSESSMENT_20261001.md`.

**v8 longer training (collected).** Graph attention trained up to 900 epochs reproduces
the v6 300-epoch anchor exactly and improves held-out ranking substantially: log loss
0.0543 vs 0.0719, average precision 0.899 vs 0.843, top-k recall 0.764 vs 0.740. It
now beats every tree model. Most runs were still improving at epoch 900.

**E1, topology vs tariff (saved v7 data).** Across 16 timetables, the bus count never
changes with the tariff, but the route topology changes in 14/16: under the midday-
cheap tariff the solver adds depot visits and doubles midday charging. This explains
the v7 learned-route loss: training labels come from only two (flat and evening-cheap)
tariffs.

## Takeover update 2 — 1 October 2026, 08:25 UTC

**Price support on the 16 v7 timetables (E0, hull typo fixed).** 14/16 hulls certify
in 3-75 s. 4/16 timetables have a certified strictly positive physical-minus-hull gap
(no fleet is supported by its own marginal prices); gaps are <= 0.1% of the bill.

**Cold solving vs size (E2, 18 cells).** The fleet MIP is solved in seconds at the
bank's 20-28 trips but leaves 2-79% gaps after 600 s at 60-80 trips; one 80-trip best
plan uses 30 buses. ML acceleration has a real target beyond ~40 trips.

**Learned pruning (E3).** Keep the 30% of connections the v8 graph model scores
highest, then solve. On the 16 bank timetables: beats random pruning on 15/16
(~28% cheaper), beats LP-relaxation ranking 8/7/1, small wins over cold (concentrated
on the two hard timetables). At 40-80 trips with a 60 s budget (interim, 12 cases):
learned beats cold 10/12 and LP and random 12/12; at 80 trips cold returns 25-32-bus
plans while learned pruning returns 4-6-bus plans 3-4x cheaper. Part of that gain is
pruning itself (random pruning also beats cold at 80 trips); learned beats random by a
median 24%. 300 s results and a four-round-policy comparison are running. A harness
bug that discarded plans when a late solver round had no time left was found and
fixed; affected cells are rerun once and reported separately.

## Takeover update 3 — 1 October 2026, 10:30 UTC: learned pruning on public timetables

On the two public Hildenbrand depots (37 services) and the 105-service Eberbach network
(10,359 movements; never solved before), keeping the 30% of connections the synthetic-
trained v8 graph model scores highest and then solving with a four-round
outer-approximation split (`learned4`) gives the best bill of every arm in all 6 cells
(180/600 s Hildenbrand, 600/1800 s Eberbach). It beats the same solver without pruning
6/6: 0.9-4.2% cheaper on Hildenbrand; on Eberbach 76% cheaper at 600 s (the unpruned
solver finds only a 44-bus plan) and 3.1% at 1800 s. Learned pruning at 600 s beats
unpruned solving at 1800 s. The model never saw a public network, so this is a real
transfer result. LP-relaxation ranking is 6-25% worse; random pruning loses buses.
One run per cell, synthetic midday-cheap tariff; no plan is certified optimal.

E4 relabelling finished (879/896 cold solves under 7 tariffs per timetable, 6.9 CPU-h;
median 4 distinct route topologies per timetable). Tariff-diverse training is running.

## Takeover update 4 — 1 October 2026, 12:30 UTC: tariff-diverse training works

E4 retrained the graph-attention route scorer with labels under 7 tariffs per
timetable (6 training tariffs + the original two source fleets) instead of two, holding
out the midday-cheap `day` tariff entirely. On held-out `day` labels it improves average
precision and log loss in 4/4 folds (AP 0.850-0.866 vs 0.828-0.852). Decoded into
physical fleets on the 16 v7 timetables, it halves the mean bill gap to the cold
solver (+18.2 -> +8.6), buys 12 kWh more in cheap midday hours, and on average beats the
v7 source-reuse policy (-0.8), which no earlier learned arm beat. The 40-80-trip learned
pruning results are final: learned beats cold 10/2 (60 s) and 9/1/2 (300 s) and beats
LP and random pruning 12/12. Next: keep-fraction sweep (E6) and pruning with the
tariff-aware model (E7).

## Takeover update 5 — 1 October 2026, 13:30 UTC: more aggressive pruning is better

E6 swept the fraction of connections kept by learned pruning (15%, 30%, 50%) on the 12
scaled 40-80-trip cases. Keeping only 15% is best: it beats unpruned solving on 12/12
cases at both 60 s and 300 s (median -6%), and at 80 trips at 300 s it produces the best
plan on all four instances. The earlier plateau at 30% came from the pruned problem
still being too large to solve, not from discarding needed connections. E8 now tests 5%
and 10% and applies aggressive pruning to the public Hildenbrand and Eberbach cases.

## Takeover update 6 — 1 October 2026, 16:35 UTC

**Learned plans make price-support computation cheaper (E9).** Seeding the complete-
fleet convex-hull computation with the learned pruned plans tightens its enclosure on
10/10 scaled cases in the same 600 s (width ratio 0.08-0.63 at 40 trips, 0.31-0.58 at
60, 0.38-0.55 at 80) and certifies one case that the unseeded hull cannot. Gaps still
contain zero at 40-80 trips; certifying them needs a stronger pricing oracle.

**How hard to prune depends on distribution shift (E8).** On synthetic cases the best
fraction shrinks with size (5% at 80 trips); on the public networks the model is less
reliable and 30% is best in every cell (5% is 17-19% worse). E10 tests a per-trip rule
(keep each trip's top-m options) that should scale without a global fraction.

**Tariff-aware scores (E7)** help large synthetic cases at short budgets but are worse
on all six public cells; the v8 model stays the default for public networks.
