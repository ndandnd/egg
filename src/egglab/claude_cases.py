"""One case-key loader for the Claude takeover experiments.

Keys: ``bank:<id>`` (TRAIN bank generator), ``scale:<id>:<trips>`` (claude-scale-v1),
``public:hildenbrand15`` / ``public:hildenbrand16`` / ``public:eberbach`` (the pinned
Sistig native payloads under data/public/sistig_26088190_v1, already adapted and
validated by the earlier intake work; this loader only rebuilds them).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from egglab import claude_scale_cases as scale
from egglab import physical_learning_cases as bank

PUBLIC = {
    "hildenbrand15": ("hildenbrand_native_cases.json", 0, "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7"),
    "hildenbrand16": ("hildenbrand_native_cases.json", 1, "216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d"),
    "eberbach": ("eberbach_native_case.json", 0, "9dc30e1034953808e0c98cd467ae02272eaf6ddde2428a326d26b08b6db94c48"),
}


def _data_root():
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "data/public/sistig_26088190_v1"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("data/public/sistig_26088190_v1 not found above src/")


@lru_cache(maxsize=None)
def _public(name):
    from experiments import sistig_native_case as intake
    filename, index, identity = PUBLIC[name]
    payload = json.loads((_data_root() / filename).read_text())
    case = intake.native_case_from_payload(payload["native_cases"][index])
    if case.identity() != identity:
        raise ValueError("Public case identity changed: " + name)
    return case


def make(key):
    kind, *rest = key.split(":")
    if kind == "bank":
        return bank.make_case(int(rest[0]))
    if kind == "scale":
        return scale.make_case(int(rest[0]), int(rest[1]))
    if kind == "public":
        return _public(rest[0])
    raise ValueError("Unknown case key " + key)
