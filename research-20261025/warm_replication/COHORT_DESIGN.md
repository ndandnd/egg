# Prospective eight-group warm-replanning extension

25 October 2026. **Static metadata design only; no numerical dispatch is authorized
by these files.** The parent reviews the scientific contrasts and later freezes
executable sources, assets, budgets and command. No case generation, source
imports, inference, tests, hashing, optimization or outcome-file reads were used
to select these groups.

## Selection frozen before new outcomes

Choose the first eight base IDs in ascending order from 50600–50999 after
excluding bases exposed in the permitted October 17 v2/v3 qualification/screen
cohort metadata, the preceding warm cohort 50600–50603, the old pilots
50685/50605, and known engineering bases 50997/50999. This gives:

**50604, 50606, 50607, 50608, 50609, 50610, 50611, 50612.**

Only `local-assets-v2.json` and `local-assets-v3.json` cohort-key fields were
inspected; their qualification/screen base sets coincide. Existing warm
`GROUP_MANIFEST.json` and `PROTOCOL.md` supplied the current assignment/design.
The old pilot and engineering exclusions above were supplied explicitly by the
parent. No outcome files, raw cases, sealed indexes or protected data were opened.
The manifest records every excluded base and its provenance.

This is deterministic selection from a narrowly checked register, not random
sampling or proof of globally unseen instances. If later metadata reveals a
previous exposure, **keep the assigned ID, disclose the exposure, and do not
replace it using its generated case or performance**. All variants of a base
remain one development group. Prior-stage results motivated this extension;
they do not make it an untouched final evaluation or a confirmatory population
sample.

## Physical design and counts

Use the unchanged `claude-scale-v1` generator, 40/80-trip nested variants and
native seeds 17/41/73. Shared trip IDs T001–T040 and induced shared movement
records must agree when measured generation occurs. Preserve the original
size-scaled resource rule: one connector and 90*ceil(services/28) kW shared grid
and per-bus power, giving 180 kW at 40 trips and 270 kW at 80. Thus the size
comparison is not a fixed-resource scale effect. Within a size variant, day→late
changes market coefficients only, preserving the physical case.

Acquire one predetermined CoverCA1 day prior per variant, seed17, using the same
pure fleet-count acquisition policy. This gives **16 acquisitions**, shared across
all eight arms and all three replanning seeds. No bill-based prior selection,
additional acquisition seeds, repairs, replacement or retries. A failed prior
leaves its assigned active cells genuinely missing, with no fabricated zero-cost
fallback. Active replanning fixes the prior's fleet count exactly.

There are **48 case/seed blocks** and **384 active 60-second decisions**: eight
groups × two sizes × three seeds × eight arms. The unchanged prior is a separate
zero-work reference for each block, not a ninth active solve.

## Frozen methods and the new fixed-pool comparison

Keep the original seven canonical arms in order:
`GNN, CatBoost, CA1, CoverCA1, random, full, fixed_route`, then append **GNN_day**.
Retain the old selected GNN and CatBoost assets and fit-only preprocessing; no
training, checkpoint selection, feature change, ensemble or tuning is permitted.
Both classical arms remain despite prior results. CatBoost remains reported
separately; the extension does not select a learned winner from its own outcomes.

GNN scores the current target using `a_late`. **GNN_day scores the same new case
with `a_day`, then solves the same late-target objective and physical problem.**
It freshly loads the same checkpoint/preprocessor and recomputes day features
inside every paid decision. It does not reuse the preceding study's scores,
selected pools or plans. Its day-ranked pool is fixed with respect to the target
tariff; only the scoring-price input differs from the target-ranked GNN arm.
Neither GNN scorer consumes b. This tests the value of **ranking adaptation with
a fixed learned model**, including its end-to-end preparation cost. It does not
identify the causal value of learning electricity information, which would need
a comparably selected trained tariff-blind model and separate interventions.

Every restricted arm, including GNN_day, starts from the same original
price-blind B and original K=min(M,max(ceil(.30*M),|B|)). Protect the known
common prior's flexible IDs S0 in Bw=B union S0. CoverCA1 also protects its frozen
cover union C. All original boundaries remain. Fill remaining slots in the arm's
fresh rank order, with **exactly the original K**. If Bw or Bw union C does not
fit, preserve the design failure and operational fallback; never enlarge K.
Record base B, Bw, S0, K, fill/exposure counts and GNN/GNN_day pool overlap.
Identical retained pools are an informative lack of ranking adaptation, not a
reason to change quota. Full/fixed_route retain their existing meanings.

All arms share the late objective, fixed fleet, warm hints, prior-load and
zero-load tangents, completion policy, native cutoff and independently replayed
receipt-inclusive admission rule of the existing warm protocol. Operational
fallback cost remains distinct from method success, lateness, configuration
failure and native-search completion. Record all assigned cells, including
unattempted cells after resource/fatal stops. No selected extra rounds or longer
deadlines for a method that appears promising.

## Execution order and administrative stages

Let b=((group_index*2+size_index)*3+seed_index), with zero-based indexes. Left
rotate the eight-arm canonical list by b mod8, then reverse it when floor(b/8)
is odd. Across b=0,…,47 this gives **six occurrences of every arm in every
position**. It does not assert balanced carryover effects. No outcome-driven
reordering, group replacement or decision-time/quota changes.

The stages are: (1) freeze this outcome-independent cohort/control metadata;
(2) parent critiques and freezes the executable scientific protocol, source/asset
bindings and command; (3) one complete assigned extension, with ordinary resource
and fatal-condition stopping; (4) descriptive grouped readout and a separate
decision about any later study. These are administrative/scientific stages, not
interim performance-based gates that resize this cohort. No execution or later
training follows automatically from this design.

The parent must freeze the continuation/readout rule before dispatch. Report GNN
and CatBoost separately against both classical arms, fixed_route, random, full
and unchanged prior; make the GNN-versus-GNN_day contrast explicit. Use the same
prior late electricity E0 for normalized differences, keeping zero-E0 and missing
priors undefined. Nested sizes and seeds are repeated measurements within eight
base groups. Do not pool the preceding four groups into a supposedly prespecified
independent replication endpoint or claim learned-price causality from this arm.

## Prospective resource direction and boundary

Select **8 CPU hours / 10 wall hours total**, one local worker/native computation
thread and observed peak RSS at most 5 GiB. This includes preparation, cold model
loading, all 16 acquisitions, all 384 decisions, failures, shutdown, accounting
and finalization. It is not an additional allowance after execution. Routine
resource authority exists; no approval question is pending. Final dispatch/closure
reserves and the concrete command remain to be bound prospectively by the parent.
If the total budget cannot fund the remaining assignments, preserve them as
unattempted; do not extend the budget or retry automatically to obtain completion.

No cluster, sealed DEV/TEST/A6/B3/confirmation/GIRO access, new training, wider
sweep, model promotion, recovery/certification study or engineering-controller
extension is authorized. `GROUP_MANIFEST.json` intentionally has no generated
case identities, source hashes, numerical command or dispatch authorization.
