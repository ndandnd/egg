# Synthetic NativeCase development generator

`src/experiments/native_scaling_cases.py` creates exactly five reserved
**development** inputs: seed 1006 at 8, 16, and 24 services, plus seeds 1012
and 1009 at 16 services. It rejects all other `(seed, services)` pairs. The
public operator split and the legacy `synthetic_instance` workload are
untouched. The stable interface is `cases() -> {name: NativeCase}`,
`witnesses() -> {name: replayed plan}`, and `tariffs() -> {name:
{flat, source_low, target_low}}`. Names follow
`native_scale_dev_s<seed>_n<two-digit service count>`. The source SHA-256,
identities, all five case results, and construction timings are pinned in
`SYNTHETIC_PREFLIGHT.json`.

## Frozen construction

Each pair has an A→B service followed by a B→A service. Duty `j` starts at
minute `360 + 25j + offset`, where `offset` is in 0–8 minutes. Each service
lasts 18–32 minutes and draws 18.00–28.00 kWh; the B wait lasts 5–30 minutes
and draws 0.01 kWh/minute. The offset, durations, wait, and service energy
hundredths come from the first eight SHA-256 digest bytes (big-endian) of
`egg-nativecase-scaling-development-v1|seed|duty|field`, reduced modulo each
stated integer range. Thus the 1006 cases share a prefix of paired duties
as service count grows, while the other seeds vary independent inputs.

Depot D is four minutes from A and six minutes from B in either direction;
A↔B takes eight minutes. Travel draws 0.25 kWh/minute. Pullout leaves D
exactly in time for the service; pullin returns immediately. For every
distinct ordered service pair, the generator emits a direct mode when travel
immediately after the first service can reach the next service on time,
adding an explicit destination wait at 0.01 kWh/minute. It emits a depot
detour when immediate inbound travel and latest feasible outbound travel
leave a nonnegative depot dwell. These are declared connectivity modes, not
selected fleet routes. The paired witness uses its B wait direct mode and
no depot detour.

Each case has a 100 kWh battery, 20 kWh reserve, 90% grid-to-battery
efficiency, one shared 90 kW connector, and 30 hourly market periods. Used
buses start full and must finish full; terminal charging opens at minute 1080
(18:00) and ends by minute 1800 (30:00). The shared resource is available throughout
the day for intermediate depot visits; the 18:00 opening applies to terminal
replenishment after a bus finishes its service path. Vehicle cost is 100 and deadhead
travel cost is zero, both synthetic. Flat tariff is 0.20 in every hour.
`source_low` is 0.10 from 18:00–22:00 and 0.30 elsewhere; `target_low` shifts
the 0.10 window to 22:00–26:00. These tariffs change no physical case field.

The one-bus-per-pair construction charges returning buses serially at 90 kW.
Every generated paired duty remains below 60.5 kWh and above reserve before
charging; `replay_native` verifies full service coverage, state of charge,
connector sharing, hourly loads, and final full replenishment. All service
events finish before 18:00. No native MIP model, optimizer, or cluster job was
created.

| Case | Grid kWh in paired witness | Service-only grid lower bound | Unavoidable kWh outside any four-hour low window | Compact variables before objective |
|---|---:|---:|---:|---:|
| 1006 / 8 | 215.01 | 205.37 | 0 | 247 |
| 1006 / 16 | 412.64 | 393.59 | 33.59 | 1,311 |
| 1006 / 24 | 622.63 | 594.34 | 234.34 | 4,276 |
| 1012 / 16 | 435.84 | 416.38 | 56.38 | 1,321 |
| 1009 / 16 | 418.62 | 399.51 | 39.51 | 1,328 |

The lower bound follows from full initial and terminal inventory: total grid
replenishment equals total battery draw divided by 0.9. Every mandatory
service contributes its modeled draw and all movement draws are nonnegative.
One four-hour 90 kW window has at most 360 kWh capacity, so service-only grid
demand above 360 kWh must be charged outside that window for **any** feasible
fleet. The paired-witness demand is a feasible construction, not a minimum
fleet or bill. The 8-service cell has no proved low-window scarcity; it was
kept as prespecified. No cell was filtered by its observed result.
