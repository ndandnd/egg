# E2 protocol: cold time-to-quality of the fleet pricing MIP vs size

Declared 2026-10-01 before launch. Driver `src/experiments/claude_e2_profile.py`,
cases `src/egglab/claude_scale_cases.py` (generator `claude-scale-v1`, ids 50000+,
development only; connector power 90*ceil(n/28) kW, otherwise the bank construction).

- Oracle: V(p) at the `day` tariff's linear prices (the hull/response pricing MIP).
  One cold Gurobi solve, 1 thread, MIPGap 1e-9, 600 s cap, progress log recorded.
- Cells: base ids 50000-50003 x services {20, 40, 60, 80}; plus bank TRAIN groups
  10069 and 10075 (the two v7 groups where cold planning left visible gaps).
- Metrics: time to first incumbent; time until incumbent within 0.5% / 0.1% of the
  final best; final relative gap; model size; replay of the final incumbent.
- Stop/go for ML-for-speed on this generator: stop if at the largest size the cold
  solver reaches within 0.5% of its own final best in < 30 s on all instances.
- Resources: 18 tasks, <= 4 concurrent, 1 CPU / 16 GB / 15 min. ~3 CPU-hours.
- Infeasible or failed cells are reported as such; nothing is retried.
