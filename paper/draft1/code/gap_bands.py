"""Exact offset intervals for the complete-graph, charge-only calibrated sweeps."""
import argparse
from decimal import Decimal
from fractions import Fraction as Q
import hashlib
import json
from math import lcm
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFSETS = tuple(Q(k, 20) for k in range(-4, 33))
RHOS = (Q(1, 2), Q(1), Q(2), Q(4))
GROUPS = {"B300_K0.5": (300, Q(1, 2)), "B300_K1.0": (300, Q(1)),
          "B400_K0.5": (400, Q(1, 2)), "B400_K1.0": (400, Q(1))}
PBAR = Q(3, 20)
FEE = 150
PUBLISHED_TOL = Decimal("1e-9")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_input(path):
    def unique_keys(items):
        result = dict(items)
        require(len(result) == len(items), "Duplicate JSON key in " + str(path))
        return result

    raw = (ROOT / path).read_bytes()
    return (json.loads(raw, parse_float=Decimal, object_pairs_hook=unique_keys),
            hashlib.sha256(raw).hexdigest())


def geometry(operator, battery):
    """Use integer kWh subunits for every pairing cost, then return rational thresholds."""
    a = sorted(map(Q, operator["a_kwh"]))
    b = sorted(map(Q, operator["b_kwh"]))
    require(a[0] > 0 and b[0] > 0, "Nonpositive run energy: " + operator["operator"])
    if max(a[-1], b[-1]) > battery:
        return None
    scale = lcm(*(x.denominator for x in a + b))
    am = [int(x * scale) for x in a]
    pm = [int(x * scale) for x in b]
    cap = battery * scale
    thresholds = [Q(0)]
    for m in range(1, min(len(am), len(pm)) + 1):
        # The smallest m runs of each batch minimize requirements. Opposite
        # ordering of these prefixes minimizes the sum of positive excesses.
        draw = sum(max(0, am[i] + pm[m - 1 - i] - cap) for i in range(m))
        thresholds.append(Q(draw, scale))
    increments = [y - x for x, y in zip(thresholds, thresholds[1:])]
    require(increments == sorted(increments), "Nonconvex matching thresholds")
    return dict(P=sum(a), S=sum(a) + sum(b), thresholds=thresholds,
                all_pairs_free=a[-1] + b[-1] <= battery,
                maximum_matching_free=thresholds[-1] == 0)


def gap_bands(layers, total, rho):
    beta = rho * PBAR / total
    bands = []
    width = Q(0)
    for (u, m), (v, n) in zip(layers, layers[1:]):
        require(n == m + 1 and v > u, "Adjacent distinct thresholds must differ by one match")
        marginal_fee = FEE / (v - u)
        lo = marginal_fee - beta * (2 * v - total)
        hi = marginal_fee - beta * (2 * u - total)
        require(lo < hi, "Empty open band")
        require(not bands or hi <= bands[-1]["lo"], "Overlapping open bands")
        width += hi - lo
        bands.append(dict(m_left=m, m_right=n, u_kwh=u, v_kwh=v, lo=lo, hi=hi))
    require(width == 2 * beta * (layers[-1][0] - layers[0][0]), "Band widths do not telescope")
    return bands, width


def index_published(rows, battery, fraction):
    gaps = {}
    for row in rows:
        key = (row["operator"], Q(row["rho"]), Q(row["s0"]))
        require((row["B"], Q(row["K_frac"]), row["f"]) == (battery, fraction, FEE),
                "Published row in the wrong scenario group: " + str(key))
        require(key not in gaps, "Duplicate published cell: " + str(key))
        gaps[key] = row["gap"]
    return gaps


def evaluate_group(operators, battery, fraction, published):
    seen = index_published(published, battery, fraction)
    interval = OFFSETS[-1] - OFFSETS[0]
    rows, mismatches = [], []
    for name, op in operators.items():
        # H=S makes the physical early minimum zero for m=0. Discard r_m>K
        # and keep the cheapest (largest m) fleet at each coincident threshold.
        early_cap = fraction * op["P"]
        layers = list({u: m for m, u in enumerate(op["thresholds"]) if u <= early_cap}.items())
        for rho in RHOS:
            bands, full_width = gap_bands(layers, op["S"], rho)
            length = sum((max(Q(0), min(b["hi"], OFFSETS[-1]) - max(b["lo"], OFFSETS[0]))
                          for b in bands), Q(0))
            require(0 <= length <= interval, "Invalid clipped union length")
            hits = []
            for s0 in OFFSETS:
                key = (name, rho, s0)
                require(key in seen, "Missing published cell: " + str(key))
                value = seen.pop(key)
                exact = any(b["lo"] < s0 < b["hi"] for b in bands)
                if exact:
                    hits.append(s0)
                if exact != (value > PUBLISHED_TOL):
                    mismatches.append(dict(operator=name, rho=rho, s0=s0,
                                           exact_positive=exact, published_gap=str(value)))
            rows.append(dict(operator=name, rho=rho, S_kwh=op["S"], K_kwh=early_cap,
                             max_feasible_matches=layers[-1][1], bands=bands,
                             untruncated_width=full_width, inside_range_width=length,
                             inside_range_share=length / interval, sampled_offsets=hits))
    require(not seen, "Unexpected published cells: " + str(list(seen)[:3]))
    continuous = sorted({r["operator"] for r in rows if r["inside_range_width"] > 0})
    sampled = sorted({r["operator"] for r in rows if r["sampled_offsets"]})
    mean_share = sum(r["inside_range_share"] for r in rows) / len(rows)
    return dict(B=battery, K_over_P=fraction, eligible_operators=len(operators),
                operator_rho_cases=len(rows), sampled_cells=len(rows) * len(OFFSETS),
                positive_sampled_cells=sum(len(r["sampled_offsets"]) for r in rows),
                continuous_gap_operator_count=len(continuous), continuous_gap_operators=continuous,
                sampled_gap_operator_count=len(sampled), sampled_gap_operators=sampled,
                continuous_gap_operator_rho_cases=sum(r["inside_range_width"] > 0 for r in rows),
                sampled_gap_operator_rho_cases=sum(bool(r["sampled_offsets"]) for r in rows),
                mean_within_case_share=mean_share, mean_within_case_percent_display=float(100 * mean_share),
                mismatches=mismatches, cases=rows)


def analyze():
    peaks, peak_digest = read_input("data/peak_runs.json")
    study, study_digest = read_input("results/study.json")
    source = peaks["operators"]
    require(len({o["operator"] for o in source}) == len(source), "Duplicate source operator")
    retained = {o["operator"]: o for o in source
                if "error" not in o and min(len(o["a_kwh"]), len(o["b_kwh"])) >= 5}
    require(sorted(retained) == sorted(study["operators"]), "Published operator denominator differs")
    require(set(study["sweeps"]) == set(GROUPS) and Q(study["pbar"]) == PBAR,
            "Published sweep groups or reference price differ")
    batteries, groups = {}, {}
    for battery in (300, 400):
        eligible = {}
        for name, operator in retained.items():
            op = geometry(operator, battery)
            if op is not None:
                eligible[name] = op
        require(bool(eligible), "Empty battery group")
        all_free = sorted(name for name, op in eligible.items() if op["all_pairs_free"])
        matching_free = sorted(name for name, op in eligible.items() if op["maximum_matching_free"])
        batteries[str(battery)] = dict(eligible_operators=sorted(eligible),
                                       over_capacity_operators=sorted(retained.keys() - eligible.keys()),
                                       all_pairs_free_count=len(all_free), all_pairs_free=all_free,
                                       max_matching_free_count=len(matching_free), max_matching_free=matching_free)
        for name, (group_battery, fraction) in GROUPS.items():
            if group_battery == battery:
                groups[name] = evaluate_group(eligible, battery, fraction, study["sweeps"][name])
    return dict(status="MISMATCH" if any(g["mismatches"] for g in groups.values()) else "PASS",
                inputs_sha256={"data/peak_runs.json": peak_digest, "results/study.json": study_digest},
                source_operators=len(source), retained_operators=len(retained),
                excluded_before_capacity=sorted({o["operator"] for o in source} - retained.keys()),
                fee=FEE, reference_price=PBAR, H="S", rhos=RHOS, sampled_offsets=OFFSETS,
                published_positive_threshold=str(PUBLISHED_TOL), band_endpoints="open",
                continuous_share="mean within-case intersection length divided by 1.8, equal operator/rho weights",
                batteries=batteries, groups=groups)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new report path")
    args = parser.parse_args()
    with args.output.open("x") as stream:
        try:
            report = analyze()
        except (KeyError, TypeError, ValueError, OSError, ArithmeticError) as exc:
            report = dict(status="FAIL", reason=f"{type(exc).__name__}: {exc}")
        json.dump(report, stream, default=str, indent=2, allow_nan=False)
        stream.write("\n")
    print(report["status"], args.output)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
