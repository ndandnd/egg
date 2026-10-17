# Final physical replay verification

Audit PASS: 342 supervisor-valid endpoints audited from 360 completed decisions; 0 mismatches.

| Arm | Decisions | Supervisor valid | Replay passed | Exact bills matched | Censored nonvalid | Other nonvalid |
|---|---:|---:|---:|---:|---:|---:|
| v8 | 60 | 60 | 60 | 60 | 0 | 0 |
| catboost_v5 | 60 | 60 | 60 | 60 | 0 | 0 |
| nonlearned | 60 | 60 | 60 | 60 | 0 | 0 |
| random | 60 | 59 | 59 | 59 | 0 | 1 |
| full4 | 60 | 44 | 44 | 44 | 0 | 16 |
| cold | 60 | 59 | 59 | 59 | 1 | 0 |

Wall 70.434 s; process CPU 51.504 s. No optimizer/model/training imports or calls. Source and model artifact hashes matched the immutable lock.

Every audited plan was replayed on its original full generated case, with day tariff. Exact Fraction(ops_cost) + native_hull.supply(load) matched the stored exact bill. Stored validity/censoring of the remaining endpoints was preserved; failures did not become successes.

Evidence JSON includes per-cell results, source/lock/input hashes and mismatches. Raw solver event logs and stdout/stderr were not read. This is a physical-witness audit of synthetic development evidence, not a new solver experiment or final test.
