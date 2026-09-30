# B3 replication comparator — frozen contract

This document freezes the verification-tier check that a planned
independent replication of the 60-cell B3 factor pilot reproduces the
original certificates.  It is committed **before any replication exists**.
No live run tree is consulted while writing it.

The analyzer (`src/experiments/analyze_b3_factor_pilot.py`) **replays
recorded evidence**; it does not re-solve.  Certificate agreement is
therefore a property of the recorded checkpoints, not of a fresh
optimization.  Until this comparator exists, “certified intervals agree
within tolerance” is only prose and a disagreement could be rationalized
after it is seen.  The constants below remove that freedom.

Normative implementation: `src/experiments/compare_b3_replication.py`
reading every input through `experiments.b3_pilot_evidence.strict_json_loads`
and `experiments.b3_pilot_evidence.read_regular_bytes_once`.

The checker is importable without a solver.

---

## 1. What is compared

**All 60 cells**, matched by cell identity (`cell_tag` from
`experiments.b3_factor_pilot.build_cells()` /
`cell_tag(setting, seed, n_trips, b)`).

```
N_CELLS = 60
REQUIRED_AGREEING_CELLS = 60
```

Agreement is **60/60**, stated here before any replica data exists.  It
is not a majority, a median, or a “close enough” count.

### Missing or extra cells

If either side is missing any of the 60 identities, or contains any extra
cell directory, or any expected cell lacks `identity.json`,
`a2.cg.ckpt.json`, or `dictator.ckpt.json`, the comparator **refuses to
run the numeric comparison**.  Status is `INCOMPLETE_POPULATION`.
Partial scores (for example 59/60) are not emitted as an agreement
result and are never used to choose a run.

---

## 2. Fields

Compared under the numeric / boolean rules in §3:

| Field | Source (replayed, not trusted as a lone outcome write) |
| --- | --- |
| `lb_best` | `max(lb_history)` in `a2.cg.ckpt.json` |
| `ub_ch` | last entry of `ub_history` in `a2.cg.ckpt.json` |
| `U_lo_raw` | raw lower endpoint of the certified uplift interval |
| `U_hi` | raw upper endpoint of the certified uplift interval |
| `z_D_lb` | dictator lower bound |
| `z_D_ub` | dictator upper bound |
| `certified` | certification flag (`outcome.certified` and `outcome.type == "certified"`) |

Both raw uplift endpoints are compared (not only the theorem-tightened
`max(0, U_lo_raw)`).  Interval construction is the analyzer’s
`cell_interval(ub_ch, lb_ch, z_d_ub, z_d_lb, n_trips)` so the comparator
cannot drift from the scorer it is checking.

### Solve-path equivalence (asserted separately from provenance)

Exact match on: `setting`, `seed`, `n_trips`, `b`, `method`, `epsilon`,
`tol_d`, `budget`, `instance_hash`, `market_hash`.

These are scientific identity, not run provenance.

### Provenance — excluded

`run_commit`, `run_manifest_sha256`, and `run_manifest.json` are
**expected to differ** between two independent runs.  They are excluded
from the comparison.  A replica that merely copies the original
manifest is not a stronger result.

---

## 3. Tolerance

SEK certificate fields use **operand-scaled** tolerance with a floor
equal to the CG / dictator noise:

```
ABS_TOL_SEK = 1e-2          # CG epsilon; also dictator tol_d
REL_SCALE   = 1e-10         # serialization / float noise
allowance   = ABS_TOL_SEK + REL_SCALE * max(1, |left|, |right|)
agree(left, right)  iff  |left - right| <= allowance
```

**Justification.**  The project’s physical replay tolerance is
`1e-4 kWh` (energy residual on independent SOC/load replay).  The CG
epsilon and dictator `tol_d` are `1e-2` SEK (certificate tightness;
`width(U) ≤ tol_d + epsilon`).  Those quantities are different units.
A comparator tighter than `1e-2` SEK would claim to resolve structure
inside the machinery’s own noise floor and is not meaningful.  The
`1e-4 kWh` constant is recorded here so it cannot be silently reused as
a SEK threshold.  Operand scaling admits relative float noise on large
objectives without loosening the `1e-2` floor on typical-magnitude
cells.

`certified` is an **exact** boolean.  Solve-path fields are **exact**.

Hand-computable examples (committed before data):

- `left=100`, `right=100.005` → `|Δ|=0.005 ≤ 0.01 + 1e-10·100` → **agree**
- `left=100`, `right=100.02` → `|Δ|=0.02 > 0.01…` → **disagree**

---

## 4. What a disagreement is

- **60/60** cells agree on every compared field within §3 → status `AGREE`.
- **Any single disagreeing cell** → status `ENGINEERING_INCIDENT`.
  Investigate the pipeline.  **Never** choose which run to score.
- A reversed uplift interval (`U_hi < U_lo_raw` on either side, or the
  replica pair equal to the original pair swapped) → `ENGINEERING_INCIDENT`.
- A non-finite compared field → `ENGINEERING_INCIDENT`.
- Duplicate JSON keys → parse refused (`strict_json_loads`) →
  `ENGINEERING_INCIDENT`.
- Incomplete population → `INCOMPLETE_POPULATION` (no numeric score).

---

## 5. Canonical original

```
ORIGINAL_IS_CANONICAL = True
REPLICA_MAY_SUBSTITUTE_ORIGINAL = False
```

The original run remains canonical **regardless of outcome**.  The
replica may never be substituted for it, including when the replica
looks “better,” when the original is the one that disagrees with a later
taste, or when the replica is byte-identical on certificates.  Scoring,
publication, and follow-on analysis continue to point at the original.

---

## 6. Implementation constraints

- Importable without a solver; tests must not need Gurobi or a cluster.
- Parse every JSON input with `experiments.b3_pilot_evidence.strict_json_loads`
  (duplicate keys refused).
- Read bytes with `experiments.b3_pilot_evidence.read_regular_bytes_once`
  (regular file, no symlink, signature stable across the read).
- Refuse to compare if either side is an incomplete population.
- Never write into either input directory.  The machine-readable verdict
  is written only to an explicit destination outside both trees.
- Verdict encoding is deterministic: UTF-8 JSON, `indent=2`,
  `sort_keys=True`, trailing newline.

Schema id: `b3-replication-comparator-v1`.
