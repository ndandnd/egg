# Next decision: all-mode ideal capacity outer cuts at fixed N

25 October 2026. STATIC mathematical design only. No artifact values, original rows, plans, imports, hashes, new numerical calculations, replay or solver calls were accessed/performed. This note proposes a distinct prospective analysis, not a launch manifest, script, retry or permission to reopen data now.

## Why this diagnostic, and which controls

The unresolved full-graph 45-kW results should be diagnosed before proposing cut-aware routing or learning. A cut on the original reference topology cannot settle those results. The next question is whether a valid **outer relaxation of every declared-route collection at the frozen fleet N** already excludes the ideal resource variant. Failure to exclude remains unknown, not evidence of feasible routes or an invitation to relabel `INF_OR_UNBD`.

Include all four fixed groups, not only failed cases: 10001, 10006, 10009 and 10005, at the two existing grid levels 90/45. Future authority would admit exactly their four owned **p90 acquisition specs**: `resource_recourse/attempt01/001-acquisition`, `004-acquisition`, `005-acquisition` and `008-acquisition`, respectively. No different group, fleet quantity, cap scan, routing solve or model fit follows. These are exposed development controls, not independent confirmation.

## Movement-energy lower bound: proof and pitfalls

For each declared movement `m`, let `e_m` be the sum of its represented leg energies. Let `I(t)` contain every declared pullout or inter-trip direct/depot mode entering mandatory trip `t`; let `O(t)` contain every declared inter-trip or pullin mode leaving it. Pullins have no incoming-trip incidence; pullouts have no outgoing-trip incidence. Define

`L_in = sum_t min_{m in I(t)} e_m + N*min_{m a pullin} e_m`,

`L_out = sum_t min_{m in O(t)} e_m + N*min_{m a pullout} e_m`,

`L_move = max(L_in,L_out)`, and `D_LB = sum_t E_trip(t) + L_move`.

Every complete fixed-N route collection uses exactly one incoming and one outgoing movement per mandatory trip, exactly N pullouts and N pullins. Selected incoming movements plus selected pullins partition its movement set; selected outgoing movements plus selected pullouts give the other partition. Each construction therefore lower-bounds selected movement energy; their **maximum**, not their sum, is a lower bound. It is harmless that independent minima may use incompatible arcs, extra starts or cycles: those choices weaken the relaxation rather than invalidating it. Parallel movement alternatives must all remain eligible. Include every leg, including auxiliary waiting draw, without using movement cost as an energy surrogate.

Require admitted unique trip/movement IDs, valid kind/before/after incidence and nonnegative individual trip/leg energies. N is the positive canonical `fleet_N` metadata in the bound spec, not a value inferred from cost or a newly opened reference plan. Missing required incidence or start/end candidates must be explicit structural-unavailable/necessary-incidence findings, not an invented finite minimum or silent arc repair. The note does not assume the source0 fleet is minimal. If complete-path coverage, fixed N, energy or identity assumptions cannot be established from the authorized projection, report unknown.

## From demand to all-mode capacity cuts

Let `K=B-r>0`, common efficiency `eta in (0,1]`, opening `h=1080` and the declared recharge deadline `H`. Initial and terminal batteries are full, reserve is respected, charging is grid-to-battery only, and there is no unmodeled consumption outside mandatory trips and movement legs. Conservation yields total grid energy `G=D/eta >= D_LB/eta`.

For each **declared depot mode**, derive its window from the validated split: arrival of leg `split-1` through departure of leg `split`. Clip to `[0,h)`, drop empty intervals and merge the union across **all modes**, even mutually incompatible ones. No terminal charge is available before `h`. Let that union be `U_all`, and

`C_pre = integral_{U_all} 1(connector available)*min(per_bus_kw,grid_kw) dt/60`,

`C_post = integral_[h,H] 1(connector available)*min(per_bus_kw,grid_kw) dt/60`.

Use actual declared resource intersections; with the frozen one-connector constant-rate settings this reduces to effective power times union duration. Do not sum overlapping mode windows or multiply shared capacity by N. Every feasible selected-route preterminal schedule is supported inside `U_all`, hence its preterminal grid energy is at most `C_pre`. Including windows from incompatible or unusable modes makes an **upper** bound and cannot create a false ideal exclusion. Optional daytime opportunities must not be omitted.

Two distinct lower bounds are available:

1. **SOC-at-opening bound, conditional on all consumption being early.** If every mandatory trip and every potentially selected movement has completed its energy consumption by `h`, aggregate SOC at opening is `N*B-D+eta*G_pre >= N*r`. Thus `G_pre >= max(0,(D_LB-N*K)/eta)`. A simple conservative source-field check is that all trip ends and all leg arrivals in the declared universe are at/before `h`, with chronological times and nonnegative draws. This check is sufficient, not necessary; an unusable late mode may make it fail. Do not apply the full `D_LB` SOC bound merely because the original reference returned early.
2. **Total-demand/post-opening bound.** Irrespective of whether consumption finishes by `h`, `G_post <= C_post` and conservation imply `G_pre >= max(0,D_LB/eta-C_post)`. This bound needs a valid horizon/terminal-conservation assumption, but not the stronger all-mode-early condition. It remains valid when useful charging after `h` includes a depot visit: `C_post` is the capacity of the entire post-opening horizon, not a claim that every bus is already terminally available.

When the all-mode-early condition holds, compare `max(0,(D_LB-N*K)/eta,D_LB/eta-C_post)` with `C_pre`. If it fails, never guess that late movement demand has already been consumed. For the SOC term, the deliberately weak safe substitute is the sum `S_h` of mandatory nonnegative service energies whose trip ends are at/before `h`: `G_pre >= max(0,(S_h-N*K)/eta)`, provided reserve by opening is part of the stated ideal physical assumptions. Otherwise leave that term unknown. The total-demand/post-opening term can remain separately valid as above. No custom movement-prefix bound, subset search, matching optimization or new solve is included.

## Meaning of a violation, and what it cannot resolve

If a justified lower bound exceeds `C_pre`, no complete route collection at this declared N can satisfy the **stated ideal physical assumptions within the admitted movement universe**. Unlike a selected-topology cut, this outer cut ranges over all declared route choices. It does not establish unrestricted EVSP infeasibility, a native-precision certificate, an optimum, or infeasibility after adding fleet/movements/resources. Exact rational arithmetic on represented input coefficients does not remove the stored-row bands, decoder/replay tolerances or possible assumption mismatch. Report exact signed margins and assumption status; do not invent an epsilon-based physical certificate or change old native classifications.

The converse is false. Independent arc minima may be jointly unrealizable; the all-mode union can combine incompatible windows; aggregate storage `N*K` ignores individual bus deficits, headroom, route order and early reserve deadlines. Even ample union capacity may be unavailable to the bus that needs it. Therefore a passing bound leaves the two unresolved full-graph cases unresolved. A violating cut for a previously admitted operational control would require preserving the discrepancy and checking assumptions/numerical scope, not silently invalidating or repairing that witness. No outcome-driven cap change, extra fleet, learning gate or rescue search is authorized.

## Future field authority, binding and budget

The future exact eight-file input set is each named folder's `external-receipt.json` and `spec.json`. Read/hash each external receipt once in the metered batch and inspect only its binding/routing fields (`spec_sha256`, folder/task/phase/group/base/service/grid identifiers). Then read/hash each spec byte buffer once and require its digest equal that external receipt's `spec_sha256`; do not follow arbitrary paths named inside either file. Require the expected p90 acquisition group/ordinal/root/phase and frozen fixed N. No inference from receipt native statuses or candidate costs is needed. The closed owner/spec provenance is inherited, not re-proved by opening older tables or plans.

Permitted spec semantics: routing/identity fields, `fleet_N`, `expected_case_identity`, and the **case only**: trip IDs/times/energies; movement IDs/kinds/before/after/split and leg endpoints/times/energies; battery/reserve/efficiency; terminal opening/deadline; resource intervals/per-bus/grid powers/connectors and the declared horizon. Name/schema fields needed for identity context may be retained, but reconstructing a whole case identity must not cause semantic inspection of excluded cost fields. Do not inspect `reference_selected_ids`, any original/acquisition plan or charge/load array, operations/vehicle/deadhead costs, prices/objectives, cached replay, models, original TRAIN files or other owned artifacts. Parsing full spec JSON for this explicit projection is permitted only after future authority is frozen; no such read occurs now. Output group/resource scalars, minimum-energy and union-capacity bounds, exact signed margins and unknown reasons, not mode-ID/plan vectors.

Propose **30 CPU seconds / 60 wall seconds total**, body 25 CPU / 50 wall plus 5 CPU / 10 wall publication/exit reserve; one standard-library process/thread and no children or native packages. Parent must prospectively bind one thin source, protocol, exact command, fresh exclusive output, the eight allowed paths and an honest new funding decision before any run. The closed resource-recourse package is not reopened or reset; any new analytical allowance must be explicit, nonrefundable and carried into cumulative totals. No manifest, numerical execution, automatic retry or further data expansion follows from this note.
