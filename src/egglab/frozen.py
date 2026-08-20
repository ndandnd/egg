"""Deterministic, manifest-bound frozen-instance artifacts.

The GIRO source material is not a ready-made benchmark and is not distributed
with this repository.  This module therefore freezes an already reviewed
``Instance.canonical()`` candidate together with a separate provenance record.
It does not infer weekday variants, deadhead fidelity, or vehicle physics.
Those choices must be explicit in the provenance record.

A frozen artifact is a directory containing exactly:

``INSTANCE.json``
    Canonical instance bytes.
``MANIFEST.json``
    Source hashes, the complete provenance record, redundant instance
    identity, and the SHA-256 of ``INSTANCE.json``.

The loader fails closed on absent, malformed, non-canonical, or inconsistent
artifacts.  Callers that need a trust root beyond a Git-tracked manifest can
also pin the manifest SHA-256.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


MANIFEST_SCHEMA = "egglab-giro-frozen-subset-manifest-v1"
PROVENANCE_SCHEMA = "egglab-giro-freeze-provenance-v1"
INSTANCE_FILENAME = "INSTANCE.json"
MANIFEST_FILENAME = "MANIFEST.json"

_INSTANCE_KEYS = {
    "name",
    "trips",
    "depot",
    "dh_min",
    "dh_kwh",
    "battery_kwh",
    "soc0_kwh",
    "soc_min_kwh",
    "soc_end_kwh",
    "charge_power_kw",
    "n_slots",
    "slot_min",
    "max_vehicles",
    "vehicle_fixed_cost",
    "dh_cost_per_min",
    "meta",
}
_TRIP_KEYS = {
    "id",
    "start_min",
    "end_min",
    "start_loc",
    "end_loc",
    "energy_kwh",
}
_PROVENANCE_KEYS = {
    "schema",
    "contract",
    "service_day",
    "variant_choice",
    "trip_selection",
    "deadhead_fidelity",
    "physics",
}
_VARIANT_CHOICE_KEYS = {"policy", "groups"}
_VARIANT_GROUP_KEYS = {"base_task", "alternatives", "selected"}
_TRIP_SELECTION_KEYS = {"rule", "lineage"}
_LINEAGE_KEYS = {"trip_id", "source_role", "source_row", "signature"}
_SIGNATURE_KEYS = {"route", "direction", "from", "start", "end", "to"}
_DEADHEAD_FIDELITY_KEYS = {
    "level",
    "directed",
    "time_dependent",
    "same_reference_policy",
    "missing_link_policy",
}
_PHYSICS_KEYS = {
    "service_energy_policy",
    "charge_power_model",
    "charger_capacity_policy",
    "instance_parameters",
}
_DEADHEAD_LEVELS = {
    "exact-directed-base",
    "reference-fallback",
    "zone-abstraction",
    "custom",
}
_MANIFEST_KEYS = {
    "schema",
    "artifact",
    "inputs",
    "provenance",
    "model",
    "selection",
}
_ARTIFACT_KEYS = {
    "file",
    "sha256",
    "size_bytes",
    "instance_hash",
}
_INPUTS_KEYS = {"instance_candidate", "provenance", "source_files"}
_INPUT_FILE_KEYS = {"role", "file", "sha256", "size_bytes"}
_MODEL_KEYS = {
    "depot",
    "battery_kwh",
    "soc0_kwh",
    "soc_min_kwh",
    "soc_end_kwh",
    "charge_power_kw",
    "n_slots",
    "slot_min",
    "max_vehicles",
    "vehicle_fixed_cost",
    "dh_cost_per_min",
}
_SELECTION_KEYS = {
    "name",
    "trip_count",
    "trip_ids_sha256",
    "first_start_min",
    "last_end_min",
}


class FrozenSubsetError(ValueError):
    """A frozen subset cannot be created or trusted."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the sole accepted on-disk JSON representation."""
    try:
        text = json.dumps(
            value,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=True,
        )
    except (TypeError, ValueError) as exc:
        raise FrozenSubsetError(f"value is not finite JSON: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise FrozenSubsetError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise FrozenSubsetError(f"non-finite JSON number: {value}")


def strict_json_bytes(payload: bytes, *, label: str) -> Any:
    """Parse UTF-8 JSON while rejecting duplicate keys and NaN/Infinity."""
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FrozenSubsetError(f"{label} is not UTF-8 JSON") from exc
    if text.startswith("\ufeff"):
        raise FrozenSubsetError(f"{label} must not contain a UTF-8 BOM")
    try:
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except FrozenSubsetError:
        raise
    except json.JSONDecodeError as exc:
        raise FrozenSubsetError(f"{label} is invalid JSON: {exc}") from exc


def _stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def read_stable_regular_file(path: str | os.PathLike, *, label: str) -> bytes:
    """Read one regular, single-link file without following a leaf symlink."""
    candidate = Path(path)
    try:
        before = candidate.lstat()
    except OSError as exc:
        raise FrozenSubsetError(f"cannot stat {label}: {candidate}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise FrozenSubsetError(f"{label} is not a regular file: {candidate}")
    if before.st_nlink != 1:
        raise FrozenSubsetError(
            f"{label} must have exactly one hard link: {candidate}"
        )

    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(candidate, flags)
    except OSError as exc:
        raise FrozenSubsetError(f"cannot open {label}: {candidate}") from exc
    try:
        opened = os.fstat(fd)
        if _stat_identity(opened) != _stat_identity(before):
            raise FrozenSubsetError(f"{label} changed before reading: {candidate}")
        chunks = []
        while True:
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        if _stat_identity(after) != _stat_identity(opened):
            raise FrozenSubsetError(f"{label} changed while reading: {candidate}")
    finally:
        os.close(fd)
    try:
        after_close = candidate.lstat()
    except OSError as exc:
        raise FrozenSubsetError(
            f"{label} disappeared while reading: {candidate}"
        ) from exc
    if _stat_identity(after_close) != _stat_identity(before):
        raise FrozenSubsetError(f"{label} changed while reading: {candidate}")
    return b"".join(chunks)


def _require_exact_keys(value: Any, expected: set[str], *, label: str) -> dict:
    if not isinstance(value, dict):
        raise FrozenSubsetError(f"{label} must be a JSON object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise FrozenSubsetError(
            f"{label} keys do not match the schema "
            f"(missing={missing}, extra={extra})"
        )
    return value


def _require_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise FrozenSubsetError(f"{label} must be a non-empty string")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise FrozenSubsetError(f"{label} contains a control character")
    return value


def _require_int(
    value: Any,
    *,
    label: str,
    minimum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise FrozenSubsetError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise FrozenSubsetError(f"{label} must be >= {minimum}")
    return value


def _require_number(
    value: Any,
    *,
    label: str,
    minimum: float | None = None,
) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FrozenSubsetError(f"{label} must be a number")
    if not math.isfinite(value):
        raise FrozenSubsetError(f"{label} must be finite")
    if minimum is not None and value < minimum:
        raise FrozenSubsetError(f"{label} must be >= {minimum}")
    return value


def _matrix(
    value: Any,
    *,
    label: str,
    integer_values: bool,
) -> dict[tuple[str, str], int | float]:
    if not isinstance(value, list):
        raise FrozenSubsetError(f"{label} must be a list of [from, to, value]")
    result = {}
    for index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != 3:
            raise FrozenSubsetError(
                f"{label}[{index}] must be a three-element JSON list"
            )
        start = _require_string(row[0], label=f"{label}[{index}][0]")
        end = _require_string(row[1], label=f"{label}[{index}][1]")
        if start == end:
            raise FrozenSubsetError(
                f"{label}[{index}] stores a same-location arc; omit it"
            )
        if integer_values:
            amount = _require_int(
                row[2], label=f"{label}[{index}][2]", minimum=0
            )
        else:
            amount = _require_number(
                row[2], label=f"{label}[{index}][2]", minimum=0.0
            )
        pair = (start, end)
        if pair in result:
            raise FrozenSubsetError(f"{label} contains duplicate arc {pair!r}")
        result[pair] = amount
    return result


def instance_from_canonical(value: Any):
    """Validate canonical data and construct an ``Instance``.

    The representation and primitive values are checked, but this function
    does not strengthen the existing ``Instance`` policy knobs or complete a
    sparse GIRO matrix.  In particular, terminal SOC remains independent of
    the running reserve and unavailable directed deadhead arcs remain absent.
    """
    data = _require_exact_keys(value, _INSTANCE_KEYS, label="instance")
    name = _require_string(data["name"], label="instance.name")
    depot = _require_string(data["depot"], label="instance.depot")

    if not isinstance(data["trips"], list) or not data["trips"]:
        raise FrozenSubsetError("instance.trips must be a non-empty list")
    trips = []
    trip_ids = set()
    previous_start = None
    from .instance import Instance, Trip

    for index, raw_trip in enumerate(data["trips"]):
        trip = _require_exact_keys(
            raw_trip, _TRIP_KEYS, label=f"instance.trips[{index}]"
        )
        trip_id = _require_string(
            trip["id"], label=f"instance.trips[{index}].id"
        )
        if trip_id in trip_ids:
            raise FrozenSubsetError(f"duplicate trip id: {trip_id!r}")
        trip_ids.add(trip_id)
        start_min = _require_int(
            trip["start_min"],
            label=f"instance.trips[{index}].start_min",
            minimum=0,
        )
        end_min = _require_int(
            trip["end_min"],
            label=f"instance.trips[{index}].end_min",
            minimum=0,
        )
        if end_min <= start_min:
            raise FrozenSubsetError(
                f"instance.trips[{index}] must end after it starts"
            )
        if previous_start is not None and start_min < previous_start:
            raise FrozenSubsetError("instance.trips must be sorted by start_min")
        previous_start = start_min
        start_loc = _require_string(
            trip["start_loc"], label=f"instance.trips[{index}].start_loc"
        )
        end_loc = _require_string(
            trip["end_loc"], label=f"instance.trips[{index}].end_loc"
        )
        energy = _require_number(
            trip["energy_kwh"],
            label=f"instance.trips[{index}].energy_kwh",
            minimum=0.0,
        )
        trips.append(
            Trip(trip_id, start_min, end_min, start_loc, end_loc, energy)
        )

    dh_min = _matrix(data["dh_min"], label="instance.dh_min", integer_values=True)
    dh_kwh = _matrix(
        data["dh_kwh"], label="instance.dh_kwh", integer_values=False
    )
    if set(dh_min) != set(dh_kwh):
        raise FrozenSubsetError(
            "instance.dh_min and instance.dh_kwh must contain identical arcs"
        )

    battery = _require_number(
        data["battery_kwh"], label="instance.battery_kwh", minimum=0.0
    )
    if battery == 0:
        raise FrozenSubsetError("instance.battery_kwh must be positive")
    soc0 = _require_number(
        data["soc0_kwh"], label="instance.soc0_kwh", minimum=0.0
    )
    soc_min = _require_number(
        data["soc_min_kwh"], label="instance.soc_min_kwh", minimum=0.0
    )
    soc_end = _require_number(
        data["soc_end_kwh"], label="instance.soc_end_kwh", minimum=0.0
    )
    if soc0 > battery or soc_min > battery or soc_end > battery:
        raise FrozenSubsetError(
            "instance SOC values must not exceed battery_kwh"
        )
    charge_power = _require_number(
        data["charge_power_kw"],
        label="instance.charge_power_kw",
        minimum=0.0,
    )
    n_slots = _require_int(
        data["n_slots"], label="instance.n_slots", minimum=1
    )
    slot_min = _require_int(
        data["slot_min"], label="instance.slot_min", minimum=1
    )
    max_vehicles = _require_int(
        data["max_vehicles"], label="instance.max_vehicles", minimum=1
    )
    vehicle_fixed_cost = _require_number(
        data["vehicle_fixed_cost"],
        label="instance.vehicle_fixed_cost",
        minimum=0.0,
    )
    dh_cost_per_min = _require_number(
        data["dh_cost_per_min"],
        label="instance.dh_cost_per_min",
        minimum=0.0,
    )
    if not isinstance(data["meta"], dict):
        raise FrozenSubsetError("instance.meta must be a JSON object")
    canonical_json_bytes(data["meta"])

    instance = Instance(
        name=name,
        trips=trips,
        depot=depot,
        dh_min=dh_min,
        dh_kwh=dh_kwh,
        battery_kwh=battery,
        soc0_kwh=soc0,
        soc_min_kwh=soc_min,
        soc_end_kwh=soc_end,
        charge_power_kw=charge_power,
        n_slots=n_slots,
        slot_min=slot_min,
        max_vehicles=max_vehicles,
        vehicle_fixed_cost=vehicle_fixed_cost,
        dh_cost_per_min=dh_cost_per_min,
        meta=data["meta"],
    )
    if canonical_json_bytes(instance.canonical()) != canonical_json_bytes(data):
        raise FrozenSubsetError(
            "instance does not round-trip through Instance.canonical()"
        )
    return instance


def _service_minutes(value: Any, *, label: str) -> int:
    text = _require_string(value, label=label)
    parts = text.split(":")
    if (
        len(parts) != 2
        or not all(part.isdigit() for part in parts)
        or not 0 <= int(parts[1]) <= 59
    ):
        raise FrozenSubsetError(
            f"{label} must be an HH:MM service-day time"
        )
    return int(parts[0]) * 60 + int(parts[1])


def validate_provenance(
    value: Any,
    *,
    instance=None,
    source_roles: set[str] | None = None,
) -> dict:
    """Validate GIRO disclosures and bind lineage to hashed source roles."""
    provenance = _require_exact_keys(
        value, _PROVENANCE_KEYS, label="provenance"
    )
    if provenance["schema"] != PROVENANCE_SCHEMA:
        raise FrozenSubsetError(
            f"unsupported provenance schema: {provenance['schema']!r}"
        )
    contract = _require_string(
        provenance["contract"], label="provenance.contract"
    )
    service_day = provenance["service_day"]
    if service_day is not None:
        _require_string(service_day, label="provenance.service_day")

    variant = _require_exact_keys(
        provenance["variant_choice"],
        _VARIANT_CHOICE_KEYS,
        label="provenance.variant_choice",
    )
    _require_string(
        variant["policy"], label="provenance.variant_choice.policy"
    )
    if not isinstance(variant["groups"], list):
        raise FrozenSubsetError(
            "provenance.variant_choice.groups must be a list"
        )
    groups = {}
    for index, raw_group in enumerate(variant["groups"]):
        label = f"provenance.variant_choice.groups[{index}]"
        group = _require_exact_keys(
            raw_group, _VARIANT_GROUP_KEYS, label=label
        )
        base_task = _require_string(
            group["base_task"], label=f"{label}.base_task"
        )
        if base_task in groups:
            raise FrozenSubsetError(
                f"duplicate variant base task: {base_task!r}"
            )
        alternatives = group["alternatives"]
        if not isinstance(alternatives, list) or len(alternatives) < 2:
            raise FrozenSubsetError(
                f"{label}.alternatives must list at least two tasks"
            )
        normalized = [
            _require_string(item, label=f"{label}.alternatives[{item_index}]")
            for item_index, item in enumerate(alternatives)
        ]
        if len(set(normalized)) != len(normalized):
            raise FrozenSubsetError(
                f"{label}.alternatives contains duplicates"
            )
        selected = _require_string(
            group["selected"], label=f"{label}.selected"
        )
        if selected not in normalized:
            raise FrozenSubsetError(
                f"{label}.selected is not one of its alternatives"
            )
        groups[base_task] = set(normalized)
    if contract.casefold() in {"partille", "par"}:
        expected_groups = {
            "13316": {"13316m", "13316uwt"},
            "13324": {"13324muw", "13324t"},
        }
        if groups != expected_groups:
            raise FrozenSubsetError(
                "Partille variant_choice must disclose exactly the 13316 "
                "and 13324 weekday-variant groups"
            )

    trip_selection = _require_exact_keys(
        provenance["trip_selection"],
        _TRIP_SELECTION_KEYS,
        label="provenance.trip_selection",
    )
    if trip_selection["rule"] != "Identifier == Regular":
        raise FrozenSubsetError(
            "provenance.trip_selection.rule must be 'Identifier == Regular'"
        )
    lineage = trip_selection["lineage"]
    if not isinstance(lineage, list) or not lineage:
        raise FrozenSubsetError(
            "provenance.trip_selection.lineage must be a non-empty list"
        )
    lineage_ids = []
    source_row_keys = set()
    lineage_times = []
    for index, raw_entry in enumerate(lineage):
        label = f"provenance.trip_selection.lineage[{index}]"
        entry = _require_exact_keys(raw_entry, _LINEAGE_KEYS, label=label)
        trip_id = _require_string(
            entry["trip_id"], label=f"{label}.trip_id"
        )
        source_role = _require_string(
            entry["source_role"], label=f"{label}.source_role"
        )
        if "/" in source_role or "\\" in source_role:
            raise FrozenSubsetError(
                f"{label}.source_role must not contain a path separator"
            )
        if source_roles is not None and source_role not in source_roles:
            raise FrozenSubsetError(
                f"{label}.source_role is not a hashed manifest source"
            )
        source_row = _require_int(
            entry["source_row"], label=f"{label}.source_row", minimum=1
        )
        row_key = (source_role, source_row)
        if row_key in source_row_keys:
            raise FrozenSubsetError(
                "provenance lineage contains a duplicate source role/row"
            )
        source_row_keys.add(row_key)
        signature = _require_exact_keys(
            entry["signature"], _SIGNATURE_KEYS, label=f"{label}.signature"
        )
        for optional in ("route", "direction"):
            field = signature[optional]
            if field is not None and (
                isinstance(field, bool)
                or not isinstance(field, (str, int))
            ):
                raise FrozenSubsetError(
                    f"{label}.signature.{optional} must be string, integer, or null"
                )
        _require_string(
            signature["from"], label=f"{label}.signature.from"
        )
        _require_string(signature["to"], label=f"{label}.signature.to")
        start_min = _service_minutes(
            signature["start"], label=f"{label}.signature.start"
        )
        end_min = _service_minutes(
            signature["end"], label=f"{label}.signature.end"
        )
        lineage_ids.append(trip_id)
        lineage_times.append((start_min, end_min))
    if len(set(lineage_ids)) != len(lineage_ids):
        raise FrozenSubsetError("provenance lineage contains duplicate trip_ids")

    deadhead = _require_exact_keys(
        provenance["deadhead_fidelity"],
        _DEADHEAD_FIDELITY_KEYS,
        label="provenance.deadhead_fidelity",
    )
    if deadhead["level"] not in _DEADHEAD_LEVELS:
        raise FrozenSubsetError(
            "provenance.deadhead_fidelity.level is unsupported by "
            "the static Instance deadhead representation"
        )
    for key in ("directed", "time_dependent"):
        if not isinstance(deadhead[key], bool):
            raise FrozenSubsetError(
                f"provenance.deadhead_fidelity.{key} must be boolean"
            )
    if deadhead["time_dependent"]:
        raise FrozenSubsetError(
            "time-dependent deadheads cannot be represented by Instance"
        )
    if (
        deadhead["level"] in {"exact-directed-base", "reference-fallback"}
        and not deadhead["directed"]
    ):
        raise FrozenSubsetError(
            f"{deadhead['level']} deadhead fidelity must remain directed"
        )
    _require_string(
        deadhead["same_reference_policy"],
        label="provenance.deadhead_fidelity.same_reference_policy",
    )
    _require_string(
        deadhead["missing_link_policy"],
        label="provenance.deadhead_fidelity.missing_link_policy",
    )

    physics = _require_exact_keys(
        provenance["physics"],
        _PHYSICS_KEYS,
        label="provenance.physics",
    )
    _require_string(
        physics["service_energy_policy"],
        label="provenance.physics.service_energy_policy",
    )
    if physics["charge_power_model"] != "constant":
        raise FrozenSubsetError(
            "provenance.physics.charge_power_model must be 'constant' "
            "for Instance"
        )
    _require_string(
        physics["charger_capacity_policy"],
        label="provenance.physics.charger_capacity_policy",
    )
    _require_exact_keys(
        physics["instance_parameters"],
        _MODEL_KEYS,
        label="provenance.physics.instance_parameters",
    )
    canonical_json_bytes(provenance)

    if instance is not None:
        actual_ids = [trip.id for trip in instance.trips]
        if lineage_ids != actual_ids:
            raise FrozenSubsetError(
                "provenance lineage trip_ids do not match the frozen instance"
            )
        actual_times = [
            (trip.start_min, trip.end_min) for trip in instance.trips
        ]
        if lineage_times != actual_times:
            raise FrozenSubsetError(
                "provenance lineage times do not match the frozen instance"
            )
        if physics["instance_parameters"] != _model_record(instance):
            raise FrozenSubsetError(
                "provenance physics do not match the frozen instance"
            )
    return provenance


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise FrozenSubsetError(
            f"{label} must be a 64-character lowercase SHA-256"
        )
    return value


def _input_file_record(role: str, path: Path, payload: bytes) -> dict:
    _require_string(role, label="source role")
    if "/" in role or "\\" in role:
        raise FrozenSubsetError("source role must not contain a path separator")
    return {
        "role": role,
        "file": path.name,
        "sha256": _sha256(payload),
        "size_bytes": len(payload),
    }


def _model_record(instance) -> dict:
    return {
        "depot": instance.depot,
        "battery_kwh": instance.battery_kwh,
        "soc0_kwh": instance.soc0_kwh,
        "soc_min_kwh": instance.soc_min_kwh,
        "soc_end_kwh": instance.soc_end_kwh,
        "charge_power_kw": instance.charge_power_kw,
        "n_slots": instance.n_slots,
        "slot_min": instance.slot_min,
        "max_vehicles": instance.max_vehicles,
        "vehicle_fixed_cost": instance.vehicle_fixed_cost,
        "dh_cost_per_min": instance.dh_cost_per_min,
    }


def _selection_record(instance) -> dict:
    trip_ids = [trip.id for trip in instance.trips]
    return {
        "name": instance.name,
        "trip_count": len(instance.trips),
        "trip_ids_sha256": _sha256(canonical_json_bytes(trip_ids)),
        "first_start_min": min(trip.start_min for trip in instance.trips),
        "last_end_min": max(trip.end_min for trip in instance.trips),
    }


def _validate_input_record(value: Any, *, label: str) -> dict:
    record = _require_exact_keys(value, _INPUT_FILE_KEYS, label=label)
    role = _require_string(record["role"], label=f"{label}.role")
    if "/" in role or "\\" in role:
        raise FrozenSubsetError(f"{label}.role must not contain a path separator")
    filename = _require_string(record["file"], label=f"{label}.file")
    if Path(filename).name != filename or filename in (".", ".."):
        raise FrozenSubsetError(f"{label}.file must be a basename")
    _require_sha256(record["sha256"], label=f"{label}.sha256")
    _require_int(record["size_bytes"], label=f"{label}.size_bytes", minimum=0)
    return record


def validate_manifest(value: Any) -> dict:
    manifest = _require_exact_keys(value, _MANIFEST_KEYS, label="manifest")
    if manifest["schema"] != MANIFEST_SCHEMA:
        raise FrozenSubsetError(
            f"unsupported frozen-subset manifest schema: {manifest['schema']!r}"
        )
    artifact = _require_exact_keys(
        manifest["artifact"], _ARTIFACT_KEYS, label="manifest.artifact"
    )
    if artifact["file"] != INSTANCE_FILENAME:
        raise FrozenSubsetError(
            f"manifest.artifact.file must be {INSTANCE_FILENAME!r}"
        )
    _require_sha256(
        artifact["sha256"], label="manifest.artifact.sha256"
    )
    _require_int(
        artifact["size_bytes"],
        label="manifest.artifact.size_bytes",
        minimum=0,
    )
    instance_hash = artifact["instance_hash"]
    if (
        not isinstance(instance_hash, str)
        or len(instance_hash) != 12
        or any(char not in "0123456789abcdef" for char in instance_hash)
    ):
        raise FrozenSubsetError(
            "manifest.artifact.instance_hash must be 12 lowercase hex characters"
        )

    inputs = _require_exact_keys(
        manifest["inputs"], _INPUTS_KEYS, label="manifest.inputs"
    )
    candidate = _validate_input_record(
        inputs["instance_candidate"],
        label="manifest.inputs.instance_candidate",
    )
    provenance_input = _validate_input_record(
        inputs["provenance"], label="manifest.inputs.provenance"
    )
    if candidate["role"] != "instance_candidate":
        raise FrozenSubsetError(
            "manifest.inputs.instance_candidate has the wrong role"
        )
    if provenance_input["role"] != "provenance":
        raise FrozenSubsetError("manifest.inputs.provenance has the wrong role")
    if (
        not isinstance(inputs["source_files"], list)
        or not inputs["source_files"]
    ):
        raise FrozenSubsetError(
            "manifest.inputs.source_files must be a non-empty list"
        )
    roles = set()
    previous_role = None
    for index, raw_record in enumerate(inputs["source_files"]):
        record = _validate_input_record(
            raw_record, label=f"manifest.inputs.source_files[{index}]"
        )
        role = record["role"]
        if role in {"instance_candidate", "provenance"} or role in roles:
            raise FrozenSubsetError(f"duplicate or reserved source role: {role!r}")
        if previous_role is not None and role < previous_role:
            raise FrozenSubsetError(
                "manifest.inputs.source_files must be sorted by role"
            )
        previous_role = role
        roles.add(role)

    validate_provenance(manifest["provenance"], source_roles=roles)
    _require_exact_keys(manifest["model"], _MODEL_KEYS, label="manifest.model")
    selection = _require_exact_keys(
        manifest["selection"], _SELECTION_KEYS, label="manifest.selection"
    )
    _require_string(selection["name"], label="manifest.selection.name")
    _require_int(
        selection["trip_count"],
        label="manifest.selection.trip_count",
        minimum=1,
    )
    _require_sha256(
        selection["trip_ids_sha256"],
        label="manifest.selection.trip_ids_sha256",
    )
    _require_int(
        selection["first_start_min"],
        label="manifest.selection.first_start_min",
        minimum=0,
    )
    _require_int(
        selection["last_end_min"],
        label="manifest.selection.last_end_min",
        minimum=1,
    )
    canonical_json_bytes(manifest)
    return manifest


def _write_durable(path: Path, payload: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise FrozenSubsetError(f"cannot write frozen artifact file: {path}") from exc


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _rename_directory_no_replace(source: Path, destination: Path) -> None:
    """Atomically publish a directory without replacing an existing path."""
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    result = -1
    if sys.platform == "darwin":
        rename_exclusive = getattr(libc, "renamex_np", None)
        if rename_exclusive is None:
            raise FrozenSubsetError("renamex_np(RENAME_EXCL) is unavailable")
        rename_exclusive.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename_exclusive.restype = ctypes.c_int
        result = rename_exclusive(
            source_bytes, destination_bytes, 0x00000004
        )
    elif sys.platform.startswith("linux"):
        rename_no_replace = getattr(libc, "renameat2", None)
        if rename_no_replace is None:
            raise FrozenSubsetError(
                "renameat2(RENAME_NOREPLACE) is unavailable"
            )
        rename_no_replace.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename_no_replace.restype = ctypes.c_int
        result = rename_no_replace(
            -100,
            source_bytes,
            -100,
            destination_bytes,
            0x00000001,
        )
    else:
        raise FrozenSubsetError(
            "exclusive frozen-artifact publication is unsupported "
            f"on {sys.platform!r}"
        )
    if result != 0:
        error = ctypes.get_errno()
        if error in (getattr(os, "EEXIST", 17), getattr(os, "ENOTEMPTY", 39)):
            raise FrozenSubsetError(
                f"refusing existing frozen artifact path: {destination}"
            )
        raise FrozenSubsetError(
            f"cannot publish frozen artifact {destination}: "
            f"{os.strerror(error)}"
        )


def _normalize_sources(
    source_files: Mapping[str, str | os.PathLike]
    | Iterable[tuple[str, str | os.PathLike]]
    | None,
) -> list[tuple[str, Path]]:
    if source_files is None:
        raise FrozenSubsetError(
            "at least one GIRO source file is required for the freeze manifest"
        )
    items = (
        list(source_files.items())
        if isinstance(source_files, Mapping)
        else list(source_files)
    )
    normalized = []
    seen = set()
    for role, raw_path in items:
        _require_string(role, label="source role")
        if role in {"instance_candidate", "provenance"}:
            raise FrozenSubsetError(f"reserved source role: {role!r}")
        if role in seen:
            raise FrozenSubsetError(f"duplicate source role: {role!r}")
        if "/" in role or "\\" in role:
            raise FrozenSubsetError(
                f"source role must not contain a path separator: {role!r}"
            )
        seen.add(role)
        normalized.append((role, Path(raw_path)))
    if not normalized:
        raise FrozenSubsetError(
            "at least one GIRO source file is required for the freeze manifest"
        )
    return sorted(normalized, key=lambda item: item[0])


def freeze_subset(
    instance_candidate: str | os.PathLike,
    provenance_path: str | os.PathLike,
    output_dir: str | os.PathLike,
    *,
    source_files: Mapping[str, str | os.PathLike]
    | Iterable[tuple[str, str | os.PathLike]]
    | None = None,
) -> dict:
    """Freeze a reviewed canonical candidate into a new artifact directory.

    The destination is published atomically with no-replace semantics.  Raw
    source files are only hashed; their contents are never copied into the
    artifact.
    """
    candidate_path = Path(instance_candidate)
    provenance_file = Path(provenance_path)
    destination = Path(output_dir)
    if destination.name in ("", ".", ".."):
        raise FrozenSubsetError("output directory must have a concrete name")
    parent = destination.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise FrozenSubsetError(
            f"cannot create output parent directory: {parent}"
        ) from exc
    if parent.is_symlink():
        raise FrozenSubsetError(f"output parent must not be a symlink: {parent}")

    candidate_bytes = read_stable_regular_file(
        candidate_path, label="instance candidate"
    )
    candidate_value = strict_json_bytes(
        candidate_bytes, label="instance candidate"
    )
    instance = instance_from_canonical(candidate_value)
    instance_bytes = canonical_json_bytes(instance.canonical())

    provenance_bytes = read_stable_regular_file(
        provenance_file, label="provenance"
    )
    source_records = []
    for role, path in _normalize_sources(source_files):
        payload = read_stable_regular_file(path, label=f"source file {role!r}")
        source_records.append(_input_file_record(role, path, payload))
    source_roles = {record["role"] for record in source_records}
    provenance = validate_provenance(
        strict_json_bytes(provenance_bytes, label="provenance"),
        instance=instance,
        source_roles=source_roles,
    )

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "artifact": {
            "file": INSTANCE_FILENAME,
            "sha256": _sha256(instance_bytes),
            "size_bytes": len(instance_bytes),
            "instance_hash": instance.hash(),
        },
        "inputs": {
            "instance_candidate": _input_file_record(
                "instance_candidate", candidate_path, candidate_bytes
            ),
            "provenance": _input_file_record(
                "provenance", provenance_file, provenance_bytes
            ),
            "source_files": source_records,
        },
        "provenance": provenance,
        "model": _model_record(instance),
        "selection": _selection_record(instance),
    }
    validate_manifest(manifest)
    manifest_bytes = canonical_json_bytes(manifest)

    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.freeze-", dir=str(parent)
        )
    )
    published = False
    try:
        _write_durable(staging / INSTANCE_FILENAME, instance_bytes)
        _write_durable(staging / MANIFEST_FILENAME, manifest_bytes)
        _fsync_directory(staging)
        _rename_directory_no_replace(staging, destination)
        published = True
        _fsync_directory(parent)
    finally:
        if not published and staging.exists():
            shutil.rmtree(staging)

    return {
        "directory": str(destination),
        "instance": str(destination / INSTANCE_FILENAME),
        "manifest": str(destination / MANIFEST_FILENAME),
        "instance_hash": instance.hash(),
        "instance_sha256": _sha256(instance_bytes),
        "manifest_sha256": _sha256(manifest_bytes),
    }


def _resolve_artifact_paths(
    path: str | os.PathLike,
    manifest_path: str | os.PathLike | None,
) -> tuple[Path, Path]:
    supplied = Path(path)
    if supplied.is_symlink():
        raise FrozenSubsetError(f"frozen subset path must not be a symlink: {supplied}")
    if supplied.is_dir():
        if manifest_path is not None:
            raise FrozenSubsetError(
                "manifest_path must be omitted when path is an artifact directory"
            )
        return supplied / INSTANCE_FILENAME, supplied / MANIFEST_FILENAME
    if manifest_path is not None:
        return supplied, Path(manifest_path)
    if supplied.name == MANIFEST_FILENAME:
        return supplied.parent / INSTANCE_FILENAME, supplied
    sibling = supplied.parent / MANIFEST_FILENAME
    if sibling.is_file():
        return supplied, sibling
    sidecar = Path(str(supplied) + ".manifest.json")
    if sidecar.is_file():
        return supplied, sidecar
    raise FrozenSubsetError(
        f"manifest is required for frozen subset: {supplied}"
    )


def load_verified_frozen_subset(
    path: str | os.PathLike,
    manifest_path: str | os.PathLike | None = None,
    *,
    expected_manifest_sha256: str | None = None,
):
    """Load an instance only after strict manifest and identity verification."""
    instance_path, resolved_manifest_path = _resolve_artifact_paths(
        path, manifest_path
    )
    if instance_path.parent.is_symlink():
        raise FrozenSubsetError(
            f"frozen subset directory must not be a symlink: {instance_path.parent}"
        )
    artifact_directory = resolved_manifest_path.parent
    try:
        names = {entry.name for entry in artifact_directory.iterdir()}
    except OSError as exc:
        raise FrozenSubsetError(
            f"cannot inventory frozen subset directory: {artifact_directory}"
        ) from exc
    expected_names = {INSTANCE_FILENAME, MANIFEST_FILENAME}
    if names != expected_names:
        raise FrozenSubsetError(
            "frozen subset directory entries do not match the manifest "
            f"contract (expected={sorted(expected_names)}, got={sorted(names)})"
        )
    manifest_bytes = read_stable_regular_file(
        resolved_manifest_path, label="frozen subset manifest"
    )
    if expected_manifest_sha256 is not None:
        expected = _require_sha256(
            expected_manifest_sha256, label="expected_manifest_sha256"
        )
        actual = _sha256(manifest_bytes)
        if actual != expected:
            raise FrozenSubsetError(
                "frozen subset manifest SHA-256 mismatch: "
                f"expected {expected}, got {actual}"
            )
    manifest_value = strict_json_bytes(
        manifest_bytes, label="frozen subset manifest"
    )
    if canonical_json_bytes(manifest_value) != manifest_bytes:
        raise FrozenSubsetError(
            "frozen subset manifest bytes are not canonical JSON"
        )
    manifest = validate_manifest(manifest_value)

    expected_instance_path = resolved_manifest_path.parent / INSTANCE_FILENAME
    try:
        same_instance = (
            instance_path.resolve(strict=True)
            == expected_instance_path.resolve(strict=True)
        )
    except OSError as exc:
        raise FrozenSubsetError(
            f"cannot resolve frozen subset artifact: {instance_path}"
        ) from exc
    if not same_instance:
        raise FrozenSubsetError(
            "manifest and instance must be the paired files in one "
            "frozen artifact directory"
        )

    instance_bytes = read_stable_regular_file(
        instance_path, label="frozen subset instance"
    )
    artifact = manifest["artifact"]
    if len(instance_bytes) != artifact["size_bytes"]:
        raise FrozenSubsetError(
            "frozen subset instance size does not match the manifest"
        )
    actual_sha256 = _sha256(instance_bytes)
    if actual_sha256 != artifact["sha256"]:
        raise FrozenSubsetError(
            "frozen subset instance SHA-256 does not match the manifest"
        )
    value = strict_json_bytes(instance_bytes, label="frozen subset instance")
    if canonical_json_bytes(value) != instance_bytes:
        raise FrozenSubsetError(
            "frozen subset instance bytes are not canonical JSON"
        )
    instance = instance_from_canonical(value)
    validate_provenance(
        manifest["provenance"],
        instance=instance,
        source_roles={
            record["role"] for record in manifest["inputs"]["source_files"]
        },
    )
    if instance.hash() != artifact["instance_hash"]:
        raise FrozenSubsetError(
            "frozen subset Instance.hash() does not match the manifest"
        )
    if _model_record(instance) != manifest["model"]:
        raise FrozenSubsetError(
            "frozen subset model parameters do not match the manifest"
        )
    if _selection_record(instance) != manifest["selection"]:
        raise FrozenSubsetError(
            "frozen subset trip selection does not match the manifest"
        )
    return instance
