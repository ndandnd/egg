#!/usr/bin/env python3
"""Hash allowed public timetable inputs and assign base groups, without parsing them."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INVENTORY = REPO / "research-20260928/computational-design/inventory.md"
ASSIGNMENT_SEED = "egg-base-network-reservation-2026-09-28-v1"
FIXED_DEVELOPMENT = {"hildenbrand", "stadtwerke eberbach"}
FILES = {"trip_set.xlsx", "deadhead_trip_matrix.mat"}
QUOTAS = {
    "small_1_200": {"test": 1, "train": 1},
    "medium_201_999": {"test": 2, "dev": 1, "train": 3},
    "large_1000_plus": {"test": 3, "dev": 1, "train": 6},
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFC", value).replace("_", " ")
    return " ".join(value.casefold().split())


def parse_inventory(text: str):
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        fields = [part.strip() for part in line.split("|")[1:-1]]
        if len(fields) == 3 and re.fullmatch(r"\d[\d,]*", fields[1]):
            rows[normalize(fields[0])] = {
                "operator": fields[0], "service_rows": int(fields[1].replace(",", ""))}
    archive_match = re.search(
        r"archive is `([^`]+\.zip)` \(([\d,]+) bytes;.*?intake SHA-256 `([0-9a-f]{64})`",
        text, flags=re.S)
    if not archive_match:
        raise ValueError("Pinned public ZIP entry not found in inventory")
    return rows, {"path": archive_match.group(1),
                  "bytes": int(archive_match.group(2).replace(",", "")),
                  "sha256": archive_match.group(3)}


def member_sha(zf: ZipFile, member: str):
    digest, size = hashlib.sha256(), 0
    with zf.open(member, "r") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {"member": member, "bytes": size, "sha256": digest.hexdigest()}


def stratum(service_rows):
    if service_rows <= 200:
        return "small_1_200"
    if service_rows <= 999:
        return "medium_201_999"
    return "large_1000_plus"


def main():
    inventory_text = INVENTORY.read_text()
    inventory, archive = parse_inventory(inventory_text)
    zip_path = Path(archive["path"])
    if not zip_path.is_file() or zip_path.stat().st_size != archive["bytes"]:
        raise ValueError("Pinned archive path/size differs from inventory")

    by_operator = defaultdict(dict)
    with ZipFile(zip_path) as zf:
        names = zf.namelist()
        for member in names:
            path = PurePosixPath(member)
            if path.name not in FILES:
                continue
            folder = re.sub(r"^\d+__", "", path.parent.name)
            operator_key = normalize(folder)
            if operator_key not in inventory:
                continue
            if path.name in by_operator[operator_key]:
                raise ValueError(f"Multiple selected {path.name} members for {folder}")
            by_operator[operator_key][path.name] = member
        if set(by_operator) != set(inventory):
            raise ValueError("Selected operator folders do not match metadata inventory")

        records = []
        for operator_key, meta in inventory.items():
            selected = by_operator[operator_key]
            if set(selected) != FILES:
                raise ValueError(f"Missing permitted fingerprint input for {meta['operator']}")
            inputs = {filename: member_sha(zf, selected[filename]) for filename in sorted(FILES)}
            fingerprint_payload = "\n".join(
                f"{filename}={inputs[filename]['sha256']}" for filename in sorted(FILES))
            fingerprint = hashlib.sha256(fingerprint_payload.encode()).hexdigest()
            records.append({**meta, "base_fingerprint": fingerprint, "inputs": inputs})

    # Merge only exact byte-identical selected-input pairs before assignment.
    by_fingerprint = defaultdict(list)
    for record in records:
        by_fingerprint[record["base_fingerprint"]].append(record)
    groups = []
    for fingerprint, members in by_fingerprint.items():
        counts = {m["service_rows"] for m in members}
        if len(counts) != 1:
            raise ValueError("Identical selected inputs have conflicting metadata sizes")
        count = counts.pop()
        groups.append({"base_fingerprint": fingerprint, "service_rows": count,
                       "stratum": stratum(count),
                       "operators": sorted(m["operator"] for m in members),
                       "members": sorted(members, key=lambda item: item["operator"])})

    reserved = []
    for band in QUOTAS:
        band_groups = [g for g in groups if g["stratum"] == band]
        forced = [g for g in band_groups
                  if any(normalize(name) in FIXED_DEVELOPMENT for name in g["operators"])]
        for group in forced:
            group["split"] = "dev"
            group["assignment_reason"] = "irrevocably development: already selected/studied base"
            group["assignment_rank_hash"] = None
        remaining = [g for g in band_groups if g not in forced]
        for group in remaining:
            group["assignment_rank_hash"] = hashlib.sha256(
                f"{ASSIGNMENT_SEED}|{band}|{group['base_fingerprint']}".encode()).hexdigest()
        remaining.sort(key=lambda g: (g["assignment_rank_hash"], g["base_fingerprint"]))
        quota = dict(QUOTAS[band])
        dev_forced = len(forced)
        expected_total = sum(quota.values()) + dev_forced
        if len(band_groups) != expected_total:
            raise ValueError(f"Unexpected {band} group count {len(band_groups)}; expected {expected_total}; freeze a revised rule before outcomes")
        cursor = 0
        for split, count in (("test", quota.get("test", 0)),
                             ("dev", quota.get("dev", 0)),
                             ("train", quota.get("train", 0))):
            for group in remaining[cursor:cursor + count]:
                group["split"] = split
                group["assignment_reason"] = f"SHA-256 rank within {band} stratum"
            cursor += count
        if cursor != len(remaining):
            raise ValueError(f"Unassigned groups remain in {band}")
        reserved.extend(band_groups)

    counts = {split: sum(group["split"] == split for group in reserved)
              for split in ("train", "dev", "test")}
    payload = {
        "schema": "egg.grouped-reservation.v1",
        "status": "prospective metadata-only reservation; not a qualification or run list",
        "source_inventory": {"path": "research-20260928/computational-design/inventory.md",
                              "sha256": hashlib.sha256(INVENTORY.read_bytes()).hexdigest()},
        "public_archive": {**archive, "local_size_verified": True},
        "fingerprint_policy": {
            "inputs_only": ["trip_set.xlsx", "deadhead_trip_matrix.mat"],
            "definition": "SHA-256 of the sorted selected-member basename/hash pairs; file contents are hashed but never parsed",
            "exact_duplicate_policy": "merge operator records only when both selected input files are byte-identical",
            "semantic_alias_limit": "different bytes do not establish semantically distinct timetables; if a candidate test base is later found to alias any already-studied train/dev/prior-screen base, quarantine the merged base from the clean test set and do not backfill after outcomes",
            "variant_policy": "every depot/day/vehicle/tariff/timing/scenario variant of one base timetable inherits its base group split",
        },
        "assignment": {
            "seed": ASSIGNMENT_SEED,
            "rank": "ascending SHA-256 of seed|size_stratum|base_fingerprint; fingerprint breaks rank ties",
            "size_strata_from_inventory_metadata_only": {
                "small_1_200": "1–200 service rows",
                "medium_201_999": "201–999 service rows",
                "large_1000_plus": "1,000+ service rows",
            },
            "additional_quotas_after_fixed_development": QUOTAS,
            "fixed_public_development_bases": ["Hildenbrand", "Stadtwerke Eberbach"],
            "prior_screen_cases_development": ["cyclic2", "multivisit3", "every prior screen case and its variants through 2026-09-28"],
        },
        "group_counts": {"total_public_base_groups": len(reserved), **counts,
                         "by_stratum": {band: {split: sum(g["stratum"] == band and g["split"] == split for g in reserved)
                                              for split in ("train", "dev", "test")}
                                        for band in QUOTAS}},
        "groups": sorted(reserved, key=lambda g: (g["stratum"], g["split"], g["base_fingerprint"])),
        "interpretation": "Held-out groups are reserved before outcomes; this metadata split does not promise that every public base will be qualified or solved. Do not open test groups for adaptation, comparative outcomes, or training. A later cross-split semantic alias contaminates the candidate holdout: quarantine the merged group from clean test membership and never promote an exposed alias to a clean holdout.",
    }
    target = HERE / "GROUPED_RESERVATION.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(target), "group_counts": payload["group_counts"],
                      "groups": [{"operators": g["operators"], "service_rows": g["service_rows"],
                                  "stratum": g["stratum"], "split": g["split"],
                                  "base_fingerprint": g["base_fingerprint"]} for g in payload["groups"]]},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
