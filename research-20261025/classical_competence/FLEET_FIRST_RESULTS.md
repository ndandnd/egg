# Global fleet-count control — completed once, 25 October 2026

Original unrestricted physical path-flow model, routing binaries free, objective
exactly the number of vehicle pullouts. One native call per exposed development
case, default solver seed, one native thread. No learned scores, greedy scaffold,
secondary electricity optimization or repair. Both plans passed unchanged
extraction and a separate full physical replay.

| Case | Replay-valid buses | Native fleet lower bound | Native status | Native solve | Complete case | Integrated system cost, not optimized |
|---|---:|---:|---|---:|---:|---:|
| scale:50685:40 | 3 | 3 | OPTIMAL | 2.0101s | 3.7242s | 682.07456 |
| scale:50605:80 | 30 | 2 | FEASIBLE | 60.0313s | 71.3317s | 4118.41094 |

The40-trip result demonstrates that conventional full physical optimization
can recover the known three-bus count on this case. Optimality is the native
solver's numerical report for vehicle count; it is not an electricity-cost
certificate or an independently exact proof of the physical formulation.

The80-trip result is a valid but poor incumbent after bounded native search.
A previously replayed graph endpoint has five buses. This proves that30 is not
necessary for this instance, but the historical run uses a different objective,
seed and allocation. Neither these cases nor their timing establish a matched
ML advantage or general superiority of either method.

The full models have23,773 rows/20,669 variables at40 trips and190,037 rows/
177,958 variables at80 trips. These are different exposed timetables, not nested
instances or an asymptotic scaling study. The counts and weak80-trip bound support
investigating formulation/search difficulty before attributing the old learning
gain to electricity-price information. They do not prove that every unrestricted
formulation or classical method must struggle.

Whole-process measurements:75.39s elapsed,73.30s user+system CPU, observed peak
RSS490,143,744 bytes, within the separate300wall/360CPU-second package. Both cases
met their120s endpoint including preparation, one physical inventory, solve,
capture, extraction, independent replay and durable output. This is not the
historical60s comparison. A single physical inventory and capture per case are
preserved separately. The one-shot archive/summary used0.92s elapsed/0.88CPU seconds.
Raw artifacts remain locally; gzip copies and streaming source SHA256 values
are recorded in fleet-first-summary.json. No retries or silent exclusions.

## What changes next

Changing only the full solver objective is insufficient as the serious80-trip
classical control. Next build a coherent conventional route pool or use root-LP
information and structured improvement, with a shared feasible incumbent across
comparison arms. Borrow GRASP/global path-selection ideas from the closest
literature. Route-only matching can diagnose fragmentation but cannot certify
accumulated SOC or shared charger capacity. Do not relaunch this pair just with
more time, retune until it wins, or call this control a replacement for the
multi-group matched study. Recovery/certification follows the baseline and
price-information gates.
