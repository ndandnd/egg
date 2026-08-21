# Cursor handoff: manifest-verified frozen-data loader for the real-data path

Date: 2026-08-20 (America/New_York)

This is an engineering-preparation task: harden the currently unused
`load_frozen_subset` stub into a freeze/load pipeline that enforces the
project's frozen-snapshot discipline before any real (GIRO) data arrives.
No real data exists in the repo and none may be added; everything is
exercised on synthetic fixtures. Read this file completely before changing
anything.

## Scientific and repository boundary

- Repository: `https://github.com/ndandnd/egg`
- Start from clean `origin/main` at
  `5b63e725d0fd85cfb0b83f462a612016e7f4321a`. If main has advanced through a
  reviewed merge, inspect the advancement and use the new clean main.
- Create a new branch such as `cursor/frozen-loader`.
- Open exactly one new draft PR. Do not merge it.
- Do not read or touch anything under `src/runs/`, `result/`, any A6 path, or
  `runs/b3_factor_pilot`. Do not edit `doc/DECISION_LOG.md`,
  `doc/RESEARCH_STATUS.md`, or `doc/ENGINEERING_INCIDENTS.md`.
- Do not launch Slurm or any cluster job. Do not set `EGGLAB_REQUIRE_GRB`.
  All tests must pass with the CBC fallback backend; solver use is optional
  and, if any, only tiny feasibility smoke checks.
- **The only existing file you may modify is `src/egglab/instance.py`, and
  within it only `load_frozen_subset` plus new additions.** `Trip`,
  `Instance`, `Instance.canonical()`, `Instance.hash()`, and
  `synthetic_instance` must remain byte-identical — every committed evidence
  identity in the project depends on them. A test must prove hash stability.
- No real GIRO/Partille data, no data download, no network access. The
  authoritative context for the pending dataset is
  `ref/context/GIRO_DATASET_HANDOFF_20260814.md` (read-only).

## Objective

The handoff rule for real-data work is: design the validation only after the
frozen subset and data manifest exist. This task builds the machinery that
makes "frozen subset + data manifest" a checkable object rather than a
convention:

1. a **freeze tool** that converts a raw subset file into a canonical frozen
   snapshot plus a manifest binding content hash, schema version, units,
   counts, and provenance;
2. a **loader** that refuses to construct an `Instance` unless the manifest
   verifies, and that revalidates physical sanity on load.

## Design requirements

New/changed files:

```text
doc/FROZEN_DATA_SPEC.md
src/experiments/freeze_subset.py          (new; argparse CLI, ap-style flags)
src/egglab/instance.py                    (load_frozen_subset only, + additions)
src/tests/test_frozen_loader.py           (new)
src/tests/fixtures/...                    (tiny synthetic fixture files)
```

Freeze tool (`freeze_subset.py`):

- input: a raw JSON file in the `Instance.canonical()` shape (the format the
  current stub reads); the spec must document the exact accepted schema and a
  `schema_version` string;
- output: `<name>.frozen.json` (canonical: sorted keys, fixed float
  formatting, LF newlines) and `<name>.MANIFEST.json` containing at least:
  full SHA-256 of the frozen bytes, schema version, trip count, horizon
  (`n_slots`, `slot_min`), unit declarations (minutes, kWh, kW), the
  resulting `Instance.hash()`, source-file SHA-256, tool commit
  (`records.git_commit()`), and timestamp;
- deterministic: same input and explicit timestamp flag produce byte-identical
  outputs; follow the argparse conventions of existing drivers
  (`parser named ap`, hyphenated flags with snake_case dest, explicit
  `--out`);
- atomic writes (reuse the `checkpoint.save` pattern or `os.replace`); no
  overwrite of an existing frozen/manifest pair without an explicit
  `--force` that is refused by default.

Loader (`load_frozen_subset(path, manifest_path=None, require_manifest=True)`):

- default behavior requires and verifies the manifest: recompute the frozen
  bytes' SHA-256, check schema version, counts, and that the reconstructed
  `Instance.hash()` matches the manifest; any mismatch raises with a message
  naming the field;
- keep a `require_manifest=False` escape hatch for exploratory loading, but
  it must mark the result (`meta["frozen_verified"] = False`) so downstream
  provenance records show it;
- physical validation on load, each failure a named error: duplicate trip
  ids; nonpositive trip duration; trip windows outside the horizon;
  trip energy exceeding usable battery (`battery_kwh - soc_min_kwh`);
  negative deadhead entries; asymmetric or self-referencing deadhead keys;
  `soc0`/`soc_min`/`soc_end` outside `[0, battery_kwh]`; obvious unit-scale
  sentinels (e.g., trip energy or charge power orders of magnitude beyond
  plausible kWh/kW, thresholds stated in the spec as heuristics that raise
  a warning-level flag rather than silently passing).

The spec must state what this task does **not** do: it defines no GIRO
schema mapping, commits no data, and makes no external-validity claim. When
the real subset arrives, its freeze is a separate reviewed step.

Known repo gotchas: tests self-bootstrap `sys.path` (no conftest.py) — copy
an existing test-file header and run from `src/`; `Instance.hash()` truncates
SHA-256 to 12 hex chars and must not change.

## Required adversarial tests

- round trip: synthetic `Instance` -> canonical JSON -> freeze -> load ->
  identical `canonical()` and `hash()`;
- hash stability guard: `synthetic_instance(seed=0, n_trips=8).hash()`
  pinned to its current value (compute it from clean main first);
- manifest SHA mismatch (single flipped byte in frozen file) refused;
- manifest field tamper (trip count, schema version, instance hash) refused,
  each named in the error;
- missing manifest refused by default; escape hatch marks
  `frozen_verified=False`;
- every physical-validation failure above triggered by a dedicated corrupt
  fixture;
- unit-scale sentinel fixture (Wh-as-kWh style, x1000) flagged;
- freeze determinism: two runs, same explicit timestamp, byte-identical
  outputs; refusal to overwrite without `--force`;
- CLI errors on missing/contradictory flags (imitate
  `ap.error(...)` conventions);
- loader never reads any path outside the one given (no defaults into
  `src/runs/` or `result/`).

Tests must assert emitted file bytes and raised messages, not source strings.

## Verification

Run from `src/`:

```bash
python3 -m pytest tests/test_frozen_loader.py -q
python3 -m pytest tests/ -q
git diff --check
```

## Final report

Include: branch, draft PR URL, exact commits; proof that `Instance`,
`canonical`, `hash`, and `synthetic_instance` are unchanged (e.g.,
`git diff` scope listing plus the pinned-hash test); test counts; the exact
manifest schema; confirmation that no real data was added, no network was
accessed, no cluster job ran, and no `src/runs/`/`result/` path was touched.
Do not merge; return the draft PR for independent review.
