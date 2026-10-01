# E5 protocol: learned pruning on public timetables (out-of-distribution)

Declared 2026-10-01 before launch. Same driver and arms as E3
(`claude_e3_prune.py`: cold / learned / lp / random, keep 30%, >= 3 options per
trip side, full-case replay, exact `day` bill), with case keys from
`src/egglab/claude_cases.py`:

- `public:hildenbrand15`, `public:hildenbrand16` (37 services, one 360 kW connector,
  400 kWh buses; the paper's public cases), T in {180, 600} s;
- `public:eberbach` (105 services, 10,359 movements; adapted earlier but never
  solved), T in {600, 1800} s, 32 GB.

Scores: v8 graph attention, fold 0 / seed 17, trained only on the synthetic bank (all
public cases are out of distribution: different battery, connector, times, energy
model). Tariff: the bank `day` tariff (cheap 10:00-14:00) with curvature 1/900.

Questions: (1) at equal wall time, does learned or LP pruning give a better physical
incumbent than cold on public-scale cases; (2) does any arm improve the paper's public
planner upper bounds. Reported per case: bill, buses, status, all failures (pruning
can make a case infeasible; that counts as a loss). Not a held-out statistical test:
three cases, one run each.
Resources: 24 runs, <= 2 concurrent, 1 CPU, 16 GB (32 GB Eberbach).

## Amendment, 05:51 UTC (before any E5 result was read)

The first submission (759411 Hildenbrand, 759412 Eberbach; code 803cded) lacked a
`cold4` control (four tangent rounds of T/4, the v7 cold shape) and per-round logging,
which are needed to separate better routes from more outer-approximation rounds. It
was cancelled and resubmitted as 759670 (Hildenbrand, 20 runs incl. cold4) and
759671 (Eberbach, 10 runs) on code 4a4263e. **Two tasks had already started and were
cancelled after 2 min 33 s each** (759411_0 = hildenbrand15 cold T=180 on
unicorn-cpu-01; 759412_16 = eberbach cold T=600 on unicorn-cpu-75); their partial
outputs were deleted by mistake during the resubmission and were never read. That
0.085 CPU-hours is counted as spent. Bank-phase E3 also gets a cold4 supplement
(759672, 32 runs).
