# Depot-15 exact rational witness candidate

27 September 2026. **Candidate pending independent review.** This package replays a direct rational repair of the archived depot-15 flat-pilot incumbent. It does not run an optimizer, alter routes or charging times, or revise archived results.

Run from any directory with Python's standard library:

```sh
python3 /absolute/path/to/check_depot15_exact.py --repo /absolute/path/to/journal-research-work
```

Omitting `--repo` uses this package's repository. Default execution only reads and checks the existing `depot15_exact_candidate.json`; it never rebuilds or overwrites it. `--build` is an exclusive creation mode (`open("x")`) for an absent candidate, and is not needed for this package.

The checker pins the original `result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json` (SHA-256 `35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b`), `depot_15_flat/result.json` (SHA-256 `d5a767d738a02db7e68481d1995549f19bd7089fdc758d8ec28cd2a64166cc85`), archived source commit `282e00b80b6fd9457006429b089269b2a9e2be92`, and case identity `1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`. It reconstructs the candidate from the fixed two vehicle routes, 37 services, 19 charging-session owners/connectors/times, and exact fractions of stored numeric inputs. It checks service/leg energy, battery and reserve at every event, charge windows, connector occupancy, individual/shared 360-kW power, the 30:00 full-replenishment boundary, and 30 exact hourly grid loads.

The original floating witness has two tiny exact terminal overfills. The candidate reduces the final session of bus 0 by `1013/562949953421312` kWh and bus 1 by `3857/562949953421312` kWh; all fixed session timings remain unchanged. The saved candidate has 116 SOC events, total grid energy `4585692153618323/4398046511104` kWh, and exact feasible flat objective `32367329682269897846497216949431/79228162514264337593543950336` (about 408.5331358838777 synthetic units). This is a feasible cost, not an optimum certificate.

The prospective claim is limited to the **ideal stored-input physical depot-15 case** and its synthetic finite 30:00 service block. If independent review accepts this upper witness and the already-proved two-bus lower bound applies to the same model, minimum fleet is exactly two and the flat-cost bounds enclose the optimum. This package does not establish a physical-versus-hull gap, exact feasibility in the solver's rounded big-M matrix, recurring daily operations, or cost optimality. Independent review is required before admitting the witness.
