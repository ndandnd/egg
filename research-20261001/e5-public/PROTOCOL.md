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
