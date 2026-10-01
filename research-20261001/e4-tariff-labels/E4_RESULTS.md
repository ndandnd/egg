# E4 results: tariff-diverse labels make learned routes price-responsive

1 October 2026, 12:25 UTC. Labels: array 759065+759102 (128 TRAIN timetables x 7 cold
solves; 879/896 replayed plans, 17 numerical extraction/replay refusals, 6.9 CPU-h).
Training: bank2 759111 and multi8 775356 (graph attention, seed 17, 4 grouped folds,
<= 900 epochs; bank2 reproduces the v8 seed-17 runs to ~1e-5). Evaluation: 779104,
781389. TRAIN cross-validation only; DEV/TEST sealed. The `day` tariff (cheap
10:00-14:00) is held out: no training label uses >= 2 cheap hours inside that window.

## Primary: ranking on held-out `day` cold incumbents (OUTER groups, equal weight)

| Fold | bank2 log loss | multi8 log loss | bank2 AP | multi8 AP | bank2 top-k | multi8 top-k | sel. epoch b2/m8 |
|---|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.0860 | **0.0759** | 0.8278 | **0.8505** | 0.7103 | 0.7056 | 896/515 |
| 1 | 0.0651 | **0.0570** | 0.8518 | **0.8663** | 0.7359 | 0.7412 | 896/900 |
| 2 | 0.0873 | **0.0794** | 0.8407 | **0.8554** | 0.7085 | 0.7025 | 897/900 |
| 3 | 0.0693 | **0.0630** | 0.8476 | **0.8552** | 0.7263 | 0.7335 | 893/897 |

multi8 improves average precision and log loss in **4/4 folds**; top-k recall is mixed
(2/4). Both arms score worse on the held-out tariff than on their training tariffs
(bank2 outer log loss on source tariffs 0.042-0.068), as expected.

## Secondary: physical decode on the 16 v7 timetables (v7 repair -> fixed-route
charging -> full replay; exact `day` bill)

| Quantity (14 timetables where both decode) | bank2 | multi8 |
|---|---:|---:|
| multi8 vs bank2 | - | 5 cheaper / 8 tie / 1 dearer; mean -9.59 |
| mean bill minus v7 cold incumbent | +18.19 | **+8.60** |
| mean bill minus v7 source-reuse policy | +8.84 | **-0.76** |
| mean energy bought 10:00-14:00 (kWh) | 47.1 | **58.7** |

Failures: the v7 route-cover repair (5 s cap) found no integral cover on 10064 (both
arms) and 10069 (multi8). bank2's 10069 plan uses 6 buses (881.18, +113 over cold).
Per-group rows: `decode_bank2.json`, `decode_multi8.json`.

## Verdict

**Go** on the pre-declared criterion (multi8 beats bank2 on day AP in >= 3/4 folds AND
lowers the mean physical gap to cold). Tariff-diverse labels are the first change in
this campaign that makes learned routes respond to an unseen price pattern: they buy
more midday energy and, on average, beat the v7 source-reuse policy that no earlier
learned arm beat. Learned routes remain 8.6 cost units (~1.5%) above the cold solver
at this size, where cold is near-optimal; the place where learning helps solve time is
larger instances (E2/E3/E5).
