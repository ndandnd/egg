# Phase1 identity reservation — blocked pending complete exclusion inventory

The default proposed base50998 is already an October17 screen identity (`scale:50998:80`). It cannot be reused for40 trips: all timetable sizes, tariffs, seeds and arms sharing that base remain grouped. Base50999 has no conflict in the reviewed metadata. Replacement50997/40 and50999/80 are provisional identity-only proposals, not admitted reservations. Neither case was generated or inspected.

The accompanying `recovery-phase1-reservations.json` preserves known exclusions and SHA256 hashes of the inspected manifest, asset-lock, training/scale identity protocol and generator-namespace sources. Its scopes are screen, training and study; `used_base_ids` conservatively includes the entire TRAIN10000–10127 range, October1 scale50000–50003 and all22 October17 qualification/screen bases from both manifest versions. Timetable variants remain grouped by base ID.

Completeness is unresolved. No authoritative registry covering every prior study was identified among these current manifests. The existing `PRIOR_EXPOSURE_CHECK.json` explicitly limits its scope to selected unsealed October1 protocols and summaries and states that absence is not proof of universal nonexposure. A current generator namespace establishes that scale IDs are development-only, but cannot establish which historical studies used each ID. Source constants and current campaign manifests alone do not prove universal historical nonuse.

Accordingly `attestation` is null and status is blocked. The runner's existing `reservation()` must reject this registry. Before fixture freeze, obtain a complete identity-only historical inventory or equivalent authoritative attestation, check both provisional IDs against it, and replace the null attestation only if justified. This uncertainty does not authorize access to sealed DEV/TEST/A6/B3/confirmation/GIRO data, STATE_MAP, raw logs or large datasets.

No tests, solver, fixture generation, training or cluster work occurred in this metadata review. No economic outcomes selected the proposed identities.

## Extended canonical study catalog

The original blocked JSON is preserved. `recovery-phase1-reservations-v2.json` adds hashes for every canonical protocol found under October1 and the current October17 study protocols/manifests, plus the corresponding `claude_e*` driver sources and shared array launcher. This narrows the intended completeness claim to all canonical recorded studies available in this checkout.

E0 and E2–E11 have explicit protocol files. Their identity declarations collectively use TRAIN10000–10127, scale50000–50003 and public-case keys. The public namespace is separate from integer scale base IDs. October17's two manifests add the same22 qualification/screen scale bases. Training, offline-ranking and replay-fix protocols do not add a new scale cohort. Grouping excludes every variant of those bases.

One specific declaration remains missing: E1-topology has no `PROTOCOL.md`, corresponding `claude_e1` source, or launch lock in the catalog. Its directory contains `E1_RESULTS.md` and `e1_rows.json`; neither was opened during this extension. A separately admitted identity-only projection of the compact rows, or another E1 launch identity declaration, could close this exact gap. The v2 attestation therefore remains null; no generic claim of needing universal historical knowledge remains.

## E1 gap resolved by authorized identity-only projection

The parent explicitly authorized extracting only identity fields from the unsealed compact `research-20261001/e1-topology/e1_rows.json`. The group identity field is `g`; its unique values are10064–10079, all already inside the excluded TRAIN10000–10127 range. No row metrics or outcomes were printed or used, and `E1_RESULTS.md` was not opened. The compact source file's SHA256 is recorded in the v2 catalog.

This closes the one named canonical-study gap. V2 now attests to all canonical recorded EGG October1 E0–E11 studies and subsequent October17 cohorts available in this checkout. E0/E1 use TRAIN10064–10079; E2–E11 introduce only TRAIN10000–10127, scale50000–50003 and the separate public-case namespace. The two October17 manifests enumerate the same22 additional scale bases, including50998. Both proposed bases50997 and50999 are absent from that complete bounded catalog. No economic evidence selected them.

The admitted identity-only design in v2 is50997/40 trips and50999/80 trips. Every size/tariff/seed/arm variant of an excluded base remains excluded; only the future freeze may generate these two admitted cases. The original blocked v1 registry and earlier draft reasoning above remain preserved as review history. The v2 attestation is expressly limited to the canonical recorded studies in this checkout, with no claim of universal historical knowledge, independent profile populations, or statistical qualification. Parent review and the separately budgeted fixture/source freeze remain required.
