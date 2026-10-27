# Closed pilot: missing endpoints and qualification

**The observed bottleneck is integer selection from independently discovered pools, not owner failure, a charging-stage timeout, or a proved physical infeasibility.** This diagnosis used bounded `jq` projections of the compact READOUT/master and the worker's `NoSelection` branch only. No bank, plan, spec, native journal or raw input was opened; no replay, solver, hash, export or rerun occurred.

## Closure and exact denominators

The owner is complete/passed with complete accounting, zero unresolved reserve, no stop/configuration/root failure and48 recorded states. Forty stages were attempted; the parent confirms all40 direct children were reaped with exit0 and no late/resource/fatal/identity violations. Worker exit0 means the stage closed without a fatal contract error, not that native search supplied a physical fleet.

| Phase | Planned | Attempted / timely administrative | Physical and method-qualified |
|---|---:|---:|---:|
| Flat acquisition A0 | 16 | 16 | 8 |
| Fresh target discovery F1 | 16 | 16 | 12 |
| Own-bank cache C1 | 16 | 8 | 8 |

All eight attempted C1 controls report a fresh strict physical candidate and native status2/OPTIMAL. None of the eight missing C1 controls was attempted, so none is a cache-solver failure. The root's successful administrative/accounting closure does not satisfy the prespecified complete-method readiness condition.

## A0 failures and dependent C1 omissions

Eight A0 stages returned exactly the worker failure `selection / NoSelection: "No new selected fleet; fallback-only is not strict delivery"`:

- All four bases61001–61004, **24-trip full**.
- Bases61002,61003,61004, **24-trip fixed_duty**.
- Base61004, **12-trip full**.

Every one reports `cg_stop=pricing_certified`, `cg_pricing_certified=true`, fleet-stage native status3/INFEASIBLE, no fleet incumbent (`buses=null`) and **no charging stage**. There is no reported outer/native deadline overrun, physical-replay rejection or configuration exception. The worker emits `NoSelection` when the runner did not publish a selected fleet; it is not an independent physical infeasibility test.

The same eight sequence-specific C1 states are explicitly unattempted for `"No timely admitted own A0 complete bank/common fleet"`. Their operational endpoints remain missing. They were not replaced with another arm's bank, a shared union or zero cost. Three failed fixed24 acquisitions and the failed full12 acquisition nevertheless have valid fresh F1 endpoints, directly showing why a flat-acquisition pool failure cannot be called physical infeasibility of those cases.

## F1 failures and what native status establishes

The four missing F1 endpoints are **24-trip full for every base61001–61004**. Each again reports `NoSelection`, fleet-stage status3, no fleet incumbent, no charging stage and zero native-cutoff overrun. Bases61001–61003 report certified pricing;61004 reports `cg_time_limit` and uncertified pricing. The latter is an internal CG stop, not an absent charging-stage timeout or a late180-second parent endpoint.

Fixed-duty F1 delivered **8/8** physical/native-OPTIMAL endpoints, including each of those four matching base/size cases; full F1 delivered its four12-trip endpoints. Hence the full24 failures do not establish that the shared physical service/resource problem is infeasible. The fleet MIP status concerns the independently retained finite pool. A continuous grid-LP pricing certificate does not imply that this pool contains an integer feasible partition; absence of an integer fleet in it does not certify the full integer route space. The compact evidence does not identify which omitted columns, price-dependent retained alternatives or initialization/search choices caused the gap. Resolving that exact mechanism would require a separately scoped decision; it is not inferred from the stop label.

## Operational retention, telemetry and decision status

No failed F1 was rescued by common fallback: its own A0 was also missing. One qualified C1 (`B61001-N24-fixed_duty-C1`) reports `used_fallback=true` because its valid OPTIMAL candidate ties the common value exactly. That is a newly delivered candidate with incumbent tie retention, **not** a failed method scored as success. Candidate, fallback and retained values remain separate.

The compact cell-level `bank_qualified` flag is acquisition-specific: it is true for the eight usable A0 banks and false for F1/C1 cells. This must not be misread as failed F1 journal admission: the12 successful F1 worker packets separately report `bank_qualified=true`. C1 qualification comes from the pinned own-A0 bank and its fresh native/physical result, not that cell flag.

Readiness correctly remains false:8/16 acquisitions,12/16 F1 deliveries and8/16 required C1 controls are qualified. Primary comparisons have only3/8 defined pairs for either control; the secondary has5/8, so complete group/mean claims remain undefined. Both reported effort screens have0/4 passing groups; that does not license dropping missing value controls or relabeling readiness as complete. No available-only promotion, feasibility conclusion, neural claim or retry follows. Internal meters are prepublication observations with external tail acceptance pending in the compact receipt; the parent owns final accounting reconciliation.
