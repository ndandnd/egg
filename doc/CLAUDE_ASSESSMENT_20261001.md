# Independent assessment of the EGG learning campaign

1 October 2026, Claude (Opus 5.5), on branch `claude/research-20261001`
(forked from `2d66b55`, the Codex pause commit). Codex schedules remain paused;
the Codex branch `codex/journal-research-20260927` is not modified by this work.

This assessment was written before any new computation. It uses the handoff
packet (`doc/CLAUDE_RESEARCH_HANDOFF_20261001.md`), the v5/v6/v7 result reports,
the v7 cost diagnosis, the generator `src/egglab/physical_learning_cases.py`,
the v7 driver/module, and prior review of drafts v0.5–v0.9.

## Established findings

1. **Theory (paper Sections 3–5).** The complete-fleet support results, the exact
   two-service constructions (quadratic and ramp-constrained two-generator), the
   replication family and the dual-coordination interpretation are correct. I
   re-derived or independently recomputed every headline number in earlier
   reviews (including an LP re-solve of the generator example).
2. **Edge ranking.** Graph models rank incumbent movements better than tree models
   (top-k recall 0.740 vs 0.694) on 128 TRAIN timetables. This is a repeatedly
   inspected cross-validation result, not a held-out claim.
3. **Physical outcome (v7).** On 16 TRAIN timetables under the `day` tariff, no
   learned arm beats the cheapest-source reuse policy on average, and **cold
   solving beats the source policy on all 16** (by 0–35 cost units). The learned
   loss is entirely charging allocation: same fleet size, but the graph arm buys
   17.1 kWh less in the cheap periods.
4. **Missing paper quantities.** All 32 v7 hull controls failed on a keyword typo
   (`pool_tol` vs `pool_tolerance`, `src/egglab/physical_route_proposal_v7.py:129`).
   The campaign therefore produced no physical-minus-hull gap or regret evidence.

## Plausible explanation for (3), from the generator itself

Training labels are incumbents solved under `source0` (flat 0.20) and `source1`
(cheap 18:00–22:00). The target `day` tariff is cheap 10:00–14:00. Charging is
only possible at the depot (one 90-kW connector) during depot movements or after
18:00. Exploiting the day tariff therefore requires **midday depot visits — a
different route topology** from those the labels reward. The models do receive
price features (window price mean/min, market mean/spread; `learned_proposals.FEATURES`),
but every timetable has labels under only two tariffs (flat and evening-cheap), so the
midday-price response is barely identifiable and the models reproduce evening/flat
topologies. The v7 loss is what this distribution shift predicts. Two consequences:
(Correction, 05:35 UTC: an earlier version of this paragraph said the models saw no
tariff features; they do.)

- it is a strong signal *for* the paper: discrete routing responds to price, so the
  fleet's indivisible choice is economically live on this generator;
- edge imitation of incumbents from two other tariffs gives almost no information
  about the midday response. v9's battery/charger context helps the input side, but
  the decisive change is labels that span many tariffs per timetable.

## Weaknesses and biases

- **No matched-time baseline.** No experiment compares a learned pipeline with cold
  solving at equal wall time or time-to-quality. Without this, no speed claim is
  testable, positive or negative.
- **Training where ML cannot help.** The bank has 20–28 trips; cold MIP returns
  better plans within its ~55 s phase. The measured bottleneck of the paper is at
  37+ services (public Hildenbrand), where pricing MIPs cannot close bounds.
- **The decoder discards the solver.** Predict edges, repair, then charge on fixed
  routes: the solver never corrects the learner's routing. Standard practice
  (Neural Diving; predict-and-search) fixes only confident decisions and lets the
  MIP optimize the rest, including charging.
- **No LP-relaxation baseline for edge scores.** Learned scores must beat the MIP's
  own LP-relaxation values as a fixing/ranking signal; otherwise they add nothing.
- **Overhead.** 35+ cluster jobs, but v7 used 0.41 CPU-hours. The receipt/hash
  machinery is valuable for reproducibility but has dominated effort.

## Strongest contribution

The exact price-support theory with its dual-coordination link to the
Alizadeh–Scaglione framework and Shapley–Folkman aggregation. The learning work
does not yet contribute to it; it could, by (a) making public-scale fleet pricing
cheaper, or (b) documenting price-responsive topology change.

## Decisive experiments (stop/go)

E0. **Hull-control rerun** on the v7 timetables with the typo fixed (new attempt
identity; the failed attempt is preserved). Go: report D, CH, gap and regret next to
the v7 bills. Cheap.

E1. **Topology-response diagnostic.** For each timetable, compare cold incumbent
topologies under source0, source1 and day. Report how often and how much the
movement set changes. Stop route-for-price learning if topology rarely changes.

E2. **Cold time-to-quality profile** on the same generator at increasing size
(e.g. 20/28 → 40/56/80 trips), with solver progress traces. Stop ML-for-speed on
this distribution if cold reaches within 0.5% of the best known bill in < 30 s at
the largest generable size.

E3. **Predict-and-fix** (fix the top-k% most confident edges, solve the rest with
the MIP including charging) using existing models and, separately, LP-relaxation
scores; versus cold, all at matched wall time. Go if learned fixing beats both
LP-score fixing and cold on ≥ 70% of groups at the matched budget.

Training continues in parallel: collect v8 once (no retries), verify its 300-epoch
anchor, then run v9 (tariff/battery context) because its scores feed E3.

## Operating rules for this takeover

- Branch `claude/research-20261001`; every experiment gets a short protocol file
  before launch and a results file after; all failures and spent time retained.
- Cluster: ≤ 6 concurrent Gurobi processes (shared token server; the user's own
  `rvS*` MIP/CG jobs must not be starved); exclude `scaglione-compute-01`; never
  touch other jobs; no automatic retries.
- DEV/TEST timetables, A6/B3/confirmation data and private GIRO data stay sealed.
- Google Doc: append consolidated updates only.
