# E2 results (interim, 12 of 18 cells, 06:25 UTC): cold time-to-quality vs size

Array 758967, code 4403c30. One cold Gurobi solve (1 thread, 600 s cap) of the fleet
pricing MIP at the `day` tariff's linear prices, on `claude-scale-v1` cases (connector
power 90*ceil(n/28) kW). "0.5%" = first time the incumbent is within 0.5% of that run's
own final incumbent (not of the true optimum). Gap = final (incumbent-bound)/incumbent.

| Case | Movements | Build s | Status at 600 s | Final incumbent | Gap % | 1st incumbent s | 0.5% s | Buses |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| 50000, 20 trips | 325 | 1.4 | optimal (0.2 s) | 528.51 | 0 | 0.2 | 0.2 | 4 |
| 50001, 20 | 349 | 1.5 | optimal (17.9 s) | 549.56 | 0 | 0.2 | 0.6 | 4 |
| 50002, 20 | 332 | 1.4 | optimal (5.3 s) | 582.05 | 0 | 0.2 | 0.5 | 4 |
| 50003, 20 | 325 | 1.4 | optimal (0.2 s) | 415.17 | 0 | 0.2 | 0.2 | 3 |
| 50000, 40 | 1438 | 2.1 | optimal (206 s) | 526.78 | 0 | 2.0 | 128.1 | 4 |
| 50001, 40 | 1478 | 2.1 | feasible | 611.47 | 2.09 | 2.7 | 9.8 | 4 |
| 50002, 40 | 1444 | 2.2 | optimal (44.6 s) | 637.93 | 0 | 2.1 | 24.2 | 4 |
| 50000, 60 | 3345 | 4.0 | feasible | 644.67 | 10.06 | 9.5 | 138.3 | 4 |
| 50001, 60 | 3408 | 4.0 | feasible | 868.83 | 21.43 | 13.7 | 424.9 | 5 |
| 50002, 60 | 3354 | 3.9 | feasible | 772.49 | 2.94 | 11.6 | 257.9 | 4 |
| 50000, 80 | 6062 | 7.4 | feasible | 764.98 | 10.03 | 28.2 | 470.4 | 4 |
| 50001, 80 | 6142 | 7.3 | feasible | **3781.45** | 78.94 | 46.0 | 46.0 | **30** |

Findings so far:
- Cold solving is trivial at 20 trips (the size of the training bank) and degrades
  sharply: at 40 trips it needs 10-206 s, and at 60-80 trips 600 s leaves 3-79% gaps.
  On 50001/80 the best schedule after 10 minutes uses 30 buses (bill 3781 vs ~765 for
  comparable instances): the solver never found a good fleet.
- Model build is <= 7.4 s even at 80 trips, so solve time, not python-mip
  construction, dominates.
- Stop/go for ML-for-speed on this generator: **go** (the stop condition, "< 30 s to
  0.5% at the largest size", fails badly). E3 phase 2 (761781) tests learned pruning
  on these cases.
