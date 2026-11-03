"""Read-only curated reporting smoke; prints a compact JSON artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from experiments.computational_benchmark_report import with_analytic_energy_floor  # noqa: E402


def main():
    archive = REPO / "research-20260928/computational-results/attempt1/scientific_evidence.zip"
    analysis = REPO / "research-20260928/computational-results/attempt1/analysis.json"
    with zipfile.ZipFile(archive) as z:
        frozen = json.loads(z.read("frozen.json"))
    saved_analysis = json.loads(analysis.read_text())
    rows = saved_analysis["rows"]
    native_before = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    report = {"scope": "curated scalar development smoke", "rows": rows,
              "supervisor_integrity_ok": saved_analysis.get("supervisor_integrity_ok")}
    augmented = with_analytic_energy_floor(report, frozen, repo=REPO)
    native_after = json.dumps(augmented["rows"], sort_keys=True, separators=(",", ":")).encode()
    assert native_before == native_after
    appendix = augmented["analytic_energy_floor_baseline"]
    compact = {}
    for case, states in appendix["cases"].items():
        if case not in ("public_depot15", "public_depot16"):
            compact[case] = states["status"]
            continue
        compact[case] = {}
        for state, item in states.items():
            mixed = item["conditional_mixed_enclosures"]["cold_hull"]
            compact[case][state] = {
                "ideal_ch_lower_exact": item["ideal_ch_lower"]["ch_lower_exact"],
                "mixed_status": mixed["status"],
                "mixed_gap_exact": mixed.get("gap_interval_exact"),
                "native_certification": mixed["native_certification"],
            }
    print(json.dumps({
        "status": "PASS",
        "inputs_sha256": {
            str(archive.relative_to(REPO)): hashlib.sha256(archive.read_bytes()).hexdigest(),
            str(analysis.relative_to(REPO)): hashlib.sha256(analysis.read_bytes()).hexdigest(),
        },
        "native_rows_count": len(rows),
        "native_rows_sha256_before": hashlib.sha256(native_before).hexdigest(),
        "native_rows_sha256_after": hashlib.sha256(native_after).hexdigest(),
        "native_rows_byte_identical": True,
        "baseline": compact,
        "scope": "curated frozen/scalar reporting-only smoke; no sealed raw events or native solver",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
