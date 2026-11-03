# Independent exact review of the cyclic experiment

**PASS — no scientific blocker found for the stated four-period reference
model.** Reviewed September27,2026. The reviewer did not author the driver,
import author code, or invoke an optimizer. The preliminary independent
[physical/algebraic derivation](CYCLIC_CANDIDATE_CHECK.md) preceded inspection of
the output. This audit then reconstructed the execution using a separate
vertex/edge method and raw event replay.

## Identity and reproduction

Frozen execution head: `7bf913a87a455e77a4e309eaa58dfcf0b10f76c0`.

Input artifact:
`journal-research-work/result/cyclic_gap/20260927-attempt1/results.json`.

SHA256:
`aeda2a5225d0975254248bae0d942aa752f7c1a340f32d7488bf055aa8d997df`.

The recorded source and protocol digests match the bytes obtained from their
recorded frozen Git commit. Source bytes were read for hashing only; no author
module was imported. The independent [auditor](independent_cyclic_audit.py) uses
only the Python standard library; its digest is in the
[machine-readable report](independent-cyclic-audit.json).

From the workspace, with a fresh report path:

```sh
python3 research-20260927/agent-notes/literature/independent_cyclic_audit.py \
  --repo journal-research-work \
  --result journal-research-work/result/cyclic_gap/20260927-attempt1/results.json \
  --report NEW_REPORT.json
```

The report path is opened exclusively and existing reports are not overwritten.
If this audit is packaged elsewhere, pass the corresponding checkout and result
paths explicitly. The repository must retain the frozen commit.

## Checks performed

1. **Complete physical model.** With exactly two mandatory sequential services,
   up to two used buses and no splitting, there are only two unlabeled
   partitions: `[A,B]` and `[A],[B]`. One bus requires exactly10 early and20
   terminal kWh. Two buses have aggregate early energy in `[0,10]`, with terminal
   energy `30−x`. The second bus cannot charge early while it is already at
   capacity. Both partitions return every bus to20 kWh. The whole projected
   physical set is one point plus one line segment.
2. **Independent optimization.** The auditor constructs three vertices in
   `(intrinsic cost, early energy, terminal energy)`. It interpolates the
   objective at endpoints and the midpoint of each edge to recover an exact
   quadratic, then checks its stationary point when it lies within the edge.
   Physical cost is the minimum of the one-bus point and two-bus segment.
   Convexified cost is the best of all three hull edges. Interior hull points
   cannot improve upon the lower-cost edge at the same load because `f>0` and
   supply cost depends only on load. This proves that edge minimization covers
   the entire hull rather than merely the stored mixture.
3. **All24 declared parameter cases.** The Cartesian set is exactly
   `f∈{1,3,7,10,15,20}` and `a∈{0,2,4,6}`; no missing or duplicate case is allowed.
   Both physical branch objectives, planner optimum, hull optimum, gap, optimal
   early load and one-bus mixture weight match exact reconstructed fractions.
   There are11 positive gaps and13 exact zeros. These constructed cases are not
   independent population samples.
4. **Every saved schedule and mixture.** Each bus's SOC is reconstructed from
   initial energy, service consumption, early charging and terminal charging.
   The audit checks service coverage, all five event SOCs, battery bounds,
   individual early10/terminal30 power limits, shared early10/terminal30 limits,
   exact terminal replenishment, aggregate load and30 kWh recharge. Every hull
   component is replayed, including zero-weight components. Weights, intrinsic
   cost, mean load and the true quadratic objective are recomputed.
5. **Price and LOC accounting.** At nominal `f=7,a=4`, the hull gradient is
   `(107/20,93/20)` and the full physical response is recomputed over all three
   physical vertices. Nonnegative-supply conjugates, the dual value, each
   physical branch's own price/regret and common-price fleet/supplier LOC match.
   Total LOC equals physical objective minus the common-price dual value; a
   suboptimal physical branch correctly includes its extra physical cost.
6. **Serialization and provenance.** All1,894 exact/display number pairs agree;
   malformed leaves and display-only corruption fail. Source/protocol hashes
   match the recorded frozen commit. The nominal record exactly duplicates the
   corresponding declared grid cell.

Totals including the duplicated nominal record are100 saved schedule records,
150 bus trajectories,750 SOC event values and37 positive mixture components.
The24 grid cells alone contain96 schedules,144 trajectories and720 event values;
the extra nominal check is an identity/replay check, not another experiment.

## Nominal findings

| Quantity | Exact value | Decimal |
|---|---:|---:|
| One-bus physical optimum | 97 | 97 |
| Two-bus physical optimum | 99 | 99 |
| Complete-hull optimum | 7591/80 | 94.8875 |
| Planning gap | 169/80 | 2.1125 |
| One-bus weight at hull optimum | 27/40 | .675 |
| Early hull load | 27/4 | 6.75 kWh |
| Physical planner's own-price regret | 13 | 13 |
| Physical planner's fleet LOC at CH price | 0 | 0 |
| Physical planner's supply LOC at CH price | 169/80 | 2.1125 |
| Two-bus branch's fleet LOC at CH price | 7/2 | 3.5 |
| Two-bus branch's supply LOC at CH price | 49/80 | .6125 |

The two-bus branch's total LOC is329/80=4.1125: planning gap169/80 plus its2
units of physical suboptimality. Thus even this tiny example gives an inspectable
reason to report fleet and supplier accounting at the same selected price.

## Adversarial controls

All10 deliberately altered copies were rejected: physical cost; saved event
SOC; convex weight; hull price; fleet LOC; supplier LOC; display-only numeric
corruption; missing case; duplicate case; and service-coverage corruption.
Each mutation starts from an independent deep copy, leaving the original
artifact unchanged. The report records the failing check for each control.

## Scope and remaining concerns

This is stronger than a floating-point optimizer claim: its stated objective
values and gap are established by exact rational calculation plus a complete
physical-set derivation. It is deliberately a tiny, fully specified reference
model. It does not qualify a production scheduling adapter, tapering/charging
losses, finite connector counts, stochastic service consumption, real deadheads,
market calibration or a funded transfer mechanism. The zero reserve and native
terminal recharge window must appear in the paper's caption/model description.
The positive gap survives fair terminal replenishment in this construction;
its prevalence and operational magnitude remain open empirical questions.
